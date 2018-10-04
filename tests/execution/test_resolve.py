from json import dumps

from pytest import fixture

from graphql import graphql_sync
from graphql.type import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInt,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)
from graphql.pyutils import OrderedDict


def _test_schema(test_field):
    return GraphQLSchema(GraphQLObjectType("Query", {"test": test_field}))


def describe_execute_resolve_function():
    def default_function_accesses_attributes():
        schema = _test_schema(GraphQLField(GraphQLString))

        class Source:
            test = "testValue"

        assert graphql_sync(schema, "{ test }", Source()) == (
            {"test": "testValue"},
            None,
        )

    def default_function_accesses_keys():
        schema = _test_schema(GraphQLField(GraphQLString))

        source = {"test": "testValue"}

        assert graphql_sync(schema, "{ test }", source) == ({"test": "testValue"}, None)

    def default_function_calls_methods():
        schema = _test_schema(GraphQLField(GraphQLString))

        class Source:
            _secret = "testValue"

            def test(self, _info):
                return self._secret

        assert graphql_sync(schema, "{ test }", Source()) == (
            {"test": "testValue"},
            None,
        )

    def default_function_passes_args_and_context():
        schema = _test_schema(
            GraphQLField(GraphQLInt, args={"addend1": GraphQLArgument(GraphQLInt)})
        )

        class Adder:
            def __init__(self, num):
                self._num = num

            def test(self, info, addend1):
                return self._num + addend1 + info.context.addend2

        source = Adder(700)

        class Context:
            addend2 = 9

        assert graphql_sync(schema, "{ test(addend1: 80) }", source, Context()) == (
            {"test": 789},
            None,
        )

    def uses_provided_resolve_function():
        schema = _test_schema(
            GraphQLField(
                GraphQLString,
                args=OrderedDict(
                    (
                        ("aInt", GraphQLArgument(GraphQLInt)),
                        ("aStr", GraphQLArgument(GraphQLString)),
                    )
                ),
                resolve=lambda source, info, **args: dumps([source, args]),
            )
        )

        assert graphql_sync(schema, "{ test }") == ({"test": "[null, {}]"}, None)

        assert graphql_sync(schema, "{ test }", "Source!") == (
            {"test": '["Source!", {}]'},
            None,
        )

        assert graphql_sync(schema, '{ test(aStr: "String!") }', "Source!") == (
            {"test": '["Source!", {"aStr": "String!"}]'},
            None,
        )

        assert graphql_sync(
            schema, '{ test(aInt: -123, aStr: "String!") }', "Source!"
        ) == ({"test": '["Source!", {"aInt": -123, "aStr": "String!"}]'}, None)

