# flake8: noqa

import asyncio
import functools
from graphql.core.execution import Executor
from graphql.core.execution.middlewares.asyncio import AsyncioExecutionMiddleware
from graphql.core.language.location import SourceLocation
from graphql.core.type import (
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

    executor = Executor(GraphQLSchema(Type), [AsyncioExecutionMiddleware()])
    result = await executor.execute(doc)
    assert result.errors == [{'locations': [SourceLocation(1, 20)], 'message': 'resolver_2 failed!'}]
    assert result.data == {'a': 'hey', 'b': None}