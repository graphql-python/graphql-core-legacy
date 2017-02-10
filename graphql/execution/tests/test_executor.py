import json

from pytest import raises

from graphql.error import GraphQLError
from graphql.execution import MiddlewareManager, execute
from graphql.language.parser import parse
from graphql.type import (GraphQLArgument, GraphQLBoolean, GraphQLField,
                          GraphQLInt, GraphQLList, GraphQLObjectType,
                          GraphQLSchema, GraphQLString)


def test_executes_arbitary_code():
    class Data(object):
        a = 'Apple'
        b = 'Banana'
        c = 'Cookie'
        d = 'Donut'
        e = 'Egg'
        f = 'Fish'

        def pic(self, size=50):
            return 'Pic of size: {}'.format(size)

        def deep(self):
            return DeepData()

        def promise(self):
            # FIXME: promise is unsupported
            return Data()

    class DeepData(object):
        a = 'Already Been Done'
        b = 'Boring'
        c = ['Contrived', None, 'Confusing']

        def deeper(self):
            return [Data(), None, Data()]

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

    result = execute(schema, ast, Data(), operation_name='Example', variable_values={'size': 100})
    assert not result.errors
    assert result.data == expected


def test_merges_parallel_fragments():
    ast = parse('''
        { a, ...FragOne, ...FragTwo }

        fragment FragOne on Type {
            b
            deep { b, deeper: deep { b } }
        }

        fragment FragTwo on Type {
            c
            deep { c, deeper: deep { c } }
        }
    ''')

    Type = GraphQLObjectType('Type', lambda: {
        'a': GraphQLField(GraphQLString,
                          resolver=lambda *_: 'Apple'),
        'b': GraphQLField(GraphQLString,
                          resolver=lambda *_: 'Banana'),
        'c': GraphQLField(GraphQLString,
                          resolver=lambda *_: 'Cherry'),
        'deep': GraphQLField(Type, resolver=lambda *_: {}),
    })

    schema = GraphQLSchema(query=Type)
    result = execute(schema, ast)
    assert not result.errors
    assert result.data == \
        {
            'a': 'Apple',
            'b': 'Banana',
            'c': 'Cherry',
            'deep': {
                'b': 'Banana',
                'c': 'Cherry',
                'deeper': {
                    'b': 'Banana',
                    'c': 'Cherry'}}
        }


def test_threads_root_value_context_correctly():
    doc = 'query Example { a }'

    class Data(object):
        context_thing = 'thing'

    ast = parse(doc)

    def resolver(root_value, *_):
        assert root_value.context_thing == 'thing'
        resolver.got_here = True

    resolver.got_here = False

    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString, resolver=resolver)
    })

    result = execute(GraphQLSchema(Type), ast, Data(), operation_name='Example')
    assert not result.errors
    assert resolver.got_here


def test_correctly_threads_arguments():
    doc = '''
        query Example {
            b(numArg: 123, stringArg: "foo")
        }
    '''

    def resolver(_, args, *_args):
        assert args['numArg'] == 123
        assert args['stringArg'] == 'foo'
        resolver.got_here = True

    resolver.got_here = False

    doc_ast = parse(doc)

    Type = GraphQLObjectType('Type', {
        'b': GraphQLField(
            GraphQLString,
            args={
                'numArg': GraphQLArgument(GraphQLInt),
                'stringArg': GraphQLArgument(GraphQLString),
            },
            resolver=resolver),
    })

    result = execute(GraphQLSchema(Type), doc_ast, None, operation_name='Example')
    assert not result.errors
    assert resolver.got_here


def test_nulls_out_error_subtrees():
    doc = '''{
        ok,
        error
    }'''

    class Data(object):

        def ok(self):
            return 'ok'

        def error(self):
            raise Exception('Error getting error')

    doc_ast = parse(doc)

    Type = GraphQLObjectType('Type', {
        'ok': GraphQLField(GraphQLString),
        'error': GraphQLField(GraphQLString),
    })

    result = execute(GraphQLSchema(Type), doc_ast, Data())
    assert result.data == {'ok': 'ok', 'error': None}
    assert len(result.errors) == 1
    assert result.errors[0].message == 'Error getting error'
    # TODO: check error location


def test_uses_the_inline_operation_if_no_operation_name_is_provided():
    doc = '{ a }'

    class Data(object):
        a = 'b'

    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Type), ast, Data())
    assert not result.errors
    assert result.data == {'a': 'b'}


def test_uses_the_only_operation_if_no_operation_name_is_provided():
    doc = 'query Example { a }'

    class Data(object):
        a = 'b'

    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Type), ast, Data())
    assert not result.errors
    assert result.data == {'a': 'b'}


def test_uses_the_named_operation_if_operation_name_is_provided():
    doc = 'query Example { first: a } query OtherExample { second: a }'

    class Data(object):
        a = 'b'

    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Type), ast, Data(), operation_name='OtherExample')
    assert not result.errors
    assert result.data == {'second': 'b'}


def test_raises_if_no_operation_is_provided():
    doc = 'fragment Example on Type { a }'

    class Data(object):
        a = 'b'

    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    with raises(GraphQLError) as excinfo:
        execute(GraphQLSchema(Type), ast, Data())
    assert 'Must provide an operation.' == str(excinfo.value)


def test_raises_if_no_operation_name_is_provided_with_multiple_operations():
    doc = 'query Example { a } query OtherExample { a }'

    class Data(object):
        a = 'b'

    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    with raises(GraphQLError) as excinfo:
        execute(GraphQLSchema(Type), ast, Data(), operation_name="UnknownExample")
    assert 'Unknown operation named "UnknownExample".' == str(excinfo.value)


def test_raises_if_unknown_operation_name_is_provided():
    doc = 'query Example { a } query OtherExample { a }'

    class Data(object):
        a = 'b'

    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    with raises(GraphQLError) as excinfo:
        execute(GraphQLSchema(Type), ast, Data())
    assert 'Must provide operation name if query contains multiple operations.' == str(excinfo.value)


def test_uses_the_query_schema_for_queries():
    doc = 'query Q { a } mutation M { c } subscription S { a }'

    class Data(object):
        a = 'b'
        c = 'd'

    ast = parse(doc)
    Q = GraphQLObjectType('Q', {
        'a': GraphQLField(GraphQLString)
    })
    M = GraphQLObjectType('M', {
        'c': GraphQLField(GraphQLString)
    })
    S = GraphQLObjectType('S', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Q, M, S), ast, Data(), operation_name='Q')
    assert not result.errors
    assert result.data == {'a': 'b'}


def test_uses_the_mutation_schema_for_queries():
    doc = 'query Q { a } mutation M { c }'

    class Data(object):
        a = 'b'
        c = 'd'

    ast = parse(doc)
    Q = GraphQLObjectType('Q', {
        'a': GraphQLField(GraphQLString)
    })
    M = GraphQLObjectType('M', {
        'c': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Q, M), ast, Data(), operation_name='M')
    assert not result.errors
    assert result.data == {'c': 'd'}


def test_uses_the_subscription_schema_for_subscriptions():
    doc = 'query Q { a } subscription S { a }'

    class Data(object):
        a = 'b'
        c = 'd'

    ast = parse(doc)
    Q = GraphQLObjectType('Q', {
        'a': GraphQLField(GraphQLString)
    })
    S = GraphQLObjectType('S', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Q, subscription=S), ast, Data(), operation_name='S')
    assert not result.errors
    assert result.data == {'a': 'b'}


def test_avoids_recursion():
    doc = '''
        query Q {
            a
            ...Frag
            ...Frag
        }
        fragment Frag on Type {
            a,
            ...Frag
        }
    '''

    class Data(object):
        a = 'b'

    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Type), ast, Data(), operation_name='Q')
    assert not result.errors
    assert result.data == {'a': 'b'}


def test_does_not_include_illegal_fields_in_output():
    doc = 'mutation M { thisIsIllegalDontIncludeMe }'
    ast = parse(doc)
    Q = GraphQLObjectType('Q', {
        'a': GraphQLField(GraphQLString)
    })
    M = GraphQLObjectType('M', {
        'c': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Q, M), ast)
    assert not result.errors
    assert result.data == {}


def test_does_not_include_arguments_that_were_not_set():
    schema = GraphQLSchema(GraphQLObjectType(
        'Type',
        {
            'field': GraphQLField(
                GraphQLString,
                resolver=lambda data, args, *_: args and json.dumps(args, sort_keys=True, separators=(',', ':')),
                args={
                    'a': GraphQLArgument(GraphQLBoolean),
                    'b': GraphQLArgument(GraphQLBoolean),
                    'c': GraphQLArgument(GraphQLBoolean),
                    'd': GraphQLArgument(GraphQLInt),
                    'e': GraphQLArgument(GraphQLInt),
                }
            )
        }
    ))

    ast = parse('{ field(a: true, c: false, e: 0) }')
    result = execute(schema, ast)
    assert result.data == {
        'field': '{"a":true,"c":false,"e":0}'
    }


def test_fails_when_an_is_type_of_check_is_not_met():
    class Special(object):

        def __init__(self, value):
            self.value = value

    class NotSpecial(object):

        def __init__(self, value):
            self.value = value

    SpecialType = GraphQLObjectType(
        'SpecialType',
        fields={
            'value': GraphQLField(GraphQLString),
        },
        is_type_of=lambda obj, context, info: isinstance(obj, Special)
    )

    schema = GraphQLSchema(
        GraphQLObjectType(
            name='Query',
            fields={
                'specials': GraphQLField(
                    GraphQLList(SpecialType),
                    resolver=lambda root, *_: root['specials']
                )
            }
        )
    )

    query = parse('{ specials { value } }')
    value = {
        'specials': [Special('foo'), NotSpecial('bar')]
    }

    result = execute(schema, query, value)

    assert result.data == {
        'specials': [
            {'value': 'foo'},
            None
        ]
    }

    assert 'Expected value of type "SpecialType" but got: NotSpecial.' in [str(e) for e in result.errors]


def test_fails_to_execute_a_query_containing_a_type_definition():
    query = parse('''
    { foo }

    type Query { foo: String }
    ''')

    schema = GraphQLSchema(
        GraphQLObjectType(
            name='Query',
            fields={
                'foo': GraphQLField(GraphQLString)
            }
        )
    )

    with raises(GraphQLError) as excinfo:
        execute(schema, query)

    assert excinfo.value.message == 'GraphQL cannot execute a request containing a ObjectTypeDefinition.'


def test_exceptions_are_reraised_if_specified(mocker):

    logger = mocker.patch('graphql.execution.executor.logger')

    query = parse('''
    { foo }
    ''')

    def resolver(*_):
        raise Exception("UH OH!")

    schema = GraphQLSchema(
        GraphQLObjectType(
            name='Query',
            fields={
                'foo': GraphQLField(GraphQLString, resolver=resolver)
            }
        )
    )

    execute(schema, query)
    logger.exception.assert_called_with("An error occurred while resolving field Query.foo")


def test_middleware():
    doc = '''{
        ok
        not_ok
    }'''

    class Data(object):

        def ok(self):
            return 'ok'

        def not_ok(self):
            return 'not_ok'

    doc_ast = parse(doc)

    Type = GraphQLObjectType('Type', {
        'ok': GraphQLField(GraphQLString),
        'not_ok': GraphQLField(GraphQLString),
    })

    def reversed_middleware(next, *args, **kwargs):
        p = next(*args, **kwargs)
        return p.then(lambda x: x[::-1])

    middlewares = MiddlewareManager(reversed_middleware)
    result = execute(GraphQLSchema(Type), doc_ast, Data(), middleware=middlewares)
    assert result.data == {'ok': 'ko', 'not_ok': 'ko_ton'}


def test_middleware_class():
    doc = '''{
        ok
        not_ok
    }'''

    class Data(object):

        def ok(self):
            return 'ok'

        def not_ok(self):
            return 'not_ok'

    doc_ast = parse(doc)

    Type = GraphQLObjectType('Type', {
        'ok': GraphQLField(GraphQLString),
        'not_ok': GraphQLField(GraphQLString),
    })

    class MyMiddleware(object):
        def resolve(self, next, *args, **kwargs):
            p = next(*args, **kwargs)
            return p.then(lambda x: x[::-1])

    middlewares = MiddlewareManager(MyMiddleware())
    result = execute(GraphQLSchema(Type), doc_ast, Data(), middleware=middlewares)
    assert result.data == {'ok': 'ko', 'not_ok': 'ko_ton'}
