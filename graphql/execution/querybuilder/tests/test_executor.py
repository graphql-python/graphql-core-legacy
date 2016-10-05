import pytest
from functools import partial

from ....language import ast
from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                      GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                      GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)
from ..resolver import type_resolver
from ..fragment import Fragment
from ...base import ExecutionContext
from ....language.parser import parse

from ..executor import execute

from promise import Promise


def test_fragment_resolver_abstract(benchmark):
    all_slots = range(10000)

    Node = GraphQLInterfaceType('Node', fields={'id': GraphQLField(GraphQLInt)})
    Person = GraphQLObjectType('Person', interfaces=(Node, ), is_type_of=lambda *_, **__: True, fields={
        'id': GraphQLField(GraphQLInt, resolver=lambda obj, *_, **__: obj),
        'name': GraphQLField(GraphQLString, resolver=lambda obj, *_, **__: "name:"+str(obj))
    })
    Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node), resolver=lambda *_, **__: all_slots)})

    document_ast = parse('''query {
        nodes {
            id
            ... on Person {
                name
            }
        }
    }''')
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query, types=[Person])
    partial_execute = partial(execute, schema, document_ast)
    resolved = benchmark(partial_execute)
    # resolved = execute(schema, document_ast)
    assert not resolved.errors
    assert resolved.data == {
        'nodes': [{
            'id': x,
            'name': 'name:'+str(x)
        } for x in all_slots]
    }
