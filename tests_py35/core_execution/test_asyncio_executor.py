# flake8: noqa

import asyncio
import functools
from graphql.error import format_error
from graphql.execution import Executor
from graphql.execution.middlewares.asyncio import AsyncioExecutionMiddleware
from graphql.type import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString
)


def run_until_complete(fun):
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        coro = fun(*args, **kwargs)
        return asyncio.get_event_loop().run_until_complete(coro)
    return wrapper


@run_until_complete
async def test_asyncio_py35_executor():
    doc = 'query Example { a, b, c }'

    async def resolver(context, *_):
        await asyncio.sleep(0.001)
        return 'hey'

    async def resolver_2(context, *_):
        await asyncio.sleep(0.003)
        return 'hey2'

    def resolver_3(context, *_):
        return 'hey3'

    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString, resolver=resolver),
        'b': GraphQLField(GraphQLString, resolver=resolver_2),
        'c': GraphQLField(GraphQLString, resolver=resolver_3)
    })

    executor = Executor([AsyncioExecutionMiddleware()])
    result = await executor.execute(GraphQLSchema(Type), doc)
    assert not result.errors
    assert result.data == {'a': 'hey', 'b': 'hey2', 'c': 'hey3'}

@run_until_complete
async def test_asyncio_py35_executor_with_error():
    doc = 'query Example { a, b }'

    async def resolver(context, *_):
        await asyncio.sleep(0.001)
        return 'hey'

    async def resolver_2(context, *_):
        await asyncio.sleep(0.003)
        raise Exception('resolver_2 failed!')

    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString, resolver=resolver),
        'b': GraphQLField(GraphQLString, resolver=resolver_2)
    })

    executor = Executor([AsyncioExecutionMiddleware()])
    result = await executor.execute(GraphQLSchema(Type), doc)
    formatted_errors = list(map(format_error, result.errors))
    assert formatted_errors == [{'locations': [{'line': 1, 'column': 20}], 'message': 'resolver_2 failed!'}]
    assert result.data == {'a': 'hey', 'b': None}
