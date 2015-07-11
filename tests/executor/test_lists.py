from graphql.executor.executor import execute
from graphql.language import parse
from graphql.type import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
)

def run(test_type, test_data):
    class Data(object):
        test = test_data

    class DataType(GraphQLObjectType):
        name = 'DataType'
        def get_fields(self):
            return {
                'test': GraphQLField(test_type),
                'nest': GraphQLField(DataType, resolver=lambda *_: Data())
            }

    schema = GraphQLSchema(DataType())
    ast = parse('{ nest { test } }')
    return execute(schema, Data(), ast)


def check(test_type, test_data, expected_data):
    result = run(test_type, test_data)
    assert not result.errors
    assert result.data == expected_data


# Execute: Handles list nullability

def test_nullable_list_of_nullables():
    type = GraphQLList(GraphQLInt) # [T]
    # Contains values
    check(type, [1, 2], {'nest': {'test': [1, 2]}})
    # Contains null
    check(type, [1, None, 2], {'nest': {'test': [1, None, 2]}})
    # Returns null
    check(type, None, {'nest': {'test': None}})


def test_non_nullable_list_of_nullables():
    type = GraphQLNonNull(GraphQLList(GraphQLInt)) # [T]!
    # Contains values
    check(type, [1, 2], {'nest': {'test': [1, 2]}})
    # Contains null
    check(type, [1, None, 2], {'nest': {'test': [1, None, 2]}})
    # Returns null
    result = run(type, None)
    assert len(result.errors) == 1
    assert result.errors[0].message == 'Cannot return null for non-nullable type.'
    # TODO: check error location
    assert result.data == {'nest': None}


def test_nullable_list_of_non_nullables():
    type = GraphQLList(GraphQLNonNull(GraphQLInt)) # [T!]
    # Contains values
    check(type, [1, 2], {'nest': {'test': [1, 2]}})
    # Contains null
    result = run(type, [1, None, 2])
    assert len(result.errors) == 1
    assert result.errors[0].message == 'Cannot return null for non-nullable type.'
    # TODO: check error location
    assert result.data == {'nest': {'test': None}}
    # Returns null
    check(type, None, {'nest': {'test': None}})


def test_non_nullable_list_of_non_nullables():
    type = GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLInt))) # [T!]!
    # Contains values
    check(type, [1, 2], {'nest': {'test': [1, 2]}})
    # Contains null
    result = run(type, [1, None, 2])
    assert len(result.errors) == 1
    assert result.errors[0].message == 'Cannot return null for non-nullable type.'
    # TODO: check error location
    assert result.data == {'nest': None}
    # Returns null
    result = run(type, None)
    assert len(result.errors) == 1
    assert result.errors[0].message == 'Cannot return null for non-nullable type.'
    # TODO: check error location
    assert result.data == {'nest': None}
