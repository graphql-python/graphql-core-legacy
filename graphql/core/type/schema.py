from .definition import (
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLUnionType,
)
from .directives import GraphQLIncludeDirective, GraphQLSkipDirective
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
    __slots__ = '_query', '_mutation', '_type_map', '_directives'

    def __init__(self, query, mutation=None):
        assert isinstance(query, GraphQLObjectType), 'Schema query must be Object Type but got: {}.'.format(query)
        if mutation:
            assert isinstance(mutation, GraphQLObjectType), \
                'Schema mutation must be Object Type but got: {}.'.format(mutation)

        self._query = query
        self._mutation = mutation
        self._type_map = self._build_type_map()
        self._directives = None

    def get_query_type(self):
        return self._query

    def get_mutation_type(self):
        return self._mutation

    def get_type_map(self):
        return self._type_map

    def get_type(self, name):
        return self._type_map.get(name)

    def get_directives(self):
        if self._directives is None:
            self._directives = [
                GraphQLIncludeDirective,
                GraphQLSkipDirective
            ]

        return self._directives

    def get_directive(self, name):
        for directive in self.get_directives():
            if directive.name == name:
                return directive

        return None

    def _build_type_map(self):
        type_map = {}
        for type in (self.get_query_type(), self.get_mutation_type(), IntrospectionSchema):
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
            .format(type.name)
        )
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
