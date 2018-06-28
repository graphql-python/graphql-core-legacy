from ..language import ast
from ..type.definition import GraphQLList, GraphQLNonNull

if False:  # flake8: noqa
    from ..language.ast import ListType, NamedType, NonNullType
    from ..type.definition import GraphQLNamedType
    from ..type.schema import GraphQLSchema
    from typing import Any, Union


def type_from_ast(schema, input_type_ast):
    # type: (GraphQLSchema, Union[ListType, NamedType, NonNullType]) -> Union[GraphQLList, GraphQLNonNull, GraphQLNamedType]
    if isinstance(input_type_ast, ast.ListType):
        inner_type = type_from_ast(schema, input_type_ast.type)
        if inner_type:
            return GraphQLList(inner_type)
        else:
            return None

    if isinstance(input_type_ast, ast.NonNullType):
        inner_type = type_from_ast(schema, input_type_ast.type)
        if inner_type:
            return GraphQLNonNull(inner_type)
        else:
            return None

    assert isinstance(input_type_ast, ast.NamedType), "Must be a type name."
    return schema.get_type(input_type_ast.name.value)
