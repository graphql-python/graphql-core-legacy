from ..language import ast
from ..type import (Undefined, GraphQLEnumType, GraphQLInputObjectType, GraphQLList,
                    GraphQLNonNull, GraphQLScalarType)


def value_from_ast(value_ast, type, variables=None):
    """Given a type and a value AST node known to match this type, build a
    runtime value."""
    if isinstance(type, GraphQLNonNull):
        # Note: we're not checking that the result of coerceValueAST is non-null.
        # We're assuming that this query has been validated and the value used here is of the correct type.
        return value_from_ast(value_ast, type.of_type, variables)

    if value_ast is Undefined:
        return Undefined

    if value_ast is None:
        return None

    if isinstance(value_ast, ast.Variable):
        variable_name = value_ast.name.value
        if not variables:
            return Undefined

        # Note: we're not doing any checking that this variable is correct. We're assuming that this query
        # has been validated and the variable usage here is of the correct type.
        return variables.get(variable_name, Undefined)

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if isinstance(value_ast, ast.ListValue):
            return [value_from_ast(item_ast, item_type, variables)
                    for item_ast in value_ast.values]

        else:
            return [value_from_ast(value_ast, item_type, variables)]

    if isinstance(type, GraphQLInputObjectType):
        fields = type.fields
        if not isinstance(value_ast, ast.ObjectValue):
            return Undefined

        field_asts = {}

        for field in value_ast.fields:
            field_asts[field.name.value] = field

        obj = {}
        for field_name, field in fields.items():
            field_ast = field_asts.get(field_name, Undefined)
            field_value_ast = Undefined

            if field_ast:
                field_value_ast = field_ast.value

            field_value = value_from_ast(
                field_value_ast, field.type, variables
            )
            if field_value is Undefined:
                field_value = field.default_value

            if field_value is not Undefined:
                # We use out_name as the output name for the
                # dict if exists
                obj[field.out_name or field_name] = field_value

        return  type.create_container(obj)

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), \
        'Must be input type'

    value = type.parse_literal(value_ast)
    if value is None:
        return Undefined

    return value
