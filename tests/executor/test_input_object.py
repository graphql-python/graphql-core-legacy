import json
from graphql.executor.executor import execute
from graphql.language import parse
from graphql.type import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLArgument,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLString,
    GraphQLNonNull,
)

class TestInputObject(GraphQLInputObjectType):
    name = 'TestInputObject'
    fields = {
        'a': GraphQLField(GraphQLString()),
        'b': GraphQLField(GraphQLList(GraphQLString())),
        'c': GraphQLField(GraphQLNonNull(GraphQLString())),
    }


class TestType(GraphQLObjectType):
    name = 'TestType'
    fields = {
        'fieldWithObjectInput': GraphQLField(GraphQLString(),
            args={'input': GraphQLArgument(TestInputObject())},
            resolver=lambda obj, args, *_: json.dumps(args['input'])),
        'fieldWithNullableStringInput': GraphQLField(GraphQLString(),
            args={'input': GraphQLArgument(GraphQLString())},
            resolver=lambda obj, args, *_: json.dumps(args['input'])),
        'fieldWithNonNullableStringInput': GraphQLField(GraphQLString(),
            args={'input': GraphQLArgument(GraphQLNonNull(GraphQLString()))},
            resolver=lambda obj, args, *_: json.dumps(args['input'])),
        'list': GraphQLField(GraphQLString(),
            args={'input': GraphQLArgument(GraphQLList(GraphQLString()))},
            resolver=lambda obj, args, *_: json.dumps(args['input'])),
        'nnList': GraphQLField(GraphQLString(),
            args={'input': GraphQLArgument(
                GraphQLNonNull(GraphQLList(GraphQLString()))
            )},
            resolver=lambda obj, args, *_: json.dumps(args['input'])),
        'listNN': GraphQLField(GraphQLString(),
            args={'input': GraphQLArgument(
                GraphQLList(GraphQLNonNull(GraphQLString()))
            )},
            resolver=lambda obj, args, *_: json.dumps(args['input'])),
        'nnListNN': GraphQLField(GraphQLString(),
            args={'input': GraphQLArgument(
                GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLString())))
            )},
            resolver=lambda obj, args, *_: json.dumps(args['input'])),
    }

schema = GraphQLSchema(TestType())

# Handles objects and nullability

def test_inline_executes_with_complex_input():
    doc = '''
    {
      fieldWithObjectInput(input: {a: "foo", b: ["bar"], c: "baz"})
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert json.loads(result.data['fieldWithObjectInput']) == \
        {"a": "foo", "b": ["bar"], "c": "baz"}


def test_inline_properly_coerces_single_value_to_array():
    doc = '''
    {
        fieldWithObjectInput(input: {a: "foo", b: "bar", c: "baz"})
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert json.loads(result.data['fieldWithObjectInput']) == \
           {"a": "foo", "b": ["bar"], "c": "baz"}


def test_variable_executes_with_complex_input():
    doc = '''
    query q($input:TestInputObject) {
        fieldWithObjectInput(input: $input)
    }
    '''
    params = {'input': {'a': 'foo', 'b': ['bar'], 'c': 'baz'}}
    ast = parse(doc)
    result = execute(schema, None, ast, None, params)
    assert not result.errors
    assert json.loads(result.data['fieldWithObjectInput']) == \
           {"a": "foo", "b": ["bar"], "c": "baz"}


def test_variable_properly_coerces_single_value_to_array():
    doc = '''
    query q($input:TestInputObject) {
        fieldWithObjectInput(input: $input)
    }
    '''
    params = {'input': {'a': 'foo', 'b': 'bar', 'c': 'baz'}}
    ast = parse(doc)
    result = execute(schema, None, ast, None, params)
    assert not result.errors
    assert json.loads(result.data['fieldWithObjectInput']) == \
           {"a": "foo", "b": ["bar"], "c": "baz"}


def test_errors_on_null_for_nested_non_null():
    doc = '''
    query q($input:TestInputObject) {
        fieldWithObjectInput(input: $input)
    }
    '''
    params = {'input': {'a': 'foo', 'b': 'bar', 'c': None}}
    ast = parse(doc)
    result = execute(schema, None, ast, None, params)
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data


def test_errors_on_omission_of_nested_non_null():
    doc = '''
    query q($input:TestInputObject) {
        fieldWithObjectInput(input: $input)
    }
    '''
    params = {'input': {'a': 'foo', 'b': 'bar'}}
    ast = parse(doc)
    result = execute(schema, None, ast, None, params)
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data


# Handles nullable scalars

def test_allows_nullable_inputs_to_be_omitted():
    doc = '''
    {
        fieldWithNullableStringInput
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert result.data == \
           {"fieldWithNullableStringInput": "null"}


def test_allows_nullable_inputs_to_be_omitted_in_a_variable():
    doc = '''
    query SetsNullable($value: String) {
        fieldWithNullableStringInput(input: $value)
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert result.data == \
           {"fieldWithNullableStringInput": "null"}


def test_allows_nullable_inputs_to_be_omitted_in_an_unlisted_variable():
    doc = '''
    query SetsNullable {
        fieldWithNullableStringInput(input: $value)
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert result.data == \
           {"fieldWithNullableStringInput": "null"}


def test_allows_nullable_inputs_to_be_set_to_null_in_a_variable():
    doc = '''
    query SetsNullable($value: String) {
        fieldWithNullableStringInput(input: $value)
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'value': None})
    assert not result.errors
    assert result.data == \
           {"fieldWithNullableStringInput": "null"}


def test_allows_nullable_inputs_to_be_set_to_null_directly():
    doc = '''
    {
        fieldWithNullableStringInput(input: null)
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert result.data == \
           {"fieldWithNullableStringInput": "null"}


def test_allows_nullable_inputs_to_be_set_to_a_value_in_a_variable():
    doc = '''
    query SetsNullable($value: String) {
        fieldWithNullableStringInput(input: $value)
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'value': 'a'})
    assert not result.errors
    assert result.data == \
           {"fieldWithNullableStringInput": '"a"'}


def test_allows_nullable_inputs_to_be_set_to_a_value_directly():
    doc = '''
    {
        fieldWithNullableStringInput(input: "a")
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert result.data == \
           {"fieldWithNullableStringInput": '"a"'}


# Handles non-nullable scalars

def test_does_not_allow_non_nullable_inputs_to_be_omitted_in_a_variable():
    doc = '''
        query SetsNonNullable($value: String!) {
          fieldWithNonNullableStringInput(input: $value)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data


def test_does_not_allow_non_nullable_inputs_to_be_set_to_null_in_a_variable():
    doc = '''
        query SetsNonNullable($value: String!) {
          fieldWithNonNullableStringInput(input: $value)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'value': None})
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data


def test_allows_non_nullable_inputs_to_be_set_to_a_value_in_a_variable():
    doc = '''
        query SetsNonNullable($value: String!) {
          fieldWithNonNullableStringInput(input: $value)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'value': 'a'})
    assert not result.errors
    assert result.data == \
           {"fieldWithNonNullableStringInput": '"a"'}


def test_allows_non_nullable_inputs_to_be_set_to_a_value_directly():
    doc = '''
        {
          fieldWithNonNullableStringInput(input: "a")
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert result.data == \
           {"fieldWithNonNullableStringInput": '"a"'}


def test_passes_along_null_for_non_nullable_inputs_if_explicitly_set_in_the_query():
    doc = '''
    {
        fieldWithNonNullableStringInput
    }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast)
    assert not result.errors
    assert result.data == \
           {"fieldWithNonNullableStringInput": 'null'}


# Handles lists and nullability

def test_allows_lists_to_be_null():
    doc = '''
        query q($input:[String]) {
          list(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': None})
    assert not result.errors
    assert result.data == {'list': 'null'}


def test_allows_lists_to_contain_values():
    doc = '''
        query q($input:[String]) {
          list(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A']})
    assert not result.errors
    assert result.data == {'list': '["A"]'}


def test_allows_lists_to_contain_null():
    doc = '''
        query q($input:[String]) {
          list(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A', None, 'B']})
    assert not result.errors
    assert result.data == {'list': '["A", null, "B"]'}


def test_does_not_allow_non_null_lists_to_be_null():
    doc = '''
        query q($input:[String]!) {
          nnList(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': None})
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data


def test_allows_non_null_lists_to_contain_values():
    doc = '''
        query q($input:[String]!) {
          nnList(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A']})
    assert not result.errors
    assert result.data == {'nnList': '["A"]'}


def test_allows_non_null_lists_to_contain_null():
    doc = '''
        query q($input:[String]!) {
          nnList(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A', None, 'B']})
    assert not result.errors
    assert result.data == {'nnList': '["A", null, "B"]'}


def test_allows_lists_of_non_nulls_to_be_null():
    doc = '''
        query q($input:[String!]) {
          listNN(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': None})
    assert not result.errors
    assert result.data == {'listNN': 'null'}


def test_allows_lists_of_non_nulls_to_contain_values():
    doc = '''
        query q($input:[String!]) {
          listNN(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A']})
    assert not result.errors
    assert result.data == {'listNN': '["A"]'}


def test_does_not_allow_lists_of_non_nulls_to_contain_null():
    doc = '''
        query q($input:[String!]) {
          listNN(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A', None, 'B']})
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data


def test_does_not_allow_non_null_lists_of_non_nulls_to_be_null():
    doc = '''
        query q($input:[String!]!) {
          nnListNN(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': None})
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data


def test_allows_non_null_lists_of_non_nulls_to_contain_values():
    doc = '''
        query q($input:[String!]!) {
          nnListNN(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A']})
    assert not result.errors
    assert result.data == {'nnListNN': '["A"]'}


def test_does_not_allow_non_null_lists_of_non_nulls_to_contain_null():
    doc = '''
        query q($input:[String!]!) {
          nnListNN(input: $input)
        }
    '''
    ast = parse(doc)
    result = execute(schema, None, ast, None, {'input': ['A', None, 'B']})
    assert len(result.errors) == 1
    # TODO: check error message and location
    assert not result.data
