from ..language import ast
from ..type import (GraphQLEnumType, GraphQLInputObjectType, GraphQLList, GraphQLNonNull, GraphQLScalarType)
from .is_nullish import is_nullish


def value_from_ast(type, value_ast, variables):
    """Given a type and a value AST node known to match this type, build a
    runtime value."""
    if isinstance(type, GraphQLNonNull):
        # Note: we're not checking that the result of coerceValueAST is non-null.
        # We're assuming that this query has been validated and the value used here is of the correct type.
        return value_from_ast(type.of_type, value_ast, variables)

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
            return [value_from_ast(item_type, item_ast, variables)
                    for item_ast in value_ast.values]
        else:
            return [value_from_ast(item_type, value_ast, variables)]

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
            field_value = value_from_ast(
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
