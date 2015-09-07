import copy
from graphql.core.language.ast import Field, Name
from graphql.core.language.parser import parse
from graphql.core.language.printer import print_ast
from pytest import raises
from fixtures import KITCHEN_SINK


def test_does_not_alter_ast():
    ast = parse(KITCHEN_SINK)
    ast_copy = copy.deepcopy(ast)
    print_ast(ast)
    assert ast == ast_copy


def test_prints_minimal_ast():
    ast = Field(name=Name(loc=None, value='foo'),
                loc=None,
                alias=None,
                arguments=None,
                directives=None,
                selection_set=None)
    assert print_ast(ast) == 'foo'


def test_produces_helpful_error_messages():
    bad_ast = {'random': 'Data'}
    with raises(Exception) as excinfo:
        print_ast(bad_ast)
    assert 'Invalid AST Node' in str(excinfo.value)


def test_prints_kitchen_sink():
    ast = parse(KITCHEN_SINK)
    printed = print_ast(ast)
    assert printed == '''query queryName($foo: ComplexType, $site: Site = MOBILE) {
  whoever123is: node(id: [123, 456]) {
    id
    ... on User @defer {
      field2 {
        id
        alias: field1(first: 10, after: $foo) @include(if: $foo) {
          id
          ...frag
        }
      }
    }
  }
}

mutation likeStory {
  like(story: 123) @defer {
    story {
      id
    }
  }
}

fragment frag on Friend {
  foo(size: $size, bar: $b, obj: {key: "value"})
}

{
  unnamed(truthy: true, falsey: false)
  query
}
'''
