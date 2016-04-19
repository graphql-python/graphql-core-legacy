from collections import namedtuple

from graphql.core.error import format_error
from graphql.core.execution import Executor, execute
from graphql.core.language.parser import parse
from graphql.core.pyutils.defer import fail, succeed
from graphql.core.type import (GraphQLField, GraphQLInt, GraphQLList,
                               GraphQLNonNull, GraphQLObjectType,
                               GraphQLSchema)

Data = namedtuple('Data', 'test')
ast = parse('{ nest { test } }')
executor = Executor()


def check(test_data, expected):
    def run_check(self):
        test_type = self.type

        data = Data(test=test_data)
        DataType = GraphQLObjectType(
            name='DataType',
            fields=lambda: {
                'test': GraphQLField(test_type),
                'nest': GraphQLField(DataType, resolver=lambda *_: data)
            }
        )

        schema = GraphQLSchema(query=DataType)
        response = executor.execute(schema, ast, data)
        assert response.called
        response = response.result

        if response.errors:
            result = {
                'data': response.data,
                'errors': [format_error(e) for e in response.errors]
            }
        else:
            result = {
                'data': response.data
            }

        assert result == expected

    return run_check


class Test_ListOfT_Array_T:  # [T] Array<T>
    type = GraphQLList(GraphQLInt)

    test_contains_values = check([1, 2], {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check([1, None, 2], {'data': {'nest': {'test': [1, None, 2]}}})
    test_returns_null = check(None, {'data': {'nest': {'test': None}}})


class Test_ListOfT_Promise_Array_T:  # [T] Promise<Array<T>>
    type = GraphQLList(GraphQLInt)

    test_contains_values = check(succeed([1, 2]), {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check(succeed([1, None, 2]), {'data': {'nest': {'test': [1, None, 2]}}})
    test_returns_null = check(succeed(None), {'data': {'nest': {'test': None}}})
    test_rejected = check(lambda: fail(Exception('bad')), {
        'data': {'nest': {'test': None}},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })


class Test_ListOfT_Array_Promise_T:  # [T] Array<Promise<T>>
    type = GraphQLList(GraphQLInt)

    test_contains_values = check([succeed(1), succeed(2)], {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check([succeed(1), succeed(None), succeed(2)], {'data': {'nest': {'test': [1, None, 2]}}})
    test_contains_reject = check(lambda: [succeed(1), fail(Exception('bad')), succeed(2)], {
        'data': {'nest': {'test': [1, None, 2]}},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })


class Test_NotNullListOfT_Array_T:  # [T]! Array<T>
    type = GraphQLNonNull(GraphQLList(GraphQLInt))

    test_contains_values = check(succeed([1, 2]), {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check(succeed([1, None, 2]), {'data': {'nest': {'test': [1, None, 2]}}})
    test_returns_null = check(succeed(None), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })


class Test_NotNullListOfT_Promise_Array_T:  # [T]! Promise<Array<T>>>
    type = GraphQLNonNull(GraphQLList(GraphQLInt))

    test_contains_values = check(succeed([1, 2]), {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check(succeed([1, None, 2]), {'data': {'nest': {'test': [1, None, 2]}}})
    test_returns_null = check(succeed(None), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })

    test_rejected = check(lambda: fail(Exception('bad')), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })


class Test_NotNullListOfT_Array_Promise_T:  # [T]! Promise<Array<T>>>
    type = GraphQLNonNull(GraphQLList(GraphQLInt))
    test_contains_values = check([succeed(1), succeed(2)], {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check([succeed(1), succeed(None), succeed(2)], {'data': {'nest': {'test': [1, None, 2]}}})
    test_contains_reject = check(lambda: [succeed(1), fail(Exception('bad')), succeed(2)], {
        'data': {'nest': {'test': [1, None, 2]}},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })


class TestListOfNotNullT_Array_T:  # [T!] Array<T>
    type = GraphQLList(GraphQLNonNull(GraphQLInt))

    test_contains_values = check([1, 2], {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check([1, None, 2], {
        'data': {'nest': {'test': None}},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })
    test_returns_null = check(None, {'data': {'nest': {'test': None}}})


class TestListOfNotNullT_Promise_Array_T:  # [T!] Promise<Array<T>>
    type = GraphQLList(GraphQLNonNull(GraphQLInt))

    test_contains_value = check(succeed([1, 2]), {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check(succeed([1, None, 2]), {
        'data': {'nest': {'test': None}},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })

    test_returns_null = check(succeed(None), {'data': {'nest': {'test': None}}})

    test_rejected = check(lambda: fail(Exception('bad')), {
        'data': {'nest': {'test': None}},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })


class TestListOfNotNullT_Array_Promise_T:  # [T!] Array<Promise<T>>
    type = GraphQLList(GraphQLNonNull(GraphQLInt))

    test_contains_values = check([succeed(1), succeed(2)], {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check([succeed(1), succeed(None), succeed(2)], {
        'data': {'nest': {'test': None}},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })
    test_contains_reject = check(lambda: [succeed(1), fail(Exception('bad')), succeed(2)], {
        'data': {'nest': {'test': None}},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })


class TestNotNullListOfNotNullT_Array_T:  # [T!]! Array<T>
    type = GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLInt)))

    test_contains_values = check([1, 2], {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check([1, None, 2], {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })
    test_returns_null = check(None, {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })


class TestNotNullListOfNotNullT_Promise_Array_T:  # [T!]! Promise<Array<T>>
    type = GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLInt)))

    test_contains_value = check(succeed([1, 2]), {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check(succeed([1, None, 2]), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })

    test_returns_null = check(succeed(None), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })

    test_rejected = check(lambda: fail(Exception('bad')), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })


class TestNotNullListOfNotNullT_Array_Promise_T:  # [T!]! Array<Promise<T>>
    type = GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLInt)))

    test_contains_values = check([succeed(1), succeed(2)], {'data': {'nest': {'test': [1, 2]}}})
    test_contains_null = check([succeed(1), succeed(None), succeed(2)], {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}],
                    'message': 'Cannot return null for non-nullable field DataType.test.'}]
    })
    test_contains_reject = check(lambda: [succeed(1), fail(Exception('bad')), succeed(2)], {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 10, 'line': 1}], 'message': 'bad'}]
    })
