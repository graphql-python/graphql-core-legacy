from graphql.type.definition import (
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
)
from graphql.type.scalars import GraphQLString, GraphQLBoolean

class _TypeKind(GraphQLEnumType):
    name = '__TypeKind'
    description = 'An enum describing what kind of type a given __Type is'


class _Type(GraphQLObjectType):
    name = '__Type'
    fields = {
        'kind': GraphQLField(
            type=GraphQLNonNull(_TypeKind()),
        )
    }


class _Schema(GraphQLObjectType):
    name = '__Schema'
    description = 'A GraphQL Schema defines the capabilities of a GraphQL '\
               'server. It exposes all available types and directives on '\
               'the server, as well as the entry points for query and '\
               'mutation operations.'
    fields = {
        'types': GraphQLField(
            description='A list of all types supported by this server.',
            type=GraphQLNonNull(GraphQLList(GraphQLNonNull(_Type()))),
            resolver=lambda schema, *args: schema.get_type_map().values(),
        )
    }


# TODO
SchemaMetaFieldDef = GraphQLField(GraphQLNonNull(_Schema()))
SchemaMetaFieldDef.name = '__schema'
TypeMetaFieldDef = GraphQLField(_Type())
TypeMetaFieldDef.name = '__type'
TypeNameMetaFieldDef = GraphQLField(GraphQLNonNull(GraphQLString()))
TypeNameMetaFieldDef.name = '__typename'
