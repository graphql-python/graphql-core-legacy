from graphql.core.language.location import SourceLocation
from graphql.core.validation.rules import ArgumentsOfCorrectType
from utils import expect_passes_rule, expect_fails_rule


def bad_value(arg_name, type_name, value, line, column):
    return {
        'message': ArgumentsOfCorrectType.bad_value_message(arg_name, type_name, value),
        'locations': [SourceLocation(line, column)]
    }


# noinspection PyMethodMayBeStatic
class TestValidValues(object):
    def test_good_int_value(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                intArgField(intArg: 2)
            }
        }
        ''')

    def test_good_boolean_value(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
              booleanArgField(booleanArg: true)
            }
        }
        ''')

    def test_good_string_value(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                stringArgField(stringArg: "foo")
            }
        }
        ''')

    def test_good_float_value(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                floatArgField(floatArg: 1.1)
            }
        }
        ''')

    def test_int_into_float(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                floatArgField(floatArg: 1)
            }
        }
        ''')

    def test_int_into_id(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
              idArgField(idArg: 1)
            }
        }
        ''')

    def test_string_into_id(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
              idArgField(idArg: "someIdString")
            }
        }
        ''')

    def test_good_enum_value(self):
        expect_passes_rule(ArgumentsOfCorrectType, '''
        {
            dog {
                doesKnowCommand(dogCommand: SIT)
            }
        }
        ''')


# noinspection PyMethodMayBeStatic
class TestInvalidStringValues(object):
    def test_int_into_string(self):
        expect_fails_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                stringArgField(stringArg: 1)
            }
        }
        ''', [
            bad_value('stringArg', 'String', '1', 4, 39)
        ])

    def test_float_into_string(self):
        expect_fails_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                stringArgField(stringArg: 1.0)
            }
        }
        ''', [
            bad_value('stringArg', 'String', '1.0', 4, 39)
        ])

    def test_bool_into_string(self):
        expect_fails_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                stringArgField(stringArg: true)
            }
        }
        ''', [
            bad_value('stringArg', 'String', 'true', 4, 39)
        ])

    def test_unquoted_string_into_string(self):
        expect_fails_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                stringArgField(stringArg: BAR)
            }
        }
        ''', [
            bad_value('stringArg', 'String', 'BAR', 4, 39)
        ])


# noinspection PyMethodMayBeStatic
class TestInvalidIntValues(object):
    def test_string_into_int(self):
        expect_fails_rule(ArgumentsOfCorrectType, '''
        {
            complicatedArgs {
                intArgField(intArg: "3")
            }
        }
        ''', [
            bad_value('intArg', 'Int', '"3"', 4, 33)
        ])


# noinspection PyMethodMayBeStatic
class TestInvalidFloatValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestInvalidBooleanValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestInvalidIDValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestInvalidEnumValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestValidListValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestInvalidListValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestValidNonNullableValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestInvalidNonNullableValues(object):
    pass


# noinspection PyMethodMayBeStatic
class TestValidInputObjectValue(object):
    pass


# noinspection PyMethodMayBeStatic
class TestInvalidInputObjectValue(object):
    pass


# noinspection PyMethodMayBeStatic
class TestDirectiveArguments(object):
    pass
