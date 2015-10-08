from ..language import ast
from ..type.definition import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
)


def is_valid_literal_value(type, value_ast):
    if isinstance(type, GraphQLNonNull):
        if not value_ast:
            return False

        of_type = type.of_type
        return is_valid_literal_value(of_type, value_ast)

    if not value_ast:
        return True

    if isinstance(value_ast, ast.Variable):
        return True

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if isinstance(value_ast, ast.ListValue):
            return all(is_valid_literal_value(item_type, item_ast) for item_ast in value_ast.values)

        return is_valid_literal_value(item_type, value_ast)

    if isinstance(type, GraphQLInputObjectType):
        if not isinstance(value_ast, ast.ObjectValue):
            return False

        fields = type.get_fields()
        field_asts = value_ast.fields

        if any(not fields.get(field_ast.name.value, None) for field_ast in field_asts):
            return False

        field_ast_map = {field_ast.name.value: field_ast for field_ast in field_asts}
        get_field_ast_value = lambda field_name: field_ast_map[
            field_name].value if field_name in field_ast_map else None

        return all(is_valid_literal_value(field.type, get_field_ast_value(field_name))
                   for field_name, field in fields.items())

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), 'Must be input type'

    return type.parse_literal(value_ast) is not None
