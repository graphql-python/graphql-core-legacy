from graphql.execution.middleware import middleware_chain 
from graphql.execution.middleware import get_middleware_resolvers 
from graphql.language.parser import parse
from graphql.execution import MiddlewareManager, execute
from graphql.type import (GraphQLArgument, GraphQLBoolean, GraphQLField,
                          GraphQLInt, GraphQLList, GraphQLObjectType,
                          GraphQLSchema, GraphQLString, GraphQLNonNull, GraphQLID)
from promise import Promise


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
    result = execute(GraphQLSchema(Type), doc_ast,
                     Data(), middleware=middlewares)
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
    result = execute(GraphQLSchema(Type), doc_ast,
                     Data(), middleware=middlewares)
    assert result.data == {'ok': 'ko', 'not_ok': 'ko_ton'}


def test_middleware_skip_promise_wrap():
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

    class MyPromiseMiddleware(object):
        def resolve(self, next, *args, **kwargs):
            return Promise.resolve(next(*args, **kwargs))

    class MyEmptyMiddleware(object):
        def resolve(self, next, *args, **kwargs):
            return next(*args, **kwargs)

    middlewares_with_promise = MiddlewareManager(
        MyPromiseMiddleware(), wrap_in_promise=False)
    middlewares_without_promise = MiddlewareManager(
        MyEmptyMiddleware(), wrap_in_promise=False)

    result1 = execute(GraphQLSchema(Type), doc_ast, Data(),
                      middleware=middlewares_with_promise)
    result2 = execute(GraphQLSchema(Type), doc_ast, Data(),
                      middleware=middlewares_without_promise)
    assert result1.data == result2.data and result1.data == {
        'ok': 'ok', 'not_ok': 'not_ok'}


def test_middleware_chain(capsys):

    class CharPrintingMiddleware(object):
        def __init__(self, char):
            self.char = char

        def resolve(self, next, *args, **kwargs):
            print(f'resolve() called for middleware {self.char}')
            return next(*args, **kwargs).then(
                lambda x: print(f'then() for {self.char}')
            )

    middlewares = [
        CharPrintingMiddleware('a'),
        CharPrintingMiddleware('b'),
        CharPrintingMiddleware('c'),
    ]

    middlewares_resolvers = get_middleware_resolvers(middlewares)

    def func(): return

    chain_iter = middleware_chain(func, middlewares_resolvers)

    assert_stdout(capsys, "")

    chain_iter()

    expected_stdout = (
        'resolve() called for middleware c\n'
        'resolve() called for middleware b\n'
        'resolve() called for middleware a\n'
        'then() for a\n'
        'then() for b\n'
        'then() for c\n'
    )
    assert_stdout(capsys, expected_stdout)


def assert_stdout(capsys, expected_stdout):
    captured = capsys.readouterr()
    assert captured.out == expected_stdout