# flake8: noqa
import gevent

from graphql.error import format_error
from graphql.execution import Executor
from graphql.execution.middlewares.gevent import (GeventExecutionMiddleware,
                                                       run_in_greenlet)
from graphql.language.location import SourceLocation
from graphql.type import (GraphQLField, GraphQLObjectType, GraphQLSchema,
                               GraphQLString)


def test_gevent_executor():
    @run_in_greenlet
    def resolver(context, *_):
        gevent.sleep(0.001)
        return 'hey'

    @run_in_greenlet
    def resolver_2(context, *_):
        gevent.sleep(0.003)
        return 'hey2'

    def resolver_3(contest, *_):
        return 'hey3'

    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString, resolver=resolver),
        'b': GraphQLField(GraphQLString, resolver=resolver_2),
        'c': GraphQLField(GraphQLString, resolver=resolver_3)
    })

    doc = '{ a b c }'
    executor = Executor([GeventExecutionMiddleware()])
    result = executor.execute(GraphQLSchema(Type), doc)
    assert not result.errors
    assert result.data == {'a': 'hey', 'b': 'hey2', 'c': 'hey3'}


def test_gevent_executor_with_error():
    doc = 'query Example { a, b }'

    @run_in_greenlet
    def resolver(context, *_):
        gevent.sleep(0.001)
        return 'hey'

    @run_in_greenlet
    def resolver_2(context, *_):
        gevent.sleep(0.003)
        raise Exception('resolver_2 failed!')

    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString, resolver=resolver),
        'b': GraphQLField(GraphQLString, resolver=resolver_2)
    })

    executor = Executor([GeventExecutionMiddleware()])
    result = executor.execute(GraphQLSchema(Type), doc)
    formatted_errors = list(map(format_error, result.errors))
    assert formatted_errors == [{'locations': [{'line': 1, 'column': 20}], 'message': 'resolver_2 failed!'}]
    assert result.data == {'a': 'hey', 'b': None}
