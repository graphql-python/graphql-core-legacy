from graphql.language.parser import parse
from graphql.language.source import Source
from graphql.validation import validate

from .starwars_schema import StarWarsSchema


def validation_errors(query):
    source = Source(query, 'StarWars.graphql')
    ast = parse(source)
    return validate(StarWarsSchema, ast)


def test_nested_query_with_fragment():
    query = '''
        query NestedQueryWithFragment {
          hero {
            ...NameAndAppearances
            friends {
              ...NameAndAppearances
              friends {
                ...NameAndAppearances
              }
            }
          }
        }
        fragment NameAndAppearances on Character {
          name
          appearsIn
        }
    '''
    assert not validation_errors(query)


def test_non_existent_fields():
    query = '''
        query HeroSpaceshipQuery {
          hero {
            favoriteSpaceship
          }
        }
    '''
    assert validation_errors(query)


def test_require_fields_on_object():
    query = '''
        query HeroNoFieldsQuery {
          hero
        }
    '''
    assert validation_errors(query)


def test_disallows_fields_on_scalars():
    query = '''
        query HeroFieldsOnScalarQuery {
          hero {
            name {
              firstCharacterOfName
            }
          }
        }
    '''
    assert validation_errors(query)


def test_disallows_object_fields_on_interfaces():
    query = '''
        query DroidFieldOnCharacter {
          hero {
            name
            primaryFunction
          }
        }
    '''
    assert validation_errors(query)


def test_allows_object_fields_in_fragments():
    query = '''
        query DroidFieldInFragment {
          hero {
            name
            ...DroidFields
          }
        }
        fragment DroidFields on Droid {
          primaryFunction
        }
    '''
    assert not validation_errors(query)


def test_allows_object_fields_in_inline_fragments():
    query = '''
        query DroidFieldInFragment {
          hero {
            name
            ...DroidFields
          }
        }

        fragment DroidFields on Droid {
            primaryFunction
        }
    '''
    assert not validation_errors(query)
