from collections import OrderedDict
from .definition import (
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLUnionType,
)
from .directives import GraphQLDirective, GraphQLIncludeDirective, GraphQLSkipDirective
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
    __slots__ = '_query', '_mutation', '_subscription', '_type_map', '_directives',

    def __init__(self, query, mutation=None, subscription=None, directives=None):
        assert isinstance(query, GraphQLObjectType), 'Schema query must be Object Type but got: {}.'.format(query)
        if mutation:
            assert isinstance(mutation, GraphQLObjectType), \
                'Schema mutation must be Object Type but got: {}.'.format(mutation)

        if subscription:
            assert isinstance(subscription, GraphQLObjectType), \
                'Schema subscription must be Object Type but got: {}.'.format(subscription)

        self._query = query
        self._mutation = mutation
        self._subscription = subscription
        self._type_map = self._build_type_map()

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

        for type in self._type_map.values():
            if isinstance(type, GraphQLObjectType):
                for interface in type.get_interfaces():
                    assert_object_implements_interface(type, interface)

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

    def _build_type_map(self):
        type_map = OrderedDict()
        types = (self.get_query_type(), self.get_mutation_type(), self.get_subscription_type(), IntrospectionSchema)
        for type in types:
            type_map = type_map_reducer(type_map, type)

        return type_map


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

    if isinstance(type, (GraphQLUnionType, GraphQLInterfaceType)):
        for t in type.get_possible_types():
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


def assert_object_implements_interface(object, interface):
    object_field_map = object.get_fields()
    interface_field_map = interface.get_fields()

    for field_name, interface_field in interface_field_map.items():
        object_field = object_field_map.get(field_name)

        assert object_field, '"{}" expects field "{}" but "{}" does not provide it.'.format(
            interface, field_name, object
        )

        assert is_equal_type(interface_field.type, object_field.type), (
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


def is_equal_type(type_a, type_b):
    if isinstance(type_a, GraphQLNonNull) and isinstance(type_b, GraphQLNonNull):
        return is_equal_type(type_a.of_type, type_b.of_type)

    if isinstance(type_a, GraphQLList) and isinstance(type_b, GraphQLList):
        return is_equal_type(type_a.of_type, type_b.of_type)

    return type_a is type_b
