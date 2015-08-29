from pytest import raises
from graphql.core.language.error import LanguageError
from graphql.core.language.source import Source
from graphql.core.language.parser import parse
from graphql.core.language import ast

KITCHEN_SINK = """
# Copyright (c) 2015, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

query queryName($foo: ComplexType, $site: Site = MOBILE) {
  whoever123is: node(id: [123, 456]) {
    id ,
    ... on User @defer {
      field2 {
        id ,
        alias: field1(first:10, after:$foo,) @include(if: $foo) {
          id,
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
  unnamed(truthy: true, falsey: false),
  query
}
"""


def test_parse_provides_useful_errors():
    with raises(LanguageError) as excinfo:
        parse("""{ ...MissingOn }
fragment MissingOn Type
""")
    assert 'Syntax Error GraphQL (2:20) Expected "on", found Name "Type"' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        parse('{ field: {} }')
    assert 'Syntax Error GraphQL (1:10) Expected Name, found {' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        parse('notanoperation Foo { field }')
    assert 'Syntax Error GraphQL (1:1) Unexpected Name "notanoperation"' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        parse('...')
    assert 'Syntax Error GraphQL (1:1) Unexpected ...' in str(excinfo.value)


def test_parse_provides_useful_error_when_using_source():
    with raises(LanguageError) as excinfo:
        parse(Source('query', 'MyQuery.graphql'))
    assert 'Syntax Error MyQuery.graphql (1:6) Expected Name, found EOF' in str(excinfo.value)


def test_parses_variable_inline_values():
    parse('{ field(complex: { a: { b: [ $var ] } }) }')


def test_parses_constant_default_values():
    with raises(LanguageError) as excinfo:
        parse('query Foo($x: Complex = { a: { b: [ $var ] } }) { field }')
    assert 'Syntax Error GraphQL (1:37) Unexpected $' in str(excinfo.value)


def test_duplicate_keys_in_input_object_is_syntax_error():
    with raises(LanguageError) as excinfo:
        parse('{ field(arg: { a: 1, a: 2 }) }')
    assert 'Syntax Error GraphQL (1:22) Duplicate input object field a.' in str(excinfo.value)


def test_parses_kitchen_sink():
    parse(KITCHEN_SINK)


def test_parse_creates_ast():
    source = Source("""{
  node(id: 4) {
    id,
    name
  }
}
""")
    result = parse(source)

    assert result == \
           ast.Document(
               loc={'start': 0, 'end': 41, 'source': source},
               definitions=
               [ast.OperationDefinition(
                   loc={'start': 0, 'end': 40, 'source': source},
                   operation='query',
                   name=None,
                   variable_definitions=None,
                   directives=[],
                   selection_set=ast.SelectionSet(
                       loc={'start': 0, 'end': 40, 'source': source},
                       selections=
                       [ast.Field(
                           loc={'start': 4, 'end': 38, 'source': source},
                           alias=None,
                           name=ast.Name(
                               loc={'start': 4, 'end': 8, 'source': source},
                               value='node'),
                           arguments=[ast.Argument(
                               name=ast.Name(loc={'start': 9, 'end': 11, 'source': source},
                                             value='id'),
                               value=ast.IntValue(
                                   loc={'start': 13, 'end': 14, 'source': source},
                                   value='4'),
                               loc={'start': 9, 'end': 14, 'source': source})],
                           directives=[],
                           selection_set=ast.SelectionSet(
                               loc={'start': 16, 'end': 38, 'source': source},
                               selections=
                               [ast.Field(
                                   loc={'start': 22, 'end': 24, 'source': source},
                                   alias=None,
                                   name=ast.Name(
                                       loc={'start': 22, 'end': 24, 'source': source},
                                       value='id'),
                                   arguments=[],
                                   directives=[],
                                   selection_set=None),
                                ast.Field(
                                    loc={'start': 30, 'end': 34, 'source': source},
                                    alias=None,
                                    name=ast.Name(
                                        loc={'start': 30, 'end': 34, 'source': source},
                                        value='name'),
                                    arguments=[],
                                    directives=[],
                                    selection_set=None)]))]))])
