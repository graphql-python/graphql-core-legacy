import pytest

from graphql.type import (GraphQLBoolean, GraphQLFloat, GraphQLInt,
                          GraphQLString)


def test_serializes_output_int():
    assert GraphQLInt.serialize(1) == 1
    assert GraphQLInt.serialize(0) == 0
    assert GraphQLInt.serialize(-1) == -1
    assert GraphQLInt.serialize(0.1) == 0
    assert GraphQLInt.serialize(1.1) == 1
    assert GraphQLInt.serialize(-1.1) == -1
    assert GraphQLInt.serialize(1e5) == 100000
    with pytest.raises(Exception):
        GraphQLInt.serialize(9876504321)
    with pytest.raises(Exception):
        GraphQLInt.serialize(-9876504321)
    with pytest.raises(Exception):
        GraphQLInt.serialize(1e100)
    with pytest.raises(Exception):
        GraphQLInt.serialize(-1e100)
    assert GraphQLInt.serialize('-1.1') == -1
    with pytest.raises(Exception):
        GraphQLInt.serialize('one')
    assert GraphQLInt.serialize(False) == 0
    assert GraphQLInt.serialize(True) == 1


def test_serializes_output_float():
    assert GraphQLFloat.serialize(1) == 1.0
    assert GraphQLFloat.serialize(0) == 0.0
    assert GraphQLFloat.serialize(-1) == -1.0
    assert GraphQLFloat.serialize(0.1) == 0.1
    assert GraphQLFloat.serialize(1.1) == 1.1
    assert GraphQLFloat.serialize(-1.1) == -1.1
    assert GraphQLFloat.serialize('-1.1') == -1.1
    with pytest.raises(Exception):
        GraphQLFloat.serialize('one')
    assert GraphQLFloat.serialize(False) == 0
    assert GraphQLFloat.serialize(True) == 1


def test_serializes_output_string():
    assert GraphQLString.serialize('string') == 'string'
    assert GraphQLString.serialize(1) == '1'
    assert GraphQLString.serialize(-1.1) == '-1.1'
    assert GraphQLString.serialize(True) == 'true'
    assert GraphQLString.serialize(False) == 'false'
    assert GraphQLString.serialize(u'\U0001F601') == u'\U0001F601'


def test_serializes_output_boolean():
    assert GraphQLBoolean.serialize('string') is True
    assert GraphQLBoolean.serialize('') is False
    assert GraphQLBoolean.serialize(1) is True
    assert GraphQLBoolean.serialize(0) is False
    assert GraphQLBoolean.serialize(True) is True
    assert GraphQLBoolean.serialize(False) is False
