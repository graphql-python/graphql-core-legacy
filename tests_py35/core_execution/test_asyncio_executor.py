# flake8: noqa

from graphql.core.execution.parallel_execution import Executor
from graphql.core.execution.middlewares.AsyncioExecutionMiddleware import AsyncioExecutionMiddleware
from graphql.core.type import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString
)
import functools
import asyncio


def run_until_complete(fun):
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        coro = fun(*args, **kwargs)
        return asyncio.get_event_loop().run_until_complete(coro)
    return wrapper


@run_until_complete
async def test_asyncio_py35_executor():
    doc = 'query Example { a, b }'

    async def resolver(context, *_):
        await asyncio.sleep(0.001)
        return 'hey'

    async def resolver_2(context, *_):
        await asyncio.sleep(0.003)
        return 'hey2'

    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString, resolver=resolver),
        'b': GraphQLField(GraphQLString, resolver=resolver_2)
    })

    executor = Executor(GraphQLSchema(Type), [AsyncioExecutionMiddleware()])
    result = await executor.execute(doc)
    assert not result.errors
    assert result.data == {'a': 'hey', 'b': 'hey2'}