
from graphql.error import format_error
from graphql.execution.execute import execute
from graphql.language.parser import parse
from graphql.type import (GraphQLArgument, GraphQLField, GraphQLInt,
                          GraphQLList, GraphQLObjectType, GraphQLSchema,
                          GraphQLString)
from graphql.type.definition import GraphQLNonNull

from ..executors.thread import ThreadExecutor
from .utils import rejected, resolved


def test_executes_arbitary_code():
    class Data(object):
        a = 'Apple'
        b = 'Banana'
        c = 'Cookie'
        d = 'Donut'
        e = 'Egg'

        @property
        def f(self):
            return resolved('Fish')

        def pic(self, size=50):
            return resolved('Pic of size: {}'.format(size))

        def deep(self):
            return DeepData()

        def promise(self):
            return resolved(Data())

    class DeepData(object):
        a = 'Already Been Done'
        b = 'Boring'
        c = ['Contrived', None, resolved('Confusing')]

        def deeper(self):
            return [Data(), None, resolved(Data())]

    ast = parse('''
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
    ''')

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

    def handle_result(result):
        assert not result.errors
        assert result.data == expected

    handle_result(
        execute(
            schema,
            ast,
            Data(),
            variable_values={
                'size': 100},
            operation_name='Example',
            executor=ThreadExecutor()))
    handle_result(execute(schema, ast, Data(), variable_values={'size': 100}, operation_name='Example'))


# def test_synchronous_executor_doesnt_support_defers_with_nullable_type_getting_set_to_null():
#     class Data(object):

#         def promise(self):
#             return succeed('i shouldn\'nt work')

#         def notPromise(self):
#             return 'i should work'

#     DataType = GraphQLObjectType('DataType', {
#         'promise': GraphQLField(GraphQLString),
#         'notPromise': GraphQLField(GraphQLString),
#     })
#     doc = '''
#     query Example {
#         promise
#         notPromise
#     }
#     '''
#     schema = GraphQLSchema(query=DataType)
#     executor = Executor([SynchronousExecutionMiddleware()])

#     result = executor.execute(schema, doc, Data(), operation_name='Example')
#     assert not isinstance(result, Deferred)
#     assert result.data == {"promise": None, 'notPromise': 'i should work'}
#     formatted_errors = list(map(format_error, result.errors))
#     assert formatted_errors == [{'locations': [dict(line=3, column=9)],
#                                  'message': 'You cannot return a Deferred from a resolver '
#                                             'when using SynchronousExecutionMiddleware'}]


# def test_synchronous_executor_doesnt_support_defers():
#     class Data(object):

#         def promise(self):
#             return succeed('i shouldn\'nt work')

#         def notPromise(self):
#             return 'i should work'

#     DataType = GraphQLObjectType('DataType', {
#         'promise': GraphQLField(GraphQLNonNull(GraphQLString)),
#         'notPromise': GraphQLField(GraphQLString),
#     })
#     doc = '''
#     query Example {
#         promise
#         notPromise
#     }
#     '''
#     schema = GraphQLSchema(query=DataType)
#     executor = Executor([SynchronousExecutionMiddleware()])

#     result = executor.execute(schema, doc, Data(), operation_name='Example')
#     assert not isinstance(result, Deferred)
#     assert result.data is None
#     formatted_errors = list(map(format_error, result.errors))
#     assert formatted_errors == [{'locations': [dict(line=3, column=9)],
#                                  'message': 'You cannot return a Deferred from a resolver '
#                                             'when using SynchronousExecutionMiddleware'}]


# def test_executor_defer_failure():
#     class Data(object):

#         def promise(self):
#             return fail(Exception('Something bad happened! Sucks :('))

#         def notPromise(self):
#             return 'i should work'

#     DataType = GraphQLObjectType('DataType', {
#         'promise': GraphQLField(GraphQLNonNull(GraphQLString)),
#         'notPromise': GraphQLField(GraphQLString),
#     })
#     doc = '''
#     query Example {
#         promise
#         notPromise
#     }
#     '''
#     schema = GraphQLSchema(query=DataType)
#     executor = Executor()

#     result = executor.execute(schema, doc, Data(), operation_name='Example')
#     assert result.called
#     result = result.result
#     assert result.data is None
#     formatted_errors = list(map(format_error, result.errors))
#     assert formatted_errors == [{'locations': [dict(line=3, column=9)],
#                                  'message': "Something bad happened! Sucks :("}]


# def test_synchronous_executor_will_synchronously_resolve():
#     class Data(object):

#         def promise(self):
#             return 'I should work'

#     DataType = GraphQLObjectType('DataType', {
#         'promise': GraphQLField(GraphQLString),
#     })
#     doc = '''
#     query Example {
#         promise
#     }
#     '''
#     schema = GraphQLSchema(query=DataType)
#     executor = Executor([SynchronousExecutionMiddleware()])

#     result = executor.execute(schema, doc, Data(), operation_name='Example')
#     assert not isinstance(result, Deferred)
#     assert result.data == {"promise": 'I should work'}
#     assert not result.errors


# def test_synchronous_error_nulls_out_error_subtrees():
#     doc = '''
#     {
#         sync
#         syncError
#         syncReturnError
#         syncReturnErrorList
#         async
#         asyncReject
#         asyncEmptyReject
#         asyncReturnError
#     }
#     '''

#     class Data:

#         def sync(self):
#             return 'sync'

#         def syncError(self):
#             raise Exception('Error getting syncError')

#         def syncReturnError(self):
#             return Exception("Error getting syncReturnError")

#         def syncReturnErrorList(self):
#             return [
#                 'sync0',
#                 Exception('Error getting syncReturnErrorList1'),
#                 'sync2',
#                 Exception('Error getting syncReturnErrorList3')
#             ]

#         def async(self):
#             return succeed('async')

#         def asyncReject(self):
#             return fail(Exception('Error getting asyncReject'))

#         def asyncEmptyReject(self):
#             return fail()

#         def asyncReturnError(self):
#             return succeed(Exception('Error getting asyncReturnError'))

#     schema = GraphQLSchema(
#         query=GraphQLObjectType(
#             name='Type',
#             fields={
#                 'sync': GraphQLField(GraphQLString),
#                 'syncError': GraphQLField(GraphQLString),
#                 'syncReturnError': GraphQLField(GraphQLString),
#                 'syncReturnErrorList': GraphQLField(GraphQLList(GraphQLString)),
#                 'async': GraphQLField(GraphQLString),
#                 'asyncReject': GraphQLField(GraphQLString),
#                 'asyncEmptyReject': GraphQLField(GraphQLString),
#                 'asyncReturnError': GraphQLField(GraphQLString),
#             }
#         )
#     )

#     executor = Executor(map_type=OrderedDict)

#     def handle_results(result):
#         assert result.data == {
#             'async': 'async',
#             'asyncEmptyReject': None,
#             'asyncReject': None,
#             'asyncReturnError': None,
#             'sync': 'sync',
#             'syncError': None,
#             'syncReturnError': None,
#             'syncReturnErrorList': ['sync0', None, 'sync2', None]
#         }
#         assert list(map(format_error, result.errors)) == [
#             {'locations': [{'line': 4, 'column': 9}], 'message': 'Error getting syncError'},
#             {'locations': [{'line': 5, 'column': 9}], 'message': 'Error getting syncReturnError'},
#             {'locations': [{'line': 6, 'column': 9}], 'message': 'Error getting syncReturnErrorList1'},
#             {'locations': [{'line': 6, 'column': 9}], 'message': 'Error getting syncReturnErrorList3'},
#             {'locations': [{'line': 8, 'column': 9}], 'message': 'Error getting asyncReject'},
#             {'locations': [{'line': 9, 'column': 9}], 'message': 'An unknown error occurred.'},
#             {'locations': [{'line': 10, 'column': 9}], 'message': 'Error getting asyncReturnError'}
#         ]

#     raise_callback_results(executor.execute(schema, doc, Data()), handle_results)


# def test_executor_can_enforce_strict_ordering():
#     Type = GraphQLObjectType('Type', lambda: {
#         'a': GraphQLField(GraphQLString,
#                           resolver=lambda *_: succeed('Apple')),
#         'b': GraphQLField(GraphQLString,
#                           resolver=lambda *_: succeed('Banana')),
#         'c': GraphQLField(GraphQLString,
#                           resolver=lambda *_: succeed('Cherry')),
#         'deep': GraphQLField(Type, resolver=lambda *_: succeed({})),
#     })
#     schema = GraphQLSchema(query=Type)
#     executor = Executor(map_type=OrderedDict)

#     query = '{ a b c aa: c cc: c bb: b aaz: a bbz: b deep { b a c deeper: deep { c a b } } ' \
#             'ccz: c zzz: c aaa: a }'

#     def handle_results(result):
#         assert not result.errors

#         data = result.data
#         assert isinstance(data, OrderedDict)
#         assert list(data.keys()) == ['a', 'b', 'c', 'aa', 'cc', 'bb', 'aaz', 'bbz', 'deep', 'ccz', 'zzz', 'aaa']
#         deep = data['deep']
#         assert isinstance(deep, OrderedDict)
#         assert list(deep.keys()) == ['b', 'a', 'c', 'deeper']
#         deeper = deep['deeper']
#         assert isinstance(deeper, OrderedDict)
#         assert list(deeper.keys()) == ['c', 'a', 'b']

#     raise_callback_results(executor.execute(schema, query), handle_results)
#     raise_callback_results(executor.execute(schema, query, execute_serially=True), handle_results)
