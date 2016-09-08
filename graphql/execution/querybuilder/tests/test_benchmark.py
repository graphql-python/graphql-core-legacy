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

    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj: obj)})
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



def test_querybuilder_big_list_of_nested_ints_two(benchmark):
    big_int_list = [x for x in range(SIZE)]

    Node = GraphQLObjectType('Node', fields={
        'id': GraphQLField(GraphQLInt, resolver=lambda obj: obj),
        'ida': GraphQLField(GraphQLInt, resolver=lambda obj: obj*2)
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
