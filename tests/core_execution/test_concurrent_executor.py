from graphql.core.error import format_error
from graphql.core.execution import Executor
from graphql.core.execution.middlewares.sync import SynchronousExecutionMiddleware
from graphql.core.pyutils.defer import succeed, Deferred, fail
from graphql.core.language.parser import parse
from graphql.core.type import (GraphQLSchema, GraphQLObjectType, GraphQLField,
                               GraphQLArgument, GraphQLList, GraphQLInt, GraphQLString)
from graphql.core.type.definition import GraphQLNonNull

from .utils import raise_callback_results


def test_executes_arbitary_code():
    class Data(object):
        a = 'Apple'
        b = 'Banana'
        c = 'Cookie'
        d = 'Donut'
        e = 'Egg'

        @property
        def f(self):
            return succeed('Fish')

        def pic(self, size=50):
            return succeed('Pic of size: {}'.format(size))

        def deep(self):
            return DeepData()

        def promise(self):
            return succeed(Data())

    class DeepData(object):
        a = 'Already Been Done'
        b = 'Boring'
        c = ['Contrived', None, succeed('Confusing')]

        def deeper(self):
            return [Data(), None, succeed(Data())]

    doc = '''
        query Example($size: Int) {
            a,
            b,
            x: c
            ...c
            f
            ...on DataType {
                pic(size: $size)
                promise {
                    a
                }
            }
            deep {
                a
                b
                c
                deeper {
                    a
                    b
                }
            }
        }
        fragment c on DataType {
            d
            e
        }
    '''

    ast = parse(doc)
    expected = {
        'a': 'Apple',
        'b': 'Banana',
        'x': 'Cookie',
        'd': 'Donut',
        'e': 'Egg',
        'f': 'Fish',
        'pic': 'Pic of size: 100',
        'promise': {'a': 'Apple'},
        'deep': {
            'a': 'Already Been Done',
            'b': 'Boring',
            'c': ['Contrived', None, 'Confusing'],
            'deeper': [
                {'a': 'Apple', 'b': 'Banana'},
                None,
                {'a': 'Apple', 'b': 'Banana'}]}
    }

    DataType = GraphQLObjectType('DataType', lambda: {
        'a': GraphQLField(GraphQLString),
        'b': GraphQLField(GraphQLString),
        'c': GraphQLField(GraphQLString),
        'd': GraphQLField(GraphQLString),
        'e': GraphQLField(GraphQLString),
        'f': GraphQLField(GraphQLString),
        'pic': GraphQLField(
            args={'size': GraphQLArgument(GraphQLInt)},
            type=GraphQLString,
            resolver=lambda obj, args, *_: obj.pic(args['size']),
        ),
        'deep': GraphQLField(DeepDataType),
        'promise': GraphQLField(DataType),
    })

    DeepDataType = GraphQLObjectType('DeepDataType', {
        'a': GraphQLField(GraphQLString),
        'b': GraphQLField(GraphQLString),
        'c': GraphQLField(GraphQLList(GraphQLString)),
        'deeper': GraphQLField(GraphQLList(DataType)),
    })

    schema = GraphQLSchema(query=DataType)
    executor = Executor(schema)

    def handle_result(result):
        assert not result.errors
        assert result.data == expected

    raise_callback_results(executor.execute(doc, Data(), {'size': 100}, 'Example'), handle_result)
    raise_callback_results(executor.execute(doc, Data(), {'size': 100}, 'Example', execute_serially=True),
                           handle_result)


def test_synchronous_executor_doesnt_support_defers_with_nullable_type_getting_set_to_null():
    class Data(object):
        def promise(self):
            return succeed('i shouldn\'nt work')

        def notPromise(self):
            return 'i should work'

    DataType = GraphQLObjectType('DataType', {
        'promise': GraphQLField(GraphQLString),
        'notPromise': GraphQLField(GraphQLString),
    })
    doc = '''
    query Example {
        promise
        notPromise
    }
    '''
    schema = GraphQLSchema(query=DataType)
    executor = Executor(schema, [SynchronousExecutionMiddleware()])

    result = executor.execute(doc, Data(), operation_name='Example')
    assert not isinstance(result, Deferred)
    assert result.data == {"promise": None, 'notPromise': 'i should work'}
    formatted_errors = list(map(format_error, result.errors))
    assert formatted_errors == [{'locations': [dict(line=3, column=9)],
                                 'message': 'You cannot return a Deferred from a resolver '
                                            'when using SynchronousExecutionMiddleware'}]


def test_synchronous_executor_doesnt_support_defers():
    class Data(object):
        def promise(self):
            return succeed('i shouldn\'nt work')

        def notPromise(self):
            return 'i should work'

    DataType = GraphQLObjectType('DataType', {
        'promise': GraphQLField(GraphQLNonNull(GraphQLString)),
        'notPromise': GraphQLField(GraphQLString),
    })
    doc = '''
    query Example {
        promise
        notPromise
    }
    '''
    schema = GraphQLSchema(query=DataType)
    executor = Executor(schema, [SynchronousExecutionMiddleware()])

    result = executor.execute(doc, Data(), operation_name='Example')
    assert not isinstance(result, Deferred)
    assert result.data is None
    formatted_errors = list(map(format_error, result.errors))
    assert formatted_errors == [{'locations': [dict(line=3, column=9)],
                                 'message': 'You cannot return a Deferred from a resolver '
                                            'when using SynchronousExecutionMiddleware'}]


def test_executor_defer_failure():
    class Data(object):
        def promise(self):
            return fail(Exception('Something bad happened! Sucks :('))

        def notPromise(self):
            return 'i should work'

    DataType = GraphQLObjectType('DataType', {
        'promise': GraphQLField(GraphQLNonNull(GraphQLString)),
        'notPromise': GraphQLField(GraphQLString),
    })
    doc = '''
    query Example {
        promise
        notPromise
    }
    '''
    schema = GraphQLSchema(query=DataType)
    executor = Executor(schema)

    result = executor.execute(doc, Data(), operation_name='Example')
    assert result.called
    result = result.result
    assert result.data is None
    formatted_errors = list(map(format_error, result.errors))
    assert formatted_errors == [{'locations': [dict(line=3, column=9)],
                                 'message': "Something bad happened! Sucks :("}]


def test_synchronous_executor_will_synchronously_resolve():
    class Data(object):
        def promise(self):
            return 'I should work'

    DataType = GraphQLObjectType('DataType', {
        'promise': GraphQLField(GraphQLString),
    })
    doc = '''
    query Example {
        promise
    }
    '''
    schema = GraphQLSchema(query=DataType)
    executor = Executor(schema, [SynchronousExecutionMiddleware()])

    result = executor.execute(doc, Data(), operation_name='Example')
    assert not isinstance(result, Deferred)
    assert result.data == {"promise": 'I should work'}
    assert not result.errors
