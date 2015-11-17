from collections import OrderedDict
from ..language.parser import parse_value
from ..type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
    is_input_type,
    is_output_type
)
from ..type.introspection import TypeKind
from .value_from_ast import value_from_ast

_none = lambda *_: None
_false = lambda *_: False


def no_execution(*args):
    raise Exception('Client Schema cannot be used for execution.')


def build_client_schema(introspection):
    schema_introspection = introspection['__schema']

    type_introspection_map = {t['name']: t for t in schema_introspection['types']}

    type_def_cache = {
        'String': GraphQLString,
        'Int': GraphQLInt,
        'Float': GraphQLFloat,
        'Boolean': GraphQLBoolean,
        'ID': GraphQLID
    }

    def get_type(type_ref):
        kind = type_ref.get('kind')

        if kind == TypeKind.LIST:
            item_ref = type_ref.get('ofType')

            if not item_ref:
                raise Exception('Decorated type deeper than introspection query.')

            return GraphQLList(get_type(item_ref))

        elif kind == TypeKind.NON_NULL:
            nullable_ref = type_ref.get('ofType')
            if not nullable_ref:
                raise Exception('Decorated type deeper than introspection query.')

            return GraphQLNonNull(get_type(nullable_ref))

        return get_named_type(type_ref['name'])

    def get_named_type(type_name):
        if type_name in type_def_cache:
            return type_def_cache[type_name]

        type_introspection = type_introspection_map.get(type_name)
        if not type_introspection:
            raise Exception(
                'Invalid or incomplete schema, unknown type: {}. Ensure that a full introspection query '
                'is used in order to build a client schema.'.format(type_name)
            )

        type_def = type_def_cache[type_name] = build_type(type_introspection)
        return type_def

    def get_input_type(type_ref):
        input_type = get_type(type_ref)
        assert is_input_type(input_type), 'Introspection must provide input type for arguments.'
        return input_type

    def get_output_type(type_ref):
        output_type = get_type(type_ref)
        assert is_output_type(output_type), 'Introspection must provide output type for fields.'
        return output_type

    def get_object_type(type_ref):
        object_type = get_type(type_ref)
        assert isinstance(object_type, GraphQLObjectType), 'Introspection must provide object type for possibleTypes.'
        return object_type

    def get_interface_type(type_ref):
        interface_type = get_type(type_ref)
        assert isinstance(interface_type, GraphQLInterfaceType), \
            'Introspection must provide interface type for interfaces.'
        return interface_type

    def build_type(type):
        type_kind = type.get('kind')
        handler = type_builders.get(type_kind)
        if not handler:
            raise Exception(
                'Invalid or incomplete schema, unknown kind: {}. Ensure that a full introspection query '
                'is used in order to build a client schema.'.format(type_kind)
            )

        return handler(type)

    def build_scalar_def(scalar_introspection):
        return GraphQLScalarType(
            name=scalar_introspection['name'],
            description=scalar_introspection['description'],
            serialize=_none,
            parse_value=_false,
            parse_literal=_false
        )

    def build_object_def(object_introspection):
        return GraphQLObjectType(
            name=object_introspection['name'],
            description=object_introspection['description'],
            interfaces=[get_interface_type(i) for i in object_introspection['interfaces']],
            fields=lambda: build_field_def_map(object_introspection)
        )

    def build_interface_def(interface_introspection):
        return GraphQLInterfaceType(
            name=interface_introspection['name'],
            description=interface_introspection['description'],
            fields=lambda: build_field_def_map(interface_introspection),
            resolve_type=no_execution
        )

    def build_union_def(union_introspection):
        return GraphQLUnionType(
            name=union_introspection['name'],
            description=union_introspection['description'],
            types=[get_object_type(t) for t in union_introspection['possibleTypes']],
            resolve_type=no_execution
        )

    def build_enum_def(enum_introspection):
        return GraphQLEnumType(
            name=enum_introspection['name'],
            description=enum_introspection['description'],
            values=OrderedDict([(value_introspection['name'],
                                 GraphQLEnumValue(description=value_introspection['description']))
                                for value_introspection in enum_introspection['enumValues']
                                ])
        )

    def build_input_object_def(input_object_introspection):
        return GraphQLInputObjectType(
            name=input_object_introspection['name'],
            description=input_object_introspection['description'],
            fields=lambda: build_input_value_def_map(
                input_object_introspection['inputFields'], GraphQLInputObjectField
            )
        )

    type_builders = {
        TypeKind.SCALAR: build_scalar_def,
        TypeKind.OBJECT: build_object_def,
        TypeKind.INTERFACE: build_interface_def,
        TypeKind.UNION: build_union_def,
        TypeKind.ENUM: build_enum_def,
        TypeKind.INPUT_OBJECT: build_input_object_def
    }

    def build_field_def_map(type_introspection):
        return OrderedDict([
            (f['name'], GraphQLField(
                type=get_output_type(f['type']),
                description=f['description'],
                resolver=no_execution,
                args=build_input_value_def_map(f['args'], GraphQLArgument)))
            for f in type_introspection['fields']
        ])

    def build_default_value(f):
        default_value = f.get('defaultValue')
        if default_value is None:
            return None

        return value_from_ast(parse_value(default_value), get_input_type(f['type']))

    def build_input_value_def_map(input_value_introspection, argument_type):
        return OrderedDict([
            (f['name'], argument_type(
                description=f['description'],
                type=get_input_type(f['type']),
                default_value=build_default_value(f)
            )) for f in input_value_introspection
        ])

    for type_introspection_name in type_introspection_map:
        get_named_type(type_introspection_name)

    query_type = get_type(schema_introspection['queryType'])
    mutation_type = get_type(schema_introspection['mutationType']) if schema_introspection.get('mutationType') else None
    subscription_type = get_type(schema_introspection['subscriptionType']) if \
        schema_introspection.get('subscriptionType') else None

    return GraphQLSchema(query=query_type, mutation=mutation_type, subscription=subscription_type)
