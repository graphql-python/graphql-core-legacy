from graphql.core.language.location import SourceLocation
from graphql.core.validation.rules import ArgumentsOfCorrectType
from utils import expect_passes_rule, expect_fails_rule


def bad_value(arg_name, type_name, value, line, column):
    return {
        'message': ArgumentsOfCorrectType.bad_value_message(arg_name, type_name, value),
        'locations': [SourceLocation(line, column)]
    }


def test_good_int_value():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        complicatedArgs {
            intArgField(intArg: 2)
        }
    }
    ''')


def test_good_boolean_value():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        complicatedArgs {
          booleanArgField(booleanArg: true)
        }
    }
    ''')


def test_good_string_value():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        complicatedArgs {
            stringArgField(stringArg: "foo")
        }
    }
    ''')


def test_good_float_value():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        complicatedArgs {
            floatArgField(floatArg: 1.1)
        }
    }
    ''')


def test_int_into_float():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        complicatedArgs {
            floatArgField(floatArg: 1)
        }
    }
    ''')


def test_int_into_id():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        complicatedArgs {
          idArgField(idArg: 1)
        }
    }
    ''')


def test_string_into_id():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        complicatedArgs {
          idArgField(idArg: "someIdString")
        }
    }
    ''')


def test_good_enum_value():
    expect_passes_rule(ArgumentsOfCorrectType, '''
    {
        dog {
            doesKnowCommand(dogCommand: SIT)
        }
    }
    ''')

#
# def test_int_into_string():
#     expect_passes_rule(ArgumentsOfCorrectType, '''
#
#     ''')
