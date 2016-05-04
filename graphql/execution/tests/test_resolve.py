import json
from collections import OrderedDict

from graphql import graphql
from graphql.type import (GraphQLArgument, GraphQLField, GraphQLInt,
                          GraphQLObjectType, GraphQLSchema, GraphQLString)


def _test_schema(test_field):
    return GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields={
                'test': test_field
            }
        )
    )


def test_default_function_accesses_properties():
    schema = _test_schema(GraphQLField(GraphQLString))

    class source:
        test = 'testValue'

    result = graphql(schema, '{ test }', source)
    assert not result.errors
    assert result.data == {'test': 'testValue'}


def test_default_function_calls_methods():
    schema = _test_schema(GraphQLField(GraphQLString))

    class source:
        _secret = 'testValue'

        def test(self):
            return self._secret

    result = graphql(schema, '{ test }', source())
    assert not result.errors
    assert result.data == {'test': 'testValue'}


def test_uses_provided_resolve_function():
    def resolver(source, args, *_):
        return json.dumps([source, args], separators=(',', ':'))

    schema = _test_schema(GraphQLField(
        GraphQLString,
        args=OrderedDict([
            ('aStr', GraphQLArgument(GraphQLString)),
            ('aInt', GraphQLArgument(GraphQLInt)),
        ]),
        resolver=resolver
    ))

    result = graphql(schema, '{ test }', None)
    assert not result.errors
    assert result.data == {'test': '[null,{}]'}

    result = graphql(schema, '{ test(aStr: "String!") }', 'Source!')
    assert not result.errors
    assert result.data == {'test': '["Source!",{"aStr":"String!"}]'}

    result = graphql(schema, '{ test(aInt: -123, aStr: "String!",) }', 'Source!')
    assert not result.errors
    assert result.data in [
        {'test': '["Source!",{"aStr":"String!","aInt":-123}]'},
        {'test': '["Source!",{"aInt":-123,"aStr":"String!"}]'}
    ]
