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

    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, args: obj)})
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
    resolver = type_resolver(type, lambda: big_int_list, fragment=fragment)
    resolved = benchmark(resolver)

    assert resolved == [{
        'id': n
    } for n in big_int_list]



def test_querybuilder_big_list_of_objecttypes_with_two_int_fields(benchmark):
    big_int_list = [x for x in range(SIZE)]

    Node = GraphQLObjectType('Node', fields={
        'id': GraphQLField(GraphQLInt, resolver=lambda obj, args: obj),
        'ida': GraphQLField(GraphQLInt, resolver=lambda obj, args: obj*2)
    })
    field_asts = [
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
    ]
    fragment = Fragment(type=Node, field_asts=field_asts)
    type = GraphQLList(Node)
    resolver = type_resolver(type, lambda: big_int_list, fragment=fragment)
    resolved = benchmark(resolver)

    assert resolved == [{
        'id': n,
        'ida': n*2
    } for n in big_int_list]



def test_querybuilder_big_list_of_objecttypes_with_one_int_field(benchmark):
    big_int_list = [x for x in range(SIZE)]
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
    Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node), resolver=lambda *_, **__: big_int_list)})
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
    resolved = benchmark(resolver)
    assert resolved == {
        'nodes': [{
            'id': n
        } for n in big_int_list]
    }
