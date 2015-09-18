from graphql.core.language.location import SourceLocation
from graphql.core.validation.rules import NoUnusedVariables
from utils import expect_passes_rule, expect_fails_rule


def unused_variable(variable_name, line, column):
    return {
        'message': NoUnusedVariables.unused_variable_message(variable_name),
        'locations': [SourceLocation(line, column)]
    }


def test_uses_all_variables():
    expect_passes_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        field(a: $a, b: $b, c: $c)
      }
    ''')


def test_uses_all_variables_deeply():
    expect_passes_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        field(a: $a) {
          field(b: $b) {
            field(c: $c)
          }
        }
      }
    ''')


def test_uses_all_variables_deeply_in_inline_fragments():
    expect_passes_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        ... on Type {
          field(a: $a) {
            field(b: $b) {
              ... on Type {
                field(c: $c)
              }
            }
          }
        }
      }
    ''')


def test_uses_all_variables_in_fragment():
    expect_passes_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        ...FragA
      }
      fragment FragA on Type {
        field(a: $a) {
          ...FragB
        }
      }
      fragment FragB on Type {
        field(b: $b) {
          ...FragC
        }
      }
      fragment FragC on Type {
        field(c: $c)
      }
    ''')


def test_variable_used_by_fragment_in_multiple_operations():
    expect_passes_rule(NoUnusedVariables, '''
      query Foo($a: String) {
        ...FragA
      }
      query Bar($b: String) {
        ...FragB
      }
      fragment FragA on Type {
        field(a: $a)
      }
      fragment FragB on Type {
        field(b: $b)
      }
    ''')


def test_variable_used_by_recursive_fragment():
    expect_passes_rule(NoUnusedVariables, '''
      query Foo($a: String) {
        ...FragA
      }
      fragment FragA on Type {
        field(a: $a) {
          ...FragA
        }
      }
   ''')


def test_variable_not_used():
    expect_fails_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        field(a: $a, b: $b)
      }
    ''', [
        unused_variable('c', 2, 41)
    ])


def test_multiple_variables_not_used():
    expect_fails_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        field(b: $b)
      }
    ''', [
        unused_variable('a', 2, 17),
        unused_variable('c', 2, 41)
    ])


def test_variable_not_used_in_fragments():
    expect_fails_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        ...FragA
      }
      fragment FragA on Type {
        field(a: $a) {
          ...FragB
        }
      }
      fragment FragB on Type {
        field(b: $b) {
          ...FragC
        }
      }
      fragment FragC on Type {
        field
      }
    ''', [
        unused_variable('c', 2, 41)
    ])


def test_multiple_variables_not_used_in_fragments():
    expect_fails_rule(NoUnusedVariables, '''
      query Foo($a: String, $b: String, $c: String) {
        ...FragA
      }
      fragment FragA on Type {
        field {
          ...FragB
        }
      }
      fragment FragB on Type {
        field(b: $b) {
          ...FragC
        }
      }
      fragment FragC on Type {
        field
      }
    ''', [
        unused_variable('a', 2, 17),
        unused_variable('c', 2, 41)
    ])


def test_variable_not_used_by_unreferenced_fragment():
    expect_fails_rule(NoUnusedVariables, '''
      query Foo($b: String) {
        ...FragA
      }
      fragment FragA on Type {
        field(a: $a)
      }
      fragment FragB on Type {
        field(b: $b)
      }
    ''', [
        unused_variable('b', 2, 17),
    ])


def test_variable_not_used_by_fragment_used_by_other_operation():
    expect_fails_rule(NoUnusedVariables, '''
      query Foo($b: String) {
        ...FragA
      }
      query Bar($a: String) {
        ...FragB
      }
      fragment FragA on Type {
        field(a: $a)
      }
      fragment FragB on Type {
        field(b: $b)
      }
    ''', [
        unused_variable('b', 2, 17),
        unused_variable('a', 5, 17),
    ])
