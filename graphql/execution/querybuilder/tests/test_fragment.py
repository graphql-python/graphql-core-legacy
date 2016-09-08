import pytest

from ....language import ast
from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                      GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                      GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)
from ..resolver import type_resolver
from ..fragment import Fragment

from promise import Promise



def test_fragment_resolver():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda *_, **__: 2)})
    field_asts = [
        ast.Field(
            alias=None,
            name=ast.Name(value='id'),
            arguments=[],
            directives=[],
            selection_set=None
        )
    ]
    fragment = Fragment(type=Node, field_asts=field_asts)
    assert fragment.resolver(lambda: 1) == {'id': 2}


def test_fragment_resolver_nested():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    field_asts = [
        ast.Field(
            alias=None,
            name=ast.Name(value='id'),
            arguments=[],
            directives=[],
            selection_set=None
        )
    ]
    fragment = Fragment(type=Node, field_asts=field_asts)
    type = GraphQLList(Node)

    resolver = type_resolver(type, lambda: range(3), fragment=fragment)
    resolved = resolver()
    assert resolved == [{
        'id': n
    } for n in range(3)]

# '''
# {
#     books {
#         title
#         author {
#             name
#         }
#     }
# }'''
# BooksFragment(
# 	('title', str(resolve_title())),
# 	('author', AuthorFragment(
# 		('name', str(resolve_author()))
# 	))
# )