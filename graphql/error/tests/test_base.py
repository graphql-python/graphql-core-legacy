import sys

import pytest
import traceback

from promise import Promise

from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

# Necessary for static type checking
if False:  # flake8: noqa
    from graphql.execution.base import ResolveInfo
    from typing import Any
    from typing import Optional


def test_raise():
    # type: () -> None
    ast = parse("query Example { a }")

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> None
        raise Exception("Failed")

    Type = GraphQLObjectType(
        "Type", {"a": GraphQLField(GraphQLString, resolver=resolver)}
    )

    result = execute(GraphQLSchema(Type), ast)
    assert str(result.errors[0]) == "Failed"


def test_reraise():
    # type: () -> None
    ast = parse("query Example { a }")

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> None
        raise Exception("Failed")

    Type = GraphQLObjectType(
        "Type", {"a": GraphQLField(GraphQLString, resolver=resolver)}
    )

    result = execute(GraphQLSchema(Type), ast)
    with pytest.raises(Exception) as exc_info:
        result.errors[0].reraise()

    extracted = traceback.extract_tb(exc_info.tb)
    formatted_tb = [row[2:] for row in extracted]
    formatted_tb = [tb for tb in formatted_tb if tb[0] != "reraise"]

    assert formatted_tb == [
        ("test_reraise", "result.errors[0].reraise()"),
        (
            "resolve_or_error",
            "return executor.execute(resolve_fn, source, info, **args)",
        ),
        ("execute", "return fn(*args, **kwargs)"),
        ("resolver", 'raise Exception("Failed")'),
    ]

    assert str(exc_info.value) == "Failed"


@pytest.mark.skipif(sys.version_info < (3,), reason="this works only with Python 3")
def test_reraise_from_promise():
    # type: () -> None
    ast = parse("query Example { a }")

    def fail():
        raise Exception("Failed")

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> None
        return Promise(lambda resolve, reject: resolve(fail()))

    Type = GraphQLObjectType(
        "Type", {"a": GraphQLField(GraphQLString, resolver=resolver)}
    )

    result = execute(GraphQLSchema(Type), ast)
    with pytest.raises(Exception) as exc_info:
        result.errors[0].reraise()

    extracted = traceback.extract_tb(exc_info.tb)
    formatted_tb = [row[2:] for row in extracted]
    formatted_tb = [tb for tb in formatted_tb if tb[0] != "reraise"]

    print(formatted_tb)

    assert formatted_tb == [
        ("test_reraise_from_promise", "result.errors[0].reraise()"),
        ("_resolve_from_executor", "executor(resolve, reject)"),
        ("<lambda>", "return Promise(lambda resolve, reject: resolve(fail()))"),
        ("fail", 'raise Exception("Failed")'),
    ]

    assert str(exc_info.value) == "Failed"
