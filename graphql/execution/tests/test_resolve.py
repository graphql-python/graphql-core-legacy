# type: ignore
import json
from collections import OrderedDict

from graphql import graphql
from graphql.type import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInputObjectField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)
from graphql.execution import ExecutionResult
from promise import Promise

# from graphql.execution.base import ResolveInfo
# from typing import Any
# from typing import Optional
# from promise.promise import Promise
# from graphql.type.definition import GraphQLField
# from graphql.type.schema import GraphQLSchema


class CustomPromise(Promise):
    @classmethod
    def fulfilled(cls, x):
        # type: (str) -> CustomPromise
        p = cls()
        p.fulfill(x)
        return p

    resolve = fulfilled

    @classmethod
    def rejected(cls, reason):
        p = cls()
        p.reject(reason)
        return p


def _test_schema(test_field):
    # type: (GraphQLField) -> GraphQLSchema
    return GraphQLSchema(
        query=GraphQLObjectType(name="Query", fields={"test": test_field})
    )


def test_default_function_accesses_properties():
    # type: () -> None
    schema = _test_schema(GraphQLField(GraphQLString))

    class source:
        test = "testValue"

    result = graphql(schema, "{ test }", source)
    assert not result.errors
    assert result.data == {"test": "testValue"}


def test_default_function_calls_methods():
    # type: () -> None
    schema = _test_schema(GraphQLField(GraphQLString))

    class source:
        _secret = "testValue"

        def test(self):
            # type: () -> str
            return self._secret

    result = graphql(schema, "{ test }", source())
    assert not result.errors
    assert result.data == {"test": "testValue"}


def test_uses_provided_resolve_function():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[str], ResolveInfo, **Any) -> str
        return json.dumps([source, args], separators=(",", ":"))

    schema = _test_schema(
        GraphQLField(
            GraphQLString,
            args=OrderedDict(
                [
                    ("aStr", GraphQLArgument(GraphQLString)),
                    ("aInt", GraphQLArgument(GraphQLInt)),
                ]
            ),
            resolver=resolver,
        )
    )

    result = graphql(schema, "{ test }", None)
    assert not result.errors
    assert result.data == {"test": "[null,{}]"}

    result = graphql(schema, '{ test(aStr: "String!") }', "Source!")
    assert not result.errors
    assert result.data == {"test": '["Source!",{"aStr":"String!"}]'}

    result = graphql(schema, '{ test(aInt: -123, aStr: "String!",) }', "Source!")
    assert not result.errors
    assert result.data in [
        {"test": '["Source!",{"aStr":"String!","aInt":-123}]'},
        {"test": '["Source!",{"aInt":-123,"aStr":"String!"}]'},
    ]


def test_handles_resolved_extensions_with_data():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[str], ResolveInfo, **Any) -> ExecutionResult
        extensions = info.extensions or {}
        extensions["test_extensions"] = extensions.get("test_extensions", {})
        extensions["test_extensions"].update({"foo": "bar"})
        return ExecutionResult(data="foobar", extensions=extensions)

    schema = _test_schema(GraphQLField(GraphQLString, resolver=resolver))

    result = graphql(schema, "{ test }", None)
    assert not result.errors
    assert result.data == {"test": "foobar"}
    assert result.extensions == {"test_extensions": {"foo": "bar"}}


def test_handles_resolved_extensions_with_errors():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[str], ResolveInfo, **Any) -> ExecutionResult
        extensions = info.extensions or {}
        extensions["errors"] = extensions.get("errors", {})
        extensions["errors"].update({"test": {"foo": "bar"}})
        return ExecutionResult(errors=[Exception()], extensions=extensions)

    schema = _test_schema(GraphQLField(GraphQLString, resolver=resolver))

    result = graphql(schema, "{ test }", None)
    assert len(result.errors) == 1
    assert result.data == {"test": None}
    assert result.extensions == {"errors": {"test": {"foo": "bar"}}}


def test_handles_resolved_promises():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[Any], ResolveInfo, **Any) -> Promise
        return Promise.resolve("foo")

    schema = _test_schema(GraphQLField(GraphQLString, resolver=resolver))

    result = graphql(schema, "{ test }", None)
    assert not result.errors
    assert result.data == {"test": "foo"}


def test_handles_resolved_promises_extensions():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[Any], ResolveInfo, **Any) -> Promise
        extensions = info.extensions or {}
        extensions["test_extensions"] = extensions.get("test_extensions", {})
        extensions["test_extensions"].update({"foo": "bar"})
        return Promise.resolve(ExecutionResult(data="foobar", extensions=extensions))

    schema = _test_schema(GraphQLField(GraphQLString, resolver=resolver))

    result = graphql(schema, "{ test }", None)
    assert not result.errors
    assert result.data == {"test": "foobar"}
    assert result.extensions == {"test_extensions": {"foo": "bar"}}


def test_handles_resolved_custom_promises():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[Any], ResolveInfo, **Any) -> CustomPromise
        return CustomPromise.resolve("custom_foo")

    schema = _test_schema(GraphQLField(GraphQLString, resolver=resolver))

    result = graphql(schema, "{ test }", None)
    assert not result.errors
    assert result.data == {"test": "custom_foo"}


def test_maps_argument_out_names_well():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[str], ResolveInfo, **Any) -> str
        return json.dumps([source, args], separators=(",", ":"))

    schema = _test_schema(
        GraphQLField(
            GraphQLString,
            args=OrderedDict(
                [
                    ("aStr", GraphQLArgument(GraphQLString, out_name="a_str")),
                    ("aInt", GraphQLArgument(GraphQLInt, out_name="a_int")),
                ]
            ),
            resolver=resolver,
        )
    )

    result = graphql(schema, "{ test }", None)
    assert not result.errors
    assert result.data == {"test": "[null,{}]"}

    result = graphql(schema, '{ test(aStr: "String!") }', "Source!")
    assert not result.errors
    assert result.data == {"test": '["Source!",{"a_str":"String!"}]'}

    result = graphql(schema, '{ test(aInt: -123, aStr: "String!",) }', "Source!")
    assert not result.errors
    assert result.data in [
        {"test": '["Source!",{"a_str":"String!","a_int":-123}]'},
        {"test": '["Source!",{"a_int":-123,"a_str":"String!"}]'},
    ]


def test_maps_argument_out_names_well_with_input():
    # type: () -> None
    def resolver(source, info, **args):
        # type: (Optional[str], ResolveInfo, **Any) -> str
        return json.dumps([source, args], separators=(",", ":"))

    TestInputObject = GraphQLInputObjectType(
        "TestInputObject",
        lambda: OrderedDict(
            [
                (
                    "inputOne",
                    GraphQLInputObjectField(GraphQLString, out_name="input_one"),
                ),
                (
                    "inputRecursive",
                    GraphQLInputObjectField(
                        TestInputObject, out_name="input_recursive"
                    ),
                ),
            ]
        ),
    )

    schema = _test_schema(
        GraphQLField(
            GraphQLString,
            args=OrderedDict(
                [("aInput", GraphQLArgument(TestInputObject, out_name="a_input"))]
            ),
            resolver=resolver,
        )
    )

    result = graphql(schema, "{ test }", None)
    assert not result.errors
    assert result.data == {"test": "[null,{}]"}

    result = graphql(schema, '{ test(aInput: {inputOne: "String!"} ) }', "Source!")
    assert not result.errors
    assert result.data == {"test": '["Source!",{"a_input":{"input_one":"String!"}}]'}

    result = graphql(
        schema,
        '{ test(aInput: {inputRecursive:{inputOne: "SourceRecursive!"}} ) }',
        "Source!",
    )
    assert not result.errors
    assert result.data == {
        "test": '["Source!",{"a_input":{"input_recursive":{"input_one":"SourceRecursive!"}}}]'
    }
