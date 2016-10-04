import pytest

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


def test_fragment_resolver_abstract():
    Node = GraphQLInterfaceType('Node', fields={'id': GraphQLField(GraphQLInt)})
    Person = GraphQLObjectType('Person', interfaces=(Node, ), is_type_of=lambda *_: True, fields={
        'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj),
        'name': GraphQLField(GraphQLString, resolver=lambda obj, **__: "name:"+str(obj))
    })
    Query = GraphQLObjectType('Query', fields={'node': GraphQLField(Node, resolver=lambda *_, **__: 1)})

    document_ast = parse('''query {
        node {
            id
            ... on Person {
                name
            }
        }
    }''')
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query, types=[Person])
    resolved = execute(schema, document_ast)
    assert not resolved.errors
    assert resolved.data == {
        'node': {
            'id': 1,
            'name': 'name:1'
        }
    }
