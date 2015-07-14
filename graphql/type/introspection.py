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

__TypeKind = GraphQLEnumType(
    '__TypeKind',
    description='An enum describing what kind of type a given __Type is',
    values={

    })

__Type = GraphQLObjectType('__Type', {
    'kind': GraphQLField(
        type=GraphQLNonNull(__TypeKind),
    )
})

__Schema = GraphQLObjectType(
    '__Schema',
    description='A GraphQL Schema defines the capabilities of a GraphQL '
                'server. It exposes all available types and directives on '
                'the server, as well as the entry points for query and '
                'mutation operations.',
    fields={
        'types': GraphQLField(
            description='A list of all types supported by this server.',
            type=GraphQLNonNull(GraphQLList(GraphQLNonNull(__Type))),
            resolver=lambda schema, *args: schema.get_type_map().values(),
        )
    })

# TODO
IntrospectionSchema = __Schema
SchemaMetaFieldDef = GraphQLField(GraphQLNonNull(__Schema))
SchemaMetaFieldDef.name = '__schema'
TypeMetaFieldDef = GraphQLField(__Type)
TypeMetaFieldDef.name = '__type'
TypeNameMetaFieldDef = GraphQLField(
    GraphQLNonNull(GraphQLString),
    resolver=lambda source, args, root, field_ast, field_type, parent_type, *_:
        parent_type.name
)
TypeNameMetaFieldDef.name = '__typename'
