from graphql.language.location import SourceLocation
from graphql.validation.rules import KnownDirectives

from .utils import expect_fails_rule, expect_passes_rule


def unknown_directive(directive_name, line, column):
    return {
        'message': KnownDirectives.unknown_directive_message(directive_name),
        'locations': [SourceLocation(line, column)]
    }


def misplaced_directive(directive_name, placement, line, column):
    return {
        'message': KnownDirectives.misplaced_directive_message(directive_name, placement),
        'locations': [SourceLocation(line, column)]
    }


def test_with_no_directives():
    expect_passes_rule(KnownDirectives, '''
      query Foo {
        name
        ...Frag
      }

      fragment Frag on Dog {
        name
      }
    ''')


def test_with_known_directives():
    expect_passes_rule(KnownDirectives, '''
      {
        dog @include(if: true) {
          name
        }
        human @skip(if: false) {
          name
        }
      }
    ''')


def test_with_unknown_directive():
    expect_fails_rule(KnownDirectives, '''
      {
        dog @unknown(directive: "value") {
          name
        }
      }
    ''', [
        unknown_directive('unknown', 3, 13)
    ])


def test_with_many_unknown_directives():
    expect_fails_rule(KnownDirectives, '''
      {
        dog @unknown(directive: "value") {
          name
        }
        human @unknown(directive: "value") {
          name
          pets @unknown(directive: "value") {
            name
          }
        }
      }
    ''', [
        unknown_directive('unknown', 3, 13),
        unknown_directive('unknown', 6, 15),
        unknown_directive('unknown', 8, 16)
    ])


def test_with_well_placed_directives():
    expect_passes_rule(KnownDirectives, '''
      query Foo {
        name @include(if: true)
        ...Frag @include(if: true)
        skippedField @skip(if: true)
        ...SkippedFrag @skip(if: true)
      }
    ''')


def test_with_misplaced_directives():
    expect_fails_rule(KnownDirectives, '''
      query Foo @include(if: true) {
        name @operationOnly
        ...Frag @operationOnly
      }
    ''', [
        misplaced_directive('include', 'QUERY', 2, 17),
        misplaced_directive('operationOnly', 'FIELD', 3, 14),
        misplaced_directive('operationOnly', 'FRAGMENT_SPREAD', 4, 17),

    ])
