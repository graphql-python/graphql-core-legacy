from graphql.type import (
    GraphQLInt,
    GraphQLFloat,
    GraphQLString,
    GraphQLBoolean,
)

def test_coerces_output_int():
    assert GraphQLInt.coerce(1) == 1
    assert GraphQLInt.coerce(0) == 0
    assert GraphQLInt.coerce(-1) == -1
    assert GraphQLInt.coerce(0.1) == 0
    assert GraphQLInt.coerce(1.1) == 1
    assert GraphQLInt.coerce(-1.1) == -1
    assert GraphQLInt.coerce(1e5) == 100000
    assert GraphQLInt.coerce(1e100) is None
    assert GraphQLInt.coerce(-1e100) is None
    assert GraphQLInt.coerce('-1.1') == -1
    assert GraphQLInt.coerce('one') is None
    assert GraphQLInt.coerce(False) == 0
    assert GraphQLInt.coerce(True) == 1


def test_coerces_output_float():
    assert GraphQLFloat.coerce(1) == 1.0
    assert GraphQLFloat.coerce(0) == 0.0
    assert GraphQLFloat.coerce(-1) == -1.0
    assert GraphQLFloat.coerce(0.1) == 0.1
    assert GraphQLFloat.coerce(1.1) == 1.1
    assert GraphQLFloat.coerce(-1.1) == -1.1
    assert GraphQLFloat.coerce('-1.1') == -1.1
    assert GraphQLFloat.coerce('one') is None
    assert GraphQLFloat.coerce(False) == 0
    assert GraphQLFloat.coerce(True) == 1


def test_coerces_output_string():
    assert GraphQLString.coerce('string') == 'string'
    assert GraphQLString.coerce(1) == '1'
    assert GraphQLString.coerce(-1.1) == '-1.1'
    assert GraphQLString.coerce(True) == 'true'
    assert GraphQLString.coerce(False) == 'false'


def test_coerces_output_boolean():
    assert GraphQLBoolean.coerce('string') is True
    assert GraphQLBoolean.coerce('') is False
    assert GraphQLBoolean.coerce(1) is True
    assert GraphQLBoolean.coerce(0) is False
    assert GraphQLBoolean.coerce(True) is True
    assert GraphQLBoolean.coerce(False) is False
