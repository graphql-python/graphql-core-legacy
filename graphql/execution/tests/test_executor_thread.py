
from graphql.error import format_error
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (GraphQLArgument, GraphQLField, GraphQLInt,
                          GraphQLList, GraphQLObjectType, GraphQLSchema,
                          GraphQLString)

from ..executors.thread import ThreadExecutor
from .test_mutations import assert_evaluate_mutations_serially
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


def test_synchronous_error_nulls_out_error_subtrees():
    ast = parse('''
    {
        sync
        syncError
        syncReturnError
        syncReturnErrorList
        async
        asyncReject
        asyncEmptyReject
        asyncReturnError
    }
    ''')

    class Data:

        def sync(self):
            return 'sync'

        def syncError(self):
            raise Exception('Error getting syncError')

        def syncReturnError(self):
            return Exception("Error getting syncReturnError")

        def syncReturnErrorList(self):
            return [
                'sync0',
                Exception('Error getting syncReturnErrorList1'),
                'sync2',
                Exception('Error getting syncReturnErrorList3')
            ]

        def async(self):
            return resolved('async')

        def asyncReject(self):
            return rejected(Exception('Error getting asyncReject'))

        def asyncEmptyReject(self):
            return rejected(Exception('An unknown error occurred.'))

        def asyncReturnError(self):
            return resolved(Exception('Error getting asyncReturnError'))

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='Type',
            fields={
                'sync': GraphQLField(GraphQLString),
                'syncError': GraphQLField(GraphQLString),
                'syncReturnError': GraphQLField(GraphQLString),
                'syncReturnErrorList': GraphQLField(GraphQLList(GraphQLString)),
                'async': GraphQLField(GraphQLString),
                'asyncReject': GraphQLField(GraphQLString),
                'asyncEmptyReject': GraphQLField(GraphQLString),
                'asyncReturnError': GraphQLField(GraphQLString),
            }
        )
    )

    def sort_key(item):
        locations = item['locations'][0]
        return (locations['line'], locations['column'])

    def handle_results(result):
        assert result.data == {
            'async': 'async',
            'asyncEmptyReject': None,
            'asyncReject': None,
            'asyncReturnError': None,
            'sync': 'sync',
            'syncError': None,
            'syncReturnError': None,
            'syncReturnErrorList': ['sync0', None, 'sync2', None]
        }
        assert sorted(list(map(format_error, result.errors)), key=sort_key) == sorted([
            {'locations': [{'line': 4, 'column': 9}], 'message': 'Error getting syncError'},
            {'locations': [{'line': 5, 'column': 9}], 'message': 'Error getting syncReturnError'},
            {'locations': [{'line': 6, 'column': 9}], 'message': 'Error getting syncReturnErrorList1'},
            {'locations': [{'line': 6, 'column': 9}], 'message': 'Error getting syncReturnErrorList3'},
            {'locations': [{'line': 8, 'column': 9}], 'message': 'Error getting asyncReject'},
            {'locations': [{'line': 9, 'column': 9}], 'message': 'An unknown error occurred.'},
            {'locations': [{'line': 10, 'column': 9}], 'message': 'Error getting asyncReturnError'}
        ], key=sort_key)

    handle_results(execute(schema, ast, Data(), executor=ThreadExecutor()))


def test_evaluates_mutations_serially():
    assert_evaluate_mutations_serially(executor=ThreadExecutor())
