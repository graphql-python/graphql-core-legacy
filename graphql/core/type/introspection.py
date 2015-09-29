from .definition import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)
from ..language.printer import print_ast
from ..utils.ast_from_value import ast_from_value
from .scalars import GraphQLBoolean, GraphQLString

__Schema = GraphQLObjectType(
    '__Schema',
    description='A GraphQL Schema defines the capabilities of a GraphQL '
                'server. It exposes all available types and directives on '
                'the server, as well as the entry points for query and '
                'mutation operations.',
    fields=lambda: {
        'types': GraphQLField(
            description='A list of all types supported by this server.',
            type=GraphQLNonNull(GraphQLList(GraphQLNonNull(__Type))),
            resolver=lambda schema, *_: schema.get_type_map().values(),
        ),
        'queryType': GraphQLField(
            description='The type that query operations will be rooted at.',
            type=GraphQLNonNull(__Type),
            resolver=lambda schema, *_: schema.get_query_type(),
        ),
        'mutationType': GraphQLField(
            description='If this server supports mutation, the type that '
                        'mutation operations will be rooted at.',
            type=__Type,
            resolver=lambda schema, *_: schema.get_mutation_type(),
        ),
        'directives': GraphQLField(
            description='A list of all directives supported by this server.',
            type=GraphQLNonNull(GraphQLList(GraphQLNonNull(__Directive))),
            resolver=lambda schema, *_: schema.get_directives(),
        ),
    })

__Directive = GraphQLObjectType('__Directive', lambda: {
    'name': GraphQLField(GraphQLNonNull(GraphQLString)),
    'description': GraphQLField(GraphQLString),
    'args': GraphQLField(
        type=GraphQLNonNull(GraphQLList(GraphQLNonNull(__InputValue))),
        resolver=lambda directive, *args: directive.args or [],
    ),
    'onOperation': GraphQLField(
        type=GraphQLBoolean,
        resolver=lambda directive, *args: directive.on_operation,
    ),
    'onFragment': GraphQLField(
        type=GraphQLBoolean,
        resolver=lambda directive, *args: directive.on_fragment,
    ),
    'onField': GraphQLField(
        type=GraphQLBoolean,
        resolver=lambda directive, *args: directive.on_field,
    ),
})


class TypeFieldResolvers(object):
    @staticmethod
    def kind(type, *_):
        for cls, kind in (
            (GraphQLScalarType, TypeKind.SCALAR),
            (GraphQLObjectType, TypeKind.OBJECT),
            (GraphQLInterfaceType, TypeKind.INTERFACE),
            (GraphQLUnionType, TypeKind.UNION),
            (GraphQLEnumType, TypeKind.ENUM),
            (GraphQLInputObjectType, TypeKind.INPUT_OBJECT),
            (GraphQLList, TypeKind.LIST),
            (GraphQLNonNull, TypeKind.NON_NULL),
        ):
            if isinstance(type, cls):
                return kind
        raise Exception('Unknown kind of type: {}'.format(type))

    @staticmethod
    def fields(type, args, *_):
        if isinstance(type, (GraphQLObjectType, GraphQLInterfaceType)):
            fields = type.get_fields().values()
            if not args.get('includeDeprecated'):
                fields = [f for f in fields if not f.deprecation_reason]
            return fields
        return None

    @staticmethod
    def interfaces(type, *_):
        if isinstance(type, GraphQLObjectType):
            return type.get_interfaces()

    @staticmethod
    def possible_types(type, *_):
        if isinstance(type, (GraphQLInterfaceType, GraphQLUnionType)):
            return type.get_possible_types()

    @staticmethod
    def enum_values(type, args, *_):
        if isinstance(type, GraphQLEnumType):
            values = type.get_values().values()
            if not args.get('includeDeprecated'):
                values = [v for v in values if not v.deprecation_reason]
            return values

    @staticmethod
    def input_fields(type, *_):
        if isinstance(type, GraphQLInputObjectType):
            return type.get_fields().values()

__Type = GraphQLObjectType('__Type', lambda: {
    'kind': GraphQLField(
        type=GraphQLNonNull(__TypeKind),
        resolver=TypeFieldResolvers.kind
    ),
    'name': GraphQLField(GraphQLString),
    'description': GraphQLField(GraphQLString),
    'fields': GraphQLField(
        type=GraphQLList(GraphQLNonNull(__Field)),
        args={
            'includeDeprecated': GraphQLArgument(
                GraphQLBoolean,
                default_value=False
            )
        },
        resolver=TypeFieldResolvers.fields
    ),
    'interfaces': GraphQLField(
        type=GraphQLList(GraphQLNonNull(__Type)),
        resolver=TypeFieldResolvers.interfaces
    ),
    'possibleTypes': GraphQLField(
        type=GraphQLList(GraphQLNonNull(__Type)),
        resolver=TypeFieldResolvers.possible_types
    ),
    'enumValues': GraphQLField(
        type=GraphQLList(GraphQLNonNull(__EnumValue)),
        args={
            'includeDeprecated': GraphQLArgument(
                GraphQLBoolean,
                default_value=False
            )
        },
        resolver=TypeFieldResolvers.enum_values
    ),
    'inputFields': GraphQLField(
        type=GraphQLList(GraphQLNonNull(__InputValue)),
        resolver=TypeFieldResolvers.input_fields
    ),
    'ofType': GraphQLField(
        type=__Type,
        resolver=lambda type, *_: getattr(type, 'of_type', None)
    ),
})

__Field = GraphQLObjectType('__Field', lambda: {
    'name': GraphQLField(GraphQLNonNull(GraphQLString)),
    'description': GraphQLField(GraphQLString),
    'args': GraphQLField(
        type=GraphQLNonNull(GraphQLList(GraphQLNonNull(__InputValue))),
        resolver=lambda field, *_: field.args or []
    ),
    'type': GraphQLField(GraphQLNonNull(__Type)),
    'isDeprecated': GraphQLField(
        type=GraphQLNonNull(GraphQLBoolean),
        resolver=lambda field, *_: bool(field.deprecation_reason)
    ),
    'deprecationReason': GraphQLField(
        type=GraphQLString,
        resolver=lambda field, *_: field.deprecation_reason
    )
})

__InputValue = GraphQLObjectType('__InputValue', lambda: {
    'name': GraphQLField(GraphQLNonNull(GraphQLString)),
    'description': GraphQLField(GraphQLString),
    'type': GraphQLField(GraphQLNonNull(__Type)),
    'defaultValue': GraphQLField(
        type=GraphQLString,
        resolver=lambda input_val, *_:
            None if input_val.default_value is None
            else print_ast(ast_from_value(input_val.default_value, input_val))
    )
})

__EnumValue = GraphQLObjectType('__EnumValue', lambda: {
    'name': GraphQLField(GraphQLNonNull(GraphQLString)),
    'description': GraphQLField(GraphQLString),
    'isDeprecated': GraphQLField(
        type=GraphQLNonNull(GraphQLBoolean),
        resolver=lambda field, *_: bool(field.deprecation_reason)
    ),
    'deprecationReason': GraphQLField(
        type=GraphQLString,
        resolver=lambda enum_value, *_: enum_value.deprecation_reason,
    )
})


class TypeKind(object):
    SCALAR = 0
    OBJECT = 1
    INTERFACE = 2
    UNION = 3
    ENUM = 4
    INPUT_OBJECT = 5
    LIST = 6
    NON_NULL = 7

__TypeKind = GraphQLEnumType(
    '__TypeKind',
    description='An enum describing what kind of type a given __Type is',
    values={
        'SCALAR': GraphQLEnumValue(
            TypeKind.SCALAR,
            description='Indicates this type is a scalar.'
        ),
        'OBJECT': GraphQLEnumValue(
            TypeKind.OBJECT,
            description='Indicates this type is an object. '
                        '`fields` and `interfaces` are valid fields.'
        ),
        'INTERFACE': GraphQLEnumValue(
            TypeKind.INTERFACE,
            description='Indicates this type is an interface. '
                        '`fields` and `possibleTypes` are valid fields.'
        ),
        'UNION': GraphQLEnumValue(
            TypeKind.UNION,
            description='Indicates this type is a union. '
                        '`possibleTypes` is a valid field.'
        ),
        'ENUM': GraphQLEnumValue(
            TypeKind.ENUM,
            description='Indicates this type is an enum. '
                        '`enumValues` is a valid field.'
        ),
        'INPUT_OBJECT': GraphQLEnumValue(
            TypeKind.INPUT_OBJECT,
            description='Indicates this type is an input object. '
                        '`inputFields` is a valid field.'
        ),
        'LIST': GraphQLEnumValue(
            TypeKind.LIST,
            description='Indicates this type is a list. '
                        '`ofType` is a valid field.'
        ),
        'NON_NULL': GraphQLEnumValue(
            TypeKind.NON_NULL,
            description='Indicates this type is a non-null. '
                        '`ofType` is a valid field.'
        ),
    })

IntrospectionSchema = __Schema

SchemaMetaFieldDef = GraphQLField(
    type=GraphQLNonNull(__Schema),
    description='Access the current type schema of this server.',
    resolver=lambda source, args, info: info.schema
)
SchemaMetaFieldDef.name = '__schema'

TypeMetaFieldDef = GraphQLField(
    type=__Type,
    description='Request the type information of a single type.',
    args={
        'name': GraphQLArgument(GraphQLNonNull(GraphQLString))
    },
    resolver=lambda source, args, info: info.schema.get_type(args['name'])
)
TypeMetaFieldDef.name = '__type'

TypeNameMetaFieldDef = GraphQLField(
    GraphQLNonNull(GraphQLString),
    resolver=lambda source, args, info: info.parent_type.name
)
TypeNameMetaFieldDef.name = '__typename'
