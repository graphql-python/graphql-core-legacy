from copy import deepcopy

from pytest import raises

from graphql import parse
from graphql.language import ast
from graphql.language.printer import print_ast

from .fixtures import SCHEMA_KITCHEN_SINK


def test_prints_minimal_ast():
    # type: () -> None
    node = ast.ScalarTypeDefinition(name=ast.Name("foo"))

    assert print_ast(node) == "scalar foo"


def test_print_produces_helpful_error_messages():
    # type: () -> None
    bad_ast = {"random": "Data"}
    with raises(AssertionError) as excinfo:
        print_ast(bad_ast)

    assert "Invalid AST Node: {'random': 'Data'}" in str(excinfo.value)


def test_does_not_alter_ast():
    # type: () -> None
    ast = parse(SCHEMA_KITCHEN_SINK)
    ast_copy = deepcopy(ast)
    print_ast(ast)
    assert ast == ast_copy


def test_prints_kitchen_sink():
    # type: () -> None
    ast = parse(SCHEMA_KITCHEN_SINK)
    printed = print_ast(ast)

    expected = '''schema {
  query: QueryType
  mutation: MutationType
}

"""
This is a description
of the `Foo` type.
"""
type Foo implements Bar {
  "Description of the `one` field."
  one: Type
  """
  This is a description of the `two` field.
  """
  two(
    """
    This is a description of the `argument` argument.
    """
    argument: InputType!
  ): Type
  """
  This is a description of the `three` field.
  """
  three(argument: InputType, other: String): Int
  four(argument: String = "string"): String
  five(argument: [String] = ["string", "string"]): String
  six(argument: InputType = {key: "value"}): Type
}

type AnnotatedObject @onObject(arg: "value") {
  annotatedField(arg: Type = "default" @onArg): Type @onField
}

interface Bar {
  one: Type
  four(argument: String = "string"): String
}

interface AnnotatedInterface @onInterface {
  annotatedField(arg: Type @onArg): Type @onField
}

union Feed = Story | Article | Advert

union AnnotatedUnion @onUnion = A | B

scalar CustomScalar

scalar AnnotatedScalar @onScalar

enum Site {
  """
  This is a description of the `DESKTOP` value
  """
  DESKTOP
  """
  This is a description of the `MOBILE` value
  """
  MOBILE
  "This is a description of the `WEB` value"
  WEB
}

enum AnnotatedEnum @onEnum {
  ANNOTATED_VALUE @onEnumValue
  OTHER_VALUE
}

input InputType {
  key: String!
  answer: Int = 42
}

input AnnotatedInput @onInputObjectType {
  annotatedField: Type @onField
}

extend type Foo {
  seven(argument: [String]): Type
}

extend type Foo @onType {}

type NoFields {}

"""
This is a description of the `@skip` directive
"""
directive @skip(if: Boolean!) on FIELD | FRAGMENT_SPREAD | INLINE_FRAGMENT

directive @include(if: Boolean!) on FIELD | FRAGMENT_SPREAD | INLINE_FRAGMENT
'''

    assert printed == expected
