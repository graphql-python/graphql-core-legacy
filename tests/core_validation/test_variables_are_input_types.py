from graphql.core.language.location import SourceLocation
from graphql.core.validation.rules import VariablesAreInputTypes
from utils import expect_passes_rule, expect_fails_rule


def test_input_types_are_valid():
    expect_passes_rule(VariablesAreInputTypes, '''
      query Foo($a: String, $b: [Boolean!]!, $c: ComplexInput) {
        field(a: $a, b: $b, c: $c)
      }
    ''')


def test_output_types_are_invalid():
    expect_fails_rule(VariablesAreInputTypes, '''
      query Foo($a: Dog, $b: [[CatOrDog!]]!, $c: Pet) {
        field(a: $a, b: $b, c: $c)
      }
    ''', [
        {'locations': [SourceLocation(2, 21)],
         'message': VariablesAreInputTypes.message('a', 'Dog')},
        {'locations': [SourceLocation(2, 30)],
         'message': VariablesAreInputTypes.message('b', '[[CatOrDog!]]!')},
        {'locations': [SourceLocation(2, 50)],
         'message': VariablesAreInputTypes.message('c', 'Pet')},
    ])
