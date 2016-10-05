import pytest

from ....language import ast
from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                      GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                      GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)
from ..resolver import type_resolver, Fragment

from promise import Promise


SIZE = 10000

def test_querybuilder_big_list_of_ints(benchmark):
    big_int_list = [x for x in range(SIZE)]

    resolver = type_resolver(GraphQLList(GraphQLInt), lambda: big_int_list)
    result = benchmark(resolver)
    
    assert result == big_int_list


def test_querybuilder_big_list_of_nested_ints(benchmark):
    big_int_list = [x for x in range(SIZE)]

    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, args, context, info: obj)})
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            alias=None,
            name=ast.Name(value='id'),
            arguments=[],
            directives=[],
            selection_set=None
        )
    ])
    fragment = Fragment(type=Node, selection_set=selection_set)
    type = GraphQLList(Node)
    resolver = type_resolver(type, lambda: big_int_list, fragment=fragment)
    resolved = benchmark(resolver)

    assert resolved == [{
        'id': n
    } for n in big_int_list]



def test_querybuilder_big_list_of_objecttypes_with_two_int_fields(benchmark):
    big_int_list = [x for x in range(SIZE)]

    Node = GraphQLObjectType('Node', fields={
        'id': GraphQLField(GraphQLInt, resolver=lambda obj, args, context, info: obj),
        'ida': GraphQLField(GraphQLInt, resolver=lambda obj, args, context, info: obj*2)
    })
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            alias=None,
            name=ast.Name(value='id'),
            arguments=[],
            directives=[],
            selection_set=None
        ),
        ast.Field(
            alias=None,
            name=ast.Name(value='ida'),
            arguments=[],
            directives=[],
            selection_set=None
        )
    ])
    fragment = Fragment(type=Node, selection_set=selection_set)
    type = GraphQLList(Node)
    resolver = type_resolver(type, lambda: big_int_list, fragment=fragment)
    resolved = benchmark(resolver)

    assert resolved == [{
        'id': n,
        'ida': n*2
    } for n in big_int_list]



def test_querybuilder_big_list_of_objecttypes_with_one_int_field(benchmark):
    big_int_list = [x for x in range(SIZE)]
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, *_, **__: obj)})
    Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node), resolver=lambda *_, **__: big_int_list)})
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
    query_fragment = Fragment(type=Query, selection_set=selection_set)
    resolver = type_resolver(Query, lambda: None, fragment=query_fragment)
    resolved = benchmark(resolver)
    assert resolved == {
        'nodes': [{
            'id': n
        } for n in big_int_list]
    }
