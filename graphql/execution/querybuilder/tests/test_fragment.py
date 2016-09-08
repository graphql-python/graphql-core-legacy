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
            name=ast.Name(value='id'),
        )
    ]
    fragment = Fragment(type=Node, field_asts=field_asts)
    assert fragment.resolver(lambda: 1) == {'id': 2}


def test_fragment_resolver_list():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    field_asts = [
        ast.Field(
            name=ast.Name(value='id'),
        )
    ]
    fragment = Fragment(type=Node, field_asts=field_asts)
    type = GraphQLList(Node)

    resolver = type_resolver(type, lambda: range(3), fragment=fragment)
    resolved = resolver()
    assert resolved == [{
        'id': n
    } for n in range(3)]


def test_fragment_resolver_nested():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    Query = GraphQLObjectType('Query', fields={'node': GraphQLField(Node, resolver=lambda *_, **__: 1)})
    node_field_asts = [
        ast.Field(
            name=ast.Name(value='id'),
        )
    ]
    field_asts = [
        ast.Field(
            name=ast.Name(value='node'),
            selection_set=node_field_asts
        )
    ]
    node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    query_fragment = Fragment(type=Query, field_asts=field_asts, field_fragments={'node': node_fragment})
    resolver = type_resolver(Query, lambda: None, fragment=query_fragment)
    resolved = resolver()
    assert resolved == {
        'node': {
            'id': 1
        }
    }


def test_fragment_resolver_nested_list():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node), resolver=lambda *_, **__: range(3))})
    node_field_asts = [
        ast.Field(
            name=ast.Name(value='id'),
        )
    ]
    field_asts = [
        ast.Field(
            name=ast.Name(value='nodes'),
            selection_set=node_field_asts
        )
    ]
    node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    query_fragment = Fragment(type=Query, field_asts=field_asts, field_fragments={'nodes': node_fragment})
    resolver = type_resolver(Query, lambda: None, fragment=query_fragment)
    resolved = resolver()
    assert resolved == {
        'nodes': [{
            'id': n
        } for n in range(3)]
    }

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