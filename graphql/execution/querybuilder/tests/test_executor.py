import pytest
from functools import partial

from ....language import ast
from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                      GraphQLNonNull, GraphQLObjectType, GraphQLScalarType, GraphQLBoolean,
                      GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)
from ..resolver import type_resolver
from ..fragment import Fragment
from ...base import ExecutionContext
from ....language.parser import parse

from ..executor import execute
# from ...executor import execute

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


def test_fragment_resolver_context():
    Query = GraphQLObjectType('Query', fields={
        'context': GraphQLField(GraphQLString, resolver=lambda root, args, context, info: context),
        'same_schema': GraphQLField(GraphQLBoolean, resolver=lambda root, args, context, info: info.schema == schema)
    })

    document_ast = parse('''query {
        context
        same_schema
    }''')
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query)
    # partial_execute = partial(execute, schema, document_ast, context_value="1")
    # resolved = benchmark(partial_execute)
    resolved = execute(schema, document_ast, context_value="1")
    assert not resolved.errors
    assert resolved.data == {
        'context': '1',
        'same_schema': True,
    }


def test_fragment_resolver_fails():
    def raise_resolver(*args, **kwargs):
        raise Exception("My exception")

    def succeeds_resolver(*args, **kwargs):
        return True

    Query = GraphQLObjectType('Query', fields={
        'fails': GraphQLField(GraphQLString, resolver=raise_resolver),
        'succeeds': GraphQLField(GraphQLBoolean, resolver=succeeds_resolver)
    })

    document_ast = parse('''query {
        fails
        succeeds
    }''')
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query)
    # partial_execute = partial(execute, schema, document_ast, context_value="1")
    # resolved = benchmark(partial_execute)
    resolved = execute(schema, document_ast, context_value="1")
    assert len(resolved.errors) == 1
    assert resolved.data == {
        'fails': None,
        'succeeds': True,
    }


def test_fragment_resolver_resolves_all_list():
    Query = GraphQLObjectType('Query', fields={
        'ints': GraphQLField(GraphQLList(GraphQLNonNull(GraphQLInt)), resolver=lambda *args: [1, "2", "non"]),
    })

    document_ast = parse('''query {
        ints
    }''')
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query)
    # partial_execute = partial(execute, schema, document_ast, context_value="1")
    # resolved = benchmark(partial_execute)
    resolved = execute(schema, document_ast)
    assert len(resolved.errors) == 1
    assert str(resolved.errors[0]) == 'could not convert string to float: non'
    assert resolved.data == {
        'ints': [1, 2, None]
    }


def test_fragment_resolver_resolves_all_list():
    Person = GraphQLObjectType('Person', fields={
        'id': GraphQLField(GraphQLInt, resolver=lambda obj, *_, **__: 1),
    })
    Query = GraphQLObjectType('Query', fields={
        'persons': GraphQLField(GraphQLList(GraphQLNonNull(Person)), resolver=lambda *args: [1, 2, None]),
    })

    document_ast = parse('''query {
        persons {
            id
        }
    }''')
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query, types=[Person])
    # partial_execute = partial(execute, schema, document_ast, context_value="1")
    # resolved = benchmark(partial_execute)
    resolved = execute(schema, document_ast)
    assert len(resolved.errors) == 1
    assert str(resolved.errors[0]) == 'Cannot return null for non-nullable field Query.persons.'
    # assert str(resolved.errors[0]) == 'could not convert string to float: non'
    assert resolved.data == {
        'persons': None
    }


def test_fragment_resolver_resolves_all_list_null():
    Person = GraphQLObjectType('Person', fields={
        'id': GraphQLField(GraphQLInt, resolver=lambda obj, *_, **__: 1),
    })
    Query = GraphQLObjectType('Query', fields={
        'persons': GraphQLField(GraphQLList(GraphQLNonNull(Person)), resolver=lambda *args: [1, 2, None]),
    })

    document_ast = parse('''query {
        persons {
            id
        }
    }''')
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    schema = GraphQLSchema(query=Query, types=[Person])
    # partial_execute = partial(execute, schema, document_ast, context_value="1")
    # resolved = benchmark(partial_execute)
    resolved = execute(schema, document_ast)
    assert len(resolved.errors) == 1
    assert str(resolved.errors[0]) == 'Cannot return null for non-nullable field Query.persons.'
    # assert str(resolved.errors[0]) == 'could not convert string to float: non'
    assert resolved.data == {
        'persons': None
    }
