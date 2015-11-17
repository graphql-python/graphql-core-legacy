from collections import OrderedDict

from ..language import ast
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
)
from ..utils.value_from_ast import value_from_ast


def _build_wrapped_type(inner_type, input_type_ast):
    if isinstance(input_type_ast, ast.ListType):
        return GraphQLList(_build_wrapped_type(inner_type, input_type_ast.type))

    if isinstance(input_type_ast, ast.NonNullType):
        return GraphQLNonNull(_build_wrapped_type(inner_type, input_type_ast.type))

    return inner_type


def _get_inner_type_name(type_ast):
    if isinstance(type_ast, (ast.ListType, ast.NonNullType)):
        return _get_inner_type_name(type_ast.type)

    return type_ast.name.value


_false = lambda *_: False
_none = lambda *_: None


def build_ast_schema(document, query_type_name, mutation_type_name=None, subscription_type_name=None):
    assert isinstance(document, ast.Document), 'must pass in Document ast.'
    assert query_type_name, 'must pass in query type'

    type_defs = [d for d in document.definitions if isinstance(d, ast.TypeDefinition)]
    ast_map = {d.name.value: d for d in type_defs}

    if query_type_name not in ast_map:
        raise Exception('Specified query type {} not found in document.'.format(query_type_name))

    if mutation_type_name and mutation_type_name not in ast_map:
        raise Exception('Specified mutation type {} not found in document.'.format(mutation_type_name))

    if subscription_type_name and subscription_type_name not in ast_map:
        raise Exception('Specified subscription type {} not found in document.'.format(subscription_type_name))

    inner_type_map = OrderedDict([
        ('String', GraphQLString),
        ('Int', GraphQLInt),
        ('Float', GraphQLFloat),
        ('Boolean', GraphQLBoolean),
        ('ID', GraphQLID)
    ])

    def produce_type_def(type_ast):
        type_name = _get_inner_type_name(type_ast)
        if type_name in inner_type_map:
            return _build_wrapped_type(inner_type_map[type_name], type_ast)

        if type_name not in ast_map:
            raise Exception('Type {} not found in document.'.format(type_name))

        inner_type_def = make_schema_def(ast_map[type_name])
        if not inner_type_def:
            raise Exception('Nothing constructed for {}.'.format(type_name))

        inner_type_map[type_name] = inner_type_def
        return _build_wrapped_type(inner_type_def, type_ast)

    def make_type_def(definition):
        return GraphQLObjectType(
            name=definition.name.value,
            fields=lambda: make_field_def_map(definition),
            interfaces=make_implemented_interfaces(definition)
        )

    def make_field_def_map(definition):
        return OrderedDict(
            (f.name.value, GraphQLField(
                type=produce_type_def(f.type),
                args=make_input_values(f.arguments, GraphQLArgument)
            ))
            for f in definition.fields
        )

    def make_implemented_interfaces(definition):
        return [produce_type_def(i) for i in definition.interfaces]

    def make_input_values(values, cls):
        return OrderedDict(
            (value.name.value, cls(
                type=produce_type_def(value.type),
                default_value=value_from_ast(value.default_value, produce_type_def(value.type))
            ))
            for value in values
        )

    def make_interface_def(definition):
        return GraphQLInterfaceType(
            name=definition.name.value,
            resolve_type=_none,
            fields=lambda: make_field_def_map(definition)
        )

    def make_enum_def(definition):
        return GraphQLEnumType(
            name=definition.name.value,
            values=OrderedDict(
                (v.name.value, GraphQLEnumValue()) for v in definition.values
            )
        )

    def make_union_def(definition):
        return GraphQLUnionType(
            name=definition.name.value,
            resolve_type=_none,
            types=[produce_type_def(t) for t in definition.types]
        )

    def make_scalar_def(definition):
        return GraphQLScalarType(
            name=definition.name.value,
            serialize=_none,
            # Validation calls the parse functions to determine if a literal value is correct.
            # Returning none, however would cause the scalar to fail validation. Returning false,
            # will cause them to pass.
            parse_literal=_false,
            parse_value=_false
        )

    def make_input_object_def(definition):
        return GraphQLInputObjectType(
            name=definition.name.value,
            fields=make_input_values(definition.fields, GraphQLInputObjectField)
        )

    _schema_def_handlers = {
        ast.ObjectTypeDefinition: make_type_def,
        ast.InterfaceTypeDefinition: make_interface_def,
        ast.EnumTypeDefinition: make_enum_def,
        ast.UnionTypeDefinition: make_union_def,
        ast.ScalarTypeDefinition: make_scalar_def,
        ast.InputObjectTypeDefinition: make_input_object_def
    }

    def make_schema_def(definition):
        if not definition:
            raise Exception('definition must be defined.')

        handler = _schema_def_handlers.get(type(definition))
        if not handler:
            raise Exception('{} not supported.'.format(type(definition).__name__))

        return handler(definition)

    for definition in document.definitions:
        produce_type_def(definition)

    schema_kwargs = {'query': produce_type_def(ast_map[query_type_name])}

    if mutation_type_name:
        schema_kwargs['mutation'] = produce_type_def(ast_map[mutation_type_name])

    if subscription_type_name:
        schema_kwargs['subscription'] = produce_type_def(ast_map[subscription_type_name])

    return GraphQLSchema(**schema_kwargs)
