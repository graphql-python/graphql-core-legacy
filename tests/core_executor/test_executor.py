from pytest import raises
from graphql.core.executor import execute
from graphql.core.language.parser import parse
from graphql.core.type import (GraphQLSchema, GraphQLObjectType, GraphQLField,
    GraphQLArgument, GraphQLList, GraphQLInt, GraphQLString)
from graphql.core.error import GraphQLError


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
        'promise': { 'a': 'Apple' },
        'deep': {
          'a': 'Already Been Done',
          'b': 'Boring',
          'c': [ 'Contrived', None, 'Confusing' ],
          'deeper': [
            { 'a': 'Apple', 'b': 'Banana' },
            None,
            { 'a': 'Apple', 'b': 'Banana' } ] }
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

    result = execute(schema, Data(), ast, 'Example', {'size': 100})
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
    result = execute(schema, None, ast)
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
                'c': 'Cherry' } }
        }


def test_threads_context_correctly():
    doc = 'query Example { a }'

    class Data(object):
        context_thing = 'thing'

    ast = parse(doc)

    def resolver(context, *_):
        assert context.context_thing == 'thing'
        resolver.got_here = True
    
    resolver.got_here = False

    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString, resolver=resolver)
    })

    result = execute(GraphQLSchema(Type), Data(), ast, 'Example', {})
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

    result = execute(GraphQLSchema(Type), None, doc_ast, 'Example', {})
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

    result = execute(GraphQLSchema(Type), Data(), doc_ast)
    assert result.data == {'ok': 'ok', 'error': None}
    assert len(result.errors) == 1
    assert result.errors[0].message == 'Error getting error'
    # TODO: check error location


def test_uses_the_inline_operation_if_no_operation_is_provided():
    doc = '{ a }'
    class Data(object):
        a = 'b'
    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Type), Data(), ast)
    assert not result.errors
    assert result.data == {'a': 'b'}


def test_uses_the_only_operation_if_no_operation_is_provided():
    doc = 'query Example { a }'
    class Data(object):
        a = 'b'
    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    result = execute(GraphQLSchema(Type), Data(), ast)
    assert not result.errors
    assert result.data == {'a': 'b'}


def test_raises_the_inline_operation_if_no_operation_is_provided():
    doc = 'query Example { a } query OtherExample { a }'
    class Data(object):
        a = 'b'
    ast = parse(doc)
    Type = GraphQLObjectType('Type', {
        'a': GraphQLField(GraphQLString)
    })
    with raises(GraphQLError) as excinfo:
        execute(GraphQLSchema(Type), Data(), ast)
    assert 'Must provide operation name if query contains multiple operations' in str(excinfo.value)


def test_uses_the_query_schema_for_queries():
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
    result = execute(GraphQLSchema(Q, M), Data(), ast, 'Q')
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
    result = execute(GraphQLSchema(Q, M), Data(), ast, 'M')
    assert not result.errors
    assert result.data == {'c': 'd'}


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
    result = execute(GraphQLSchema(Type), Data(), ast, 'Q')
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
    result = execute(GraphQLSchema(Q, M), None, ast)
    assert not result.errors
    assert result.data == {}
