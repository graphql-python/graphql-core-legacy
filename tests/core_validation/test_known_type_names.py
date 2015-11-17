from graphql.core.language.location import SourceLocation
from graphql.core.validation.rules import KnownTypeNames
from utils import expect_passes_rule, expect_fails_rule


def unknown_type(type_name, line, column):
    return {
        'message': KnownTypeNames.unknown_type_message(type_name),
        'locations': [SourceLocation(line, column)]
    }


def test_known_type_names_are_valid():
    expect_passes_rule(KnownTypeNames, '''
      query Foo($var: String, $required: [String!]!) {
        user(id: 4) {
          pets { ... on Pet { name }, ...PetFields, ... { name } }
        }
      }
      fragment PetFields on Pet {
        name
      }
    ''')


def test_unknown_type_names_are_invalid():
    expect_fails_rule(KnownTypeNames, '''
      query Foo($var: JumbledUpLetters) {
        user(id: 4) {
          name
          pets { ... on Badger { name }, ...PetFields, ... { name } }
        }
      }
      fragment PetFields on Peettt {
        name
      }
    ''', [
        unknown_type('JumbledUpLetters', 2, 23),
        unknown_type('Badger', 5, 25),
        unknown_type('Peettt', 8, 29),
    ])
