from graphql.core.language.location import SourceLocation
from graphql.core.validation.rules import FieldsOnCorrectType
from utils import expect_passes_rule, expect_fails_rule


def error(field, type, line, column):
    return {
        'message': FieldsOnCorrectType.message(field, type),
        'locations': [SourceLocation(line, column)]
    }


def test_object_field_selection():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment objectFieldSelection on Dog {
        __typename
        name
      }
    ''')


def test_aliased_object_field_selection():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment aliasedObjectFieldSelection on Dog {
        tn : __typename
        otherName : name
      }
    ''')


def test_interface_field_selection():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment interfaceFieldSelection on Pet {
        __typename
        name
      }
    ''')


def test_aliased_interface_field_selection():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment interfaceFieldSelection on Pet {
        otherName : name
      }
    ''')


def test_lying_alias_selection():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment lyingAliasSelection on Dog {
        name : nickname
      }
    ''')


def test_ignores_fields_on_unknown_type():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment unknownSelection on UnknownType {
        unknownField
      }
    ''')


def test_field_not_defined_on_fragment():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment fieldNotDefined on Dog {
        meowVolume
      }
    ''', [error('meowVolume', 'Dog', 3, 9)])


def test_field_not_defined_deeply_only_reports_first():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment deepFieldNotDefined on Dog {
        unknown_field {
          deeper_unknown_field
        }
      }
    ''', [error('unknown_field', 'Dog', 3, 9)])


def test_sub_field_not_defined():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment subFieldNotDefined on Human {
        pets {
          unknown_field
        }
      }
    ''', [error('unknown_field', 'Pet', 4, 11)])


def test_field_not_defined_on_inline_fragment():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment fieldNotDefined on Pet {
        ... on Dog {
          meowVolume
        }
      }
    ''', [error('meowVolume', 'Dog', 4, 11)])


def test_aliased_field_target_not_defined():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment aliasedFieldTargetNotDefined on Dog {
        volume : mooVolume
      }
    ''', [error('mooVolume', 'Dog', 3, 9)])


def test_aliased_lying_field_target_not_defined():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment aliasedLyingFieldTargetNotDefined on Dog {
        barkVolume : kawVolume
      }
    ''', [error('kawVolume', 'Dog', 3, 9)])


def test_not_defined_on_interface():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment notDefinedOnInterface on Pet {
        tailLength
      }
    ''', [error('tailLength', 'Pet', 3, 9)])


def test_defined_on_implementors_but_not_on_interface():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment definedOnImplementorsButNotInterface on Pet {
        nickname
      }
    ''', [error('nickname', 'Pet', 3, 9)])


def test_meta_field_selection_on_union():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment directFieldSelectionOnUnion on CatOrDog {
        __typename
      }
    ''')


def test_direct_field_selection_on_union():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment directFieldSelectionOnUnion on CatOrDog {
        directField
      }
    ''', [error('directField', 'CatOrDog', 3, 9)])


def test_defined_on_implementors_queried_on_union():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment definedOnImplementorsQueriedOnUnion on CatOrDog {
        name
      }
    ''', [error('name', 'CatOrDog', 3, 9)])


def test_valid_field_in_inline_fragment():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment objectFieldSelection on Pet {
        ... on Dog {
          name
        }
      }
    ''')
