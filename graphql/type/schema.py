from collections import Iterable, OrderedDict, defaultdict
from functools import reduce

from ..utils.type_comparators import is_equal_type, is_type_sub_type_of
from .definition import (GraphQLInputObjectType, GraphQLInterfaceType,
                         GraphQLList, GraphQLNonNull, GraphQLObjectType,
                         GraphQLUnionType)
from .directives import (GraphQLDirective, GraphQLIncludeDirective,
                         GraphQLSkipDirective)
from .introspection import IntrospectionSchema


class GraphQLSchema(object):
    """Schema Definition

    A Schema is created by supplying the root types of each type of operation, query and mutation (optional).
    A schema definition is then supplied to the validator and executor.

    Example:

        MyAppSchema = GraphQLSchema(
            query=MyAppQueryRootType,
            mutation=MyAppMutationRootType
        )
    """
    __slots__ = '_query', '_mutation', '_subscription', '_type_map', '_directives', '_implementations', '_possible_type_map'

    def __init__(self, query, mutation=None, subscription=None, directives=None, types=None):
        assert isinstance(query, GraphQLObjectType), 'Schema query must be Object Type but got: {}.'.format(query)
        if mutation:
            assert isinstance(mutation, GraphQLObjectType), \
                'Schema mutation must be Object Type but got: {}.'.format(mutation)

        if subscription:
            assert isinstance(subscription, GraphQLObjectType), \
                'Schema subscription must be Object Type but got: {}.'.format(subscription)

        if types:
            assert isinstance(types, Iterable), \
                'Schema types must be iterable if provided but got: {}.'.format(types)

        self._query = query
        self._mutation = mutation
        self._subscription = subscription
        if directives is None:
            directives = [
                GraphQLIncludeDirective,
                GraphQLSkipDirective
            ]

        assert all(isinstance(d, GraphQLDirective) for d in directives), \
            'Schema directives must be List[GraphQLDirective] if provided but got: {}.'.format(
                directives
        )

        self._directives = directives
        self._possible_type_map = defaultdict(set)
        self._type_map = self._build_type_map(types)
        # Keep track of all implementations by interface name.
        self._implementations = defaultdict(list)
        for type in self._type_map.values():
            if isinstance(type, GraphQLObjectType):
                for interface in type.get_interfaces():
                    self._implementations[interface.name].append(type)

        # Enforce correct interface implementations.
        for type in self._type_map.values():
            if isinstance(type, GraphQLObjectType):
                for interface in type.get_interfaces():
                    assert_object_implements_interface(self, type, interface)

    def get_query_type(self):
        return self._query

    def get_mutation_type(self):
        return self._mutation

    def get_subscription_type(self):
        return self._subscription

    def get_type_map(self):
        return self._type_map

    def get_type(self, name):
        return self._type_map.get(name)

    def get_directives(self):
        return self._directives

    def get_directive(self, name):
        for directive in self.get_directives():
            if directive.name == name:
                return directive

        return None

    def _build_type_map(self, _types):
        types = [
            self.get_query_type(),
            self.get_mutation_type(),
            self.get_subscription_type(),
            IntrospectionSchema
        ]
        if _types:
            types += _types

        type_map = reduce(type_map_reducer, types, OrderedDict())
        return type_map

    def get_possible_types(self, abstract_type):
        if isinstance(abstract_type, GraphQLUnionType):
            return abstract_type.get_types()
        assert isinstance(abstract_type, GraphQLInterfaceType)
        return self._implementations[abstract_type.name]

    def is_possible_type(self, abstract_type, possible_type):
        if not self._possible_type_map[abstract_type.name]:
            possible_types = self.get_possible_types(abstract_type)
            self._possible_type_map[abstract_type.name].update([p.name for p in possible_types])

        return possible_type.name in self._possible_type_map[abstract_type.name]


def type_map_reducer(map, type):
    if not type:
        return map

    if isinstance(type, GraphQLList) or isinstance(type, GraphQLNonNull):
        return type_map_reducer(map, type.of_type)

    if type.name in map:
        assert map[type.name] == type, (
            'Schema must contain unique named types but contains multiple types named "{}".'
        ).format(type.name)

        return map

    map[type.name] = type

    reduced_map = map

    if isinstance(type, (GraphQLUnionType)):
        for t in type.get_types():
            reduced_map = type_map_reducer(reduced_map, t)

    if isinstance(type, GraphQLObjectType):
        for t in type.get_interfaces():
            reduced_map = type_map_reducer(reduced_map, t)

    if isinstance(type, (GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType)):
        field_map = type.get_fields()
        for field in field_map.values():
            args = getattr(field, 'args', None)
            if args:
                field_arg_types = [arg.type for arg in field.args]
                for t in field_arg_types:
                    reduced_map = type_map_reducer(reduced_map, t)

            reduced_map = type_map_reducer(reduced_map, getattr(field, 'type', None))

    return reduced_map


def assert_object_implements_interface(schema, object, interface):
    object_field_map = object.get_fields()
    interface_field_map = interface.get_fields()

    for field_name, interface_field in interface_field_map.items():
        object_field = object_field_map.get(field_name)

        assert object_field, '"{}" expects field "{}" but "{}" does not provide it.'.format(
            interface, field_name, object
        )

        assert is_type_sub_type_of(schema, object_field.type, interface_field.type), (
            '{}.{} expects type "{}" but {}.{} provides type "{}".'
        ).format(interface, field_name, interface_field.type, object, field_name, object_field.type)

        object_arg_map = {arg.name: arg for arg in object_field.args}
        for interface_arg in interface_field.args:
            arg_name = interface_arg.name
            object_arg = object_arg_map.get(arg_name)

            assert object_arg, (
                '{}.{} expects argument "{}" but {}.{} does not provide it.'
            ).format(interface, field_name, arg_name, object, field_name)

            assert is_equal_type(interface_arg.type, object_arg.type), (
                '{}.{}({}:) expects type "{}" but {}.{}({}:) provides type "{}".'
            ).format(interface, field_name, arg_name, interface_arg.type, object, field_name, arg_name, object_arg.type)

        interface_arg_map = {arg.name: arg for arg in interface_field.args}
        for object_arg in object_field.args:
            arg_name = object_arg.name
            interface_arg = interface_arg_map.get(arg_name)
            if not interface_arg:
                assert not isinstance(object_arg.type, GraphQLNonNull), (
                    '{}.{}({}:) is of required type '
                    '"{}" but is not also provided by the '
                    'interface {}.{}.'
                ).format(object, field_name, arg_name, object_arg.type, interface, field_name)
