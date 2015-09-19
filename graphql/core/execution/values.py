import collections
from ..error import GraphQLError
from ..language import ast
from ..language.printer import print_ast
from ..type import (GraphQLNonNull, GraphQLList, GraphQLInputObjectType,
                    GraphQLScalarType, GraphQLEnumType, is_input_type)
from ..utils import type_from_ast, is_nullish

__all__ = ['get_variable_values', 'get_argument_values']


def get_variable_values(schema, definition_asts, inputs):
    """Prepares an object map of variables of the correct type based on the provided variable definitions and arbitrary input.
    If the input cannot be parsed to match the variable definitions, a GraphQLError will be thrown."""
    if inputs is None:
        inputs = {}
    values = {}
    for def_ast in definition_asts:
        var_name = def_ast.variable.name.value
        value = get_variable_value(schema, def_ast, inputs.get(var_name))
        values[var_name] = value
    return values


def get_argument_values(arg_defs, arg_asts, variables):
    """Prepares an object map of argument values given a list of argument
    definitions and list of argument AST nodes."""
    arg_ast_map = {}
    if arg_asts:
        for arg in arg_asts:
            arg_ast_map[arg.name.value] = arg
    result = {}
    for arg_def in arg_defs:
        name = arg_def.name
        value_ast = arg_ast_map.get(name)
        if value_ast:
            value_ast = value_ast.value
        value = coerce_value_ast(
            arg_def.type,
            value_ast,
            variables
        )
        if is_nullish(value) and not is_nullish(arg_def.default_value):
            value = arg_def.default_value
        result[name] = value
    return result


def get_variable_value(schema, definition_ast, input):
    """Given a variable definition, and any value of input, return a value which adheres to the variable definition, or throw an error."""
    type = type_from_ast(schema, definition_ast.type)
    if not type or not is_input_type(type):
        raise GraphQLError(
            'Variable ${} expected value of type {} which cannot be used as an input type.'.format(
                definition_ast.variable.name.value,
                print_ast(definition_ast.type),
            ),
            [definition_ast]
        )
    if is_valid_value(type, input):
        if is_nullish(input):
            default_value = definition_ast.default_value
            if default_value:
                return coerce_value_ast(type, default_value, None)
        return coerce_value(type, input)
    raise GraphQLError(
        'Variable ${} expected value of type {} but got: {}'.format(
            definition_ast.variable.name.value,
            print_ast(definition_ast.type),
            repr(input)
        ),
        [definition_ast]
    )


def is_valid_value(type, value):
    """Given a type and any value, return True if that value is valid."""
    if isinstance(type, GraphQLNonNull):
        if is_nullish(value):
            return False
        return is_valid_value(type.of_type, value)

    if is_nullish(value):
        return True

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if not isinstance(value, basestring) and \
                isinstance(value, collections.Iterable):
            return all(is_valid_value(item_type, item) for item in value)
        else:
            return is_valid_value(item_type, value)

    if isinstance(type, GraphQLInputObjectType):
        if not isinstance(value, collections.Mapping):
            return False
        fields = type.get_fields()

        # Ensure every provided field is defined.
        if any(field_name not in fields for field_name in value.keys()):
            return False

        # Ensure every defined field is valid.
        return all(
            is_valid_value(fields[field_name].type, value.get(field_name))
            for field_name in fields
        )

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), \
        'Must be input type'

    return not is_nullish(type.parse_value(value))


def coerce_value(type, value):
    """Given a type and any value, return a runtime value coerced to match the type."""
    if isinstance(type, GraphQLNonNull):
        # Note: we're not checking that the result of coerceValue is
        # non-null.
        # We only call this function after calling isValidValue.
        return coerce_value(type.of_type, value)

    if is_nullish(value):
        return None

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if not isinstance(value, basestring) and isinstance(value, collections.Iterable):
            return [coerce_value(item_type, item) for item in value]
        else:
            return [coerce_value(item_type, value)]

    if isinstance(type, GraphQLInputObjectType):
        fields = type.get_fields()
        obj = {}
        for field_name, field in fields.items():
            field_value = coerce_value(field.type, value[field_name])
            if field_value is None:
                field_value = field.default_value
            obj[field_name] = field_value
        return obj

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), \
        'Must be input type'

    parsed = type.parse_value(value)
    if not is_nullish(parsed):
        return parsed

    return None


def coerce_value_ast(type, value_ast, variables):
    """Given a type and a value AST node known to match this type, build a
    runtime value."""
    if isinstance(type, GraphQLNonNull):
        # Note: we're not checking that the result of coerceValueAST is non-null.
        # We're assuming that this query has been validated and the value used here is of the correct type.
        return coerce_value_ast(type.of_type, value_ast, variables)

    if not value_ast:
        return None

    if isinstance(value_ast, ast.Variable):
        variable_name = value_ast.name.value
        if not variables or variable_name not in variables:
            return None
        # Note: we're not doing any checking that this variable is correct. We're assuming that this query
        # has been validated and the variable usage here is of the correct type.
        return variables[variable_name]

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if isinstance(value_ast, ast.ListValue):
            return [coerce_value_ast(item_type, item_ast, variables)
                    for item_ast in value_ast.values]
        else:
            return [coerce_value_ast(item_type, value_ast, variables)]

    if isinstance(type, GraphQLInputObjectType):
        fields = type.get_fields()
        if not isinstance(value_ast, ast.ObjectValue):
            return None
        field_asts = {}
        for field in value_ast.fields:
            field_asts[field.name.value] = field
        obj = {}
        for field_name, field in fields.items():
            field_ast = field_asts.get(field_name)
            field_value_ast = None
            if field_ast:
                field_value_ast = field_ast.value
            field_value = coerce_value_ast(
                field.type, field_value_ast, variables
            )
            if field_value is None:
                field_value = field.default_value
            obj[field_name] = field_value
        return obj

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), \
        'Must be input type'

    parsed = type.parse_literal(value_ast)
    if not is_nullish(parsed):
        return parsed

    return None
