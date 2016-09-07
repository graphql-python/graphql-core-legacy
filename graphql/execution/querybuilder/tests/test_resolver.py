import pytest

from ....language import ast
from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                      GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                      GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)
from ..resolver import type_resolver, Fragment


@pytest.mark.parametrize("type,value,expected", [
    (GraphQLString, 1, "1"),
    (GraphQLInt, "1", 1),
    (GraphQLNonNull(GraphQLString), 0, "0"),
    (GraphQLNonNull(GraphQLInt), 0, 0),
    (GraphQLList(GraphQLString), [1, 2], ['1', '2']),
    (GraphQLList(GraphQLInt), ['1', '2'], [1, 2]),  
    (GraphQLList(GraphQLNonNull(GraphQLInt)), [0], [0]),
    (GraphQLNonNull(GraphQLList(GraphQLInt)), [], []),
])
def test_type_resolver(type, value, expected):
    resolver = type_resolver(type, lambda x: value)
    resolved = resolver(2)
    assert resolved == expected


def test_fragment_resolver():
    Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda *_: 2)})
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
    assert fragment.field_resolvers.keys() == ['id']
    assert fragment.resolver(lambda: 1) == {'id': 2}


def test_fragment_resolver_nested():
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

    resolver = type_resolver(type, lambda: range(3), fragment=fragment)
    resolved = resolver()
    assert resolved == [{
        'id': n
    } for n in range(3)]


# def test_big_list_of_ints(benchmark):
#     big_int_list = [x for x in range(100000)]

#     resolver = type_resolver(GraphQLList(GraphQLInt), lambda: big_int_list)
#     result = benchmark(resolver)
    
#     assert result == big_int_list


# def test_big_list_of_nested_ints(benchmark):
#     big_int_list = [x for x in range(100000)]

#     Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj: obj)})
#     field_asts = [
#         ast.Field(
#             alias=None,
#             name=ast.Name(value='id'),
#             arguments=[],
#             directives=[],
#             selection_set=None
#         )
#     ]
#     fragment = Fragment(type=Node, field_asts=field_asts)
#     type = GraphQLList(Node)
#     resolver = type_resolver(type, lambda: big_int_list, fragment=fragment)
#     resolved = benchmark(resolver)

#     assert resolved == [{
#         'id': n
#     } for n in big_int_list]

