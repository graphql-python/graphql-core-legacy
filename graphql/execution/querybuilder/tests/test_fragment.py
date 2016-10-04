import pytest

from ....language import ast
from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                      GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                      GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)
from ..resolver import type_resolver
from ..fragment import Fragment
from ...base import ExecutionContext
from ....language.parser import parse


from promise import Promise


def test_fragment_equal():
    selection1 = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='id'),
        )
    ])
    selection2 = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='id'),
        )
    ])
    assert selection1 == selection2
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt)})
    Node2 = GraphQLObjectType('Node2', fields={'id': GraphQLField(GraphQLInt)})
    fragment1 = Fragment(type=Node, selection_set=selection1)
    fragment2 = Fragment(type=Node, selection_set=selection2)
    fragment3 = Fragment(type=Node2, selection_set=selection2)
    assert fragment1 == fragment2
    assert fragment1 != fragment3
    assert fragment1 != object()


def test_fragment_resolver():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda *_, **__: 2)})
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='id'),
        )
    ])
    fragment = Fragment(type=Node, selection_set=selection_set)
    assert fragment.resolver(lambda: 1) == {'id': 2}


def test_fragment_resolver_list():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='id'),
        )
    ])
    fragment = Fragment(type=Node, selection_set=selection_set)
    type = GraphQLList(Node)

    resolver = type_resolver(type, lambda: range(3), fragment=fragment)
    resolved = resolver()
    assert resolved == [{
        'id': n
    } for n in range(3)]


def test_fragment_resolver_nested():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    Query = GraphQLObjectType('Query', fields={'node': GraphQLField(Node, resolver=lambda *_, **__: 1)})
    node_selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='id'),
        )
    ])
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='node'),
            selection_set=node_selection_set
        )
    ])
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    query_fragment = Fragment(type=Query, selection_set=selection_set)
    resolver = type_resolver(Query, lambda: None, fragment=query_fragment)
    resolved = resolver()
    assert resolved == {
        'node': {
            'id': 1
        }
    }


def test_fragment_resolver_abstract():
    Node = GraphQLInterfaceType('Node', fields={'id': GraphQLField(GraphQLInt)})
    Person = GraphQLObjectType('Person', interfaces=(Node, ), is_type_of=lambda *_: True, fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    Query = GraphQLObjectType('Query', fields={'node': GraphQLField(Node, resolver=lambda *_, **__: 1)})
    node_selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='id'),
        )
    ])
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='node'),
            selection_set=node_selection_set
        )
    ])
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query, types=[Person])
    document_ast = parse('''{
        node {
            id
        }
    }''')
    print document_ast
    root_value = None
    context_value = None
    operation_name = None
    variable_values = {}
    executor = None
    middlewares = None
    context = ExecutionContext(
        schema,
        document_ast,
        root_value,
        context_value,
        variable_values,
        operation_name,
        executor,
        middlewares
    )

    query_fragment = Fragment(type=Query, selection_set=selection_set, context=context)
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
    node_selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='id'),
        )
    ])
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='nodes'),
            selection_set=node_selection_set
        )
    ])
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    query_fragment = Fragment(type=Query, selection_set=selection_set)
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