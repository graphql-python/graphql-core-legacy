from graphql.language.location import SourceLocation
from graphql.validation.rules import FieldsOnCorrectType

from .utils import expect_fails_rule, expect_passes_rule


def undefined_field(field, type, suggestions, line, column):
    return {
        'message': FieldsOnCorrectType.undefined_field_message(field, type, suggestions),
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


def test_reports_errors_when_type_is_known_again():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment typeKnownAgain on Pet {
        unknown_pet_field {
          ... on Cat {
            unknown_cat_field
          }
        }
      },
    ''', [
        undefined_field('unknown_pet_field', 'Pet', [], 3, 9),
        undefined_field('unknown_cat_field', 'Cat', [], 5, 13)
    ])


def test_field_not_defined_on_fragment():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment fieldNotDefined on Dog {
        meowVolume
      }
    ''', [
        undefined_field('meowVolume', 'Dog', [], 3, 9)
    ])


def test_ignores_deeply_unknown_field():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment deepFieldNotDefined on Dog {
        unknown_field {
          deeper_unknown_field
        }
      }
    ''', [
        undefined_field('unknown_field', 'Dog', [], 3, 9)
    ])


def test_sub_field_not_defined():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment subFieldNotDefined on Human {
        pets {
          unknown_field
        }
      }
    ''', [
        undefined_field('unknown_field', 'Pet', [], 4, 11)
    ])


def test_field_not_defined_on_inline_fragment():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment fieldNotDefined on Pet {
        ... on Dog {
          meowVolume
        }
      }
    ''', [
        undefined_field('meowVolume', 'Dog', [], 4, 11)
    ])


def test_aliased_field_target_not_defined():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment aliasedFieldTargetNotDefined on Dog {
        volume : mooVolume
      }
    ''', [
        undefined_field('mooVolume', 'Dog', [], 3, 9)
    ])


def test_aliased_lying_field_target_not_defined():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment aliasedLyingFieldTargetNotDefined on Dog {
        barkVolume : kawVolume
      }
    ''', [
        undefined_field('kawVolume', 'Dog', [], 3, 9)
    ])


def test_not_defined_on_interface():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment notDefinedOnInterface on Pet {
        tailLength
      }
    ''', [
        undefined_field('tailLength', 'Pet', [], 3, 9)
    ])


def test_defined_on_implementors_but_not_on_interface():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment definedOnImplementorsButNotInterface on Pet {
        nickname
      }
    ''', [
        undefined_field('nickname', 'Pet', ['Cat', 'Dog'], 3, 9)
    ])


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
    ''', [
        undefined_field('directField', 'CatOrDog', [], 3, 9)
    ])


def test_defined_on_implementors_queried_on_union():
    expect_fails_rule(FieldsOnCorrectType, '''
      fragment definedOnImplementorsQueriedOnUnion on CatOrDog {
        name
      }
    ''', [
        undefined_field(
            'name',
            'CatOrDog',
            ['Being', 'Pet', 'Canine', 'Cat', 'Dog'],
            3,
            9
        )
    ])


def test_valid_field_in_inline_fragment():
    expect_passes_rule(FieldsOnCorrectType, '''
      fragment objectFieldSelection on Pet {
        ... on Dog {
          name
        }
        ... {
          name
        }
      }
    ''')


def test_fields_correct_type_no_suggestion():
    message = FieldsOnCorrectType.undefined_field_message('T', 'f', [])
    assert message == 'Cannot query field "T" on type "f".'


def test_fields_correct_type_no_small_number_suggestions():
    message = FieldsOnCorrectType.undefined_field_message('T', 'f', ['A', 'B'])
    assert message == (
        'Cannot query field "T" on type "f". ' +
        'However, this field exists on "A", "B". ' +
        'Perhaps you meant to use an inline fragment?'
    )


def test_fields_correct_type_lot_suggestions():
    message = FieldsOnCorrectType.undefined_field_message('T', 'f', ['A', 'B', 'C', 'D', 'E', 'F'])
    assert message == (
        'Cannot query field "T" on type "f". ' +
        'However, this field exists on "A", "B", "C", "D", "E", ' +
        'and 1 other types. ' +
        'Perhaps you meant to use an inline fragment?'
    )
