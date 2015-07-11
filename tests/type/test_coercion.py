from graphql.type import (
    GraphQLInt,
    GraphQLFloat,
    GraphQLString,
    GraphQLBoolean,
)

def test_coerces_output_int():
    type = GraphQLInt()
    assert type.coerce(1) == 1
    assert type.coerce(0) == 0
    assert type.coerce(-1) == -1
    assert type.coerce(0.1) == 0
    assert type.coerce(1.1) == 1
    assert type.coerce(-1.1) == -1
    assert type.coerce(1e5) == 100000
    assert type.coerce(1e100) is None
    assert type.coerce(-1e100) is None
    assert type.coerce('-1.1') == -1
    assert type.coerce('one') is None
    assert type.coerce(False) == 0
    assert type.coerce(True) == 1


def test_coerces_output_float():
    type = GraphQLFloat()
    assert type.coerce(1) == 1.0
    assert type.coerce(0) == 0.0
    assert type.coerce(-1) == -1.0
    assert type.coerce(0.1) == 0.1
    assert type.coerce(1.1) == 1.1
    assert type.coerce(-1.1) == -1.1
    assert type.coerce('-1.1') == -1.1
    assert type.coerce('one') is None
    assert type.coerce(False) == 0
    assert type.coerce(True) == 1


def test_coerces_output_string():
    type = GraphQLString()
    assert type.coerce('string') == 'string'
    assert type.coerce(1) == '1'
    assert type.coerce(-1.1) == '-1.1'
    assert type.coerce(True) == 'true'
    assert type.coerce(False) == 'false'


def test_coerces_output_boolean():
    type = GraphQLBoolean()
    assert type.coerce('string') is True
    assert type.coerce('') is False
    assert type.coerce(1) is True
    assert type.coerce(0) is False
    assert type.coerce(True) is True
    assert type.coerce(False) is False
