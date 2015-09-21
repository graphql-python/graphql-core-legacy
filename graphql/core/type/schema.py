from functools import reduce
from py._log import warning
from .definition import (
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLInputObjectType
)
from .introspection import IntrospectionSchema
from .directives import GraphQLIncludeDirective, GraphQLSkipDirective


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
    def __init__(self, query, mutation=None):
        self.query = query
        self.mutation = mutation
        self._type_map = None
        self._directives = None

    def get_query_type(self):
        return self.query

    def get_mutation_type(self):
        return self.mutation

    def get_type_map(self):
        if self._type_map is None:
            self._type_map = self._build_type_map()
        return self._type_map

    def get_type(self, name):
        return self.get_type_map().get(name)

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
        # TODO: make pythonic
        return reduce(type_map_reducer, [
            self.get_query_type(),
            self.get_mutation_type(),
            IntrospectionSchema,
        ], {})


def type_map_reducer(map, type):
    if not type:
        return map

    if isinstance(type, GraphQLList) or isinstance(type, GraphQLNonNull):
        return type_map_reducer(map, type.of_type)

    if type.name in map:
        if map[type.name] != type:
            warning.warn(
                'Schema must contain unique named types but contains multiple types named "{}".'
                .format(type.name)
            )
        return map
    map[type.name] = type

    reduced_map = map

    if isinstance(type, (GraphQLUnionType, GraphQLInterfaceType)):
        reduced_map = reduce(
            type_map_reducer, type.get_possible_types(), reduced_map
        )

    if isinstance(type, GraphQLObjectType):
        reduced_map = reduce(
            type_map_reducer, type.get_interfaces(), reduced_map
        )

    if isinstance(type, (GraphQLObjectType, GraphQLInterfaceType, GraphQLInputObjectType)):
        field_map = type.get_fields()
        for field_name, field in field_map.items():
            if hasattr(field, 'args'):
                field_arg_types = [arg.type for arg in field.args]
                reduced_map = reduce(
                    type_map_reducer, field_arg_types, reduced_map
                )

            reduced_map = type_map_reducer(reduced_map, getattr(field, 'type', None))

    return reduced_map
