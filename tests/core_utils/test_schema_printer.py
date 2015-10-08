from collections import OrderedDict
from graphql.core.type.definition import GraphQLField, GraphQLArgument
from graphql.core.utils.schema_printer import print_schema, print_introspection_schema
from graphql.core.utils.is_nullish import is_nullish
from graphql.core.language.printer import print_ast
from graphql.core.type import (
    GraphQLSchema,
    GraphQLInputObjectType,
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLString,
    GraphQLInt,
    GraphQLBoolean,
    GraphQLList,
    GraphQLNonNull,
)


def print_for_test(schema):
    return '\n' + print_schema(schema)


def print_single_field_schema(field_config):
    Root = GraphQLObjectType(
        name='Root',
        fields={
            'singleField': field_config
        }
    )
    return print_for_test(GraphQLSchema(Root))


def test_prints_string_field():
    output = print_single_field_schema(GraphQLField(GraphQLString))
    assert output == '''
type Root {
  singleField: String
}
'''


def test_prints_list_string_field():
    output = print_single_field_schema(GraphQLField(GraphQLList(GraphQLString)))
    assert output == '''
type Root {
  singleField: [String]
}
'''


def test_prints_non_null_list_string_field():
    output = print_single_field_schema(GraphQLField(GraphQLNonNull(GraphQLList(GraphQLString))))
    assert output == '''
type Root {
  singleField: [String]!
}
'''


def test_prints_list_non_null_string_field():
    output = print_single_field_schema(GraphQLField((GraphQLList(GraphQLNonNull(GraphQLString)))))
    assert output == '''
type Root {
  singleField: [String!]
}
'''


def test_prints_non_null_list_non_null_string_field():
    output = print_single_field_schema(GraphQLField(GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLString)))))
    assert output == '''
type Root {
  singleField: [String!]!
}
'''


def test_prints_object_field():
    FooType = GraphQLObjectType(
        name='Foo',
        fields={
            'str': GraphQLField(GraphQLString)
        }
    )

    Root = GraphQLObjectType(
        name='Root',
        fields={
            'foo': GraphQLField(FooType)
        }
    )

    Schema = GraphQLSchema(Root)

    output = print_for_test(Schema)

    assert output == '''
type Foo {
  str: String
}

type Root {
  foo: Foo
}
'''


def test_prints_string_field_with_int_arg():
    output = print_single_field_schema(GraphQLField(
        type=GraphQLString,
        args={'argOne': GraphQLArgument(GraphQLInt)}
    ))
    assert output == '''
type Root {
  singleField(argOne: Int): String
}
'''


def test_prints_string_field_with_int_arg_with_default():
    output = print_single_field_schema(GraphQLField(
        type=GraphQLString,
        args={'argOne': GraphQLArgument(GraphQLInt, default_value=2)}
    ))
    assert output == '''
type Root {
  singleField(argOne: Int = 2): String
}
'''


def test_prints_string_field_with_non_null_int_arg():
    output = print_single_field_schema(GraphQLField(
        type=GraphQLString,
        args={'argOne': GraphQLArgument(GraphQLNonNull(GraphQLInt))}
    ))
    assert output == '''
type Root {
  singleField(argOne: Int!): String
}
'''


def test_prints_string_field_with_multiple_args():
    output = print_single_field_schema(GraphQLField(
        type=GraphQLString,
        args=OrderedDict([
            ('argOne', GraphQLArgument(GraphQLInt)),
            ('argTwo', GraphQLArgument(GraphQLString))
        ])
    ))

    assert output == '''
type Root {
  singleField(argOne: Int, argTwo: String): String
}
'''
