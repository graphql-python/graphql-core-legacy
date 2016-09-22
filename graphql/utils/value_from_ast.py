from ..language import ast
from ..type import (GraphQLEnumType, GraphQLInputObjectType, GraphQLList,
                    GraphQLNonNull, GraphQLScalarType)

Undefined = object()
UndefinedList = [Undefined,]

def value_from_ast(value_ast, type, variables=None):
    """Given a type and a value AST node known to match this type, build a
    runtime value."""
    if isinstance(type, GraphQLNonNull):
        # Note: we're not checking that the result of coerceValueAST is non-null.
        # We're assuming that this query has been validated and the value used here is of the correct type.
        return value_from_ast(value_ast, type.of_type, variables)

    if not value_ast:
        return Undefined

    if isinstance(value_ast, ast.Variable):
        variable_name = value_ast.name.value
        if not variables or variable_name not in variables:
            return Undefined

        # Note: we're not doing any checking that this variable is correct. We're assuming that this query
        # has been validated and the variable usage here is of the correct type.
        return variables[variable_name]

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if isinstance(value_ast, ast.ListValue):
            result = [value_from_ast(item_ast, item_type, variables) for item_ast in value_ast.values]
            return result if result != UndefinedList else Undefined

        else:
            result = [value_from_ast(value_ast, item_type, variables)]
            return result if result != UndefinedList else Undefined

    if isinstance(type, GraphQLInputObjectType):
        fields = type.get_fields()
        if not isinstance(value_ast, ast.ObjectValue):
            return Undefined

        field_asts = {}

        for field in value_ast.fields:
            field_asts[field.name.value] = field

        obj = {}
        for field_name, field in fields.items():
            field_ast = field_asts.get(field_name)
            field_value_ast = Undefined

            if field_ast:
                field_value_ast = field_ast.value

            field_value = value_from_ast(
                field_value_ast, field.type, variables
            )
            if field_value == Undefined and field.default_value is not None:
                field_value = field.default_value

            if field_value != Undefined:
                obj[field_name] = field_value

        return obj

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), \
        'Must be input type'

    result = type.parse_literal(value_ast)
    return  result if result is not None else Undefined
