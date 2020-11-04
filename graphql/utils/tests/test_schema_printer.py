from collections import OrderedDict

from graphql.type import (
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)
from graphql.type.definition import (
    GraphQLArgument,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputObjectField,
)
from graphql.utils.schema_printer import print_introspection_schema, print_schema


def print_for_test(schema):
    return "\n" + print_schema(schema)


def print_single_field_schema(field_config):
    Root = GraphQLObjectType(name="Root", fields={"singleField": field_config})
    return print_for_test(GraphQLSchema(Root))


def test_prints_string_field():
    output = print_single_field_schema(GraphQLField(GraphQLString))
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField: String
}
"""
    )


def test_prints_list_string_field():
    output = print_single_field_schema(GraphQLField(GraphQLList(GraphQLString)))
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField: [String]
}
"""
    )


def test_prints_non_null_list_string_field():
    output = print_single_field_schema(
        GraphQLField(GraphQLNonNull(GraphQLList(GraphQLString)))
    )
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField: [String]!
}
"""
    )


def test_prints_list_non_null_string_field():
    output = print_single_field_schema(
        GraphQLField(GraphQLList(GraphQLNonNull(GraphQLString)))
    )
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField: [String!]
}
"""
    )


def test_prints_non_null_list_non_null_string_field():
    output = print_single_field_schema(
        GraphQLField(GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLString))))
    )
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField: [String!]!
}
"""
    )


def test_prints_object_field():
    FooType = GraphQLObjectType(name="Foo", fields={"str": GraphQLField(GraphQLString)})

    Root = GraphQLObjectType(name="Root", fields={"foo": GraphQLField(FooType)})

    Schema = GraphQLSchema(Root)

    output = print_for_test(Schema)

    assert (
        output
        == """
schema {
  query: Root
}

type Foo {
  str: String
}

type Root {
  foo: Foo
}
"""
    )


def test_prints_string_field_with_int_arg():
    output = print_single_field_schema(
        GraphQLField(type_=GraphQLString, args={"argOne": GraphQLArgument(GraphQLInt)})
    )
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField(argOne: Int): String
}
"""
    )


def test_prints_string_field_with_int_arg_with_default():
    output = print_single_field_schema(
        GraphQLField(
            type_=GraphQLString,
            args={"argOne": GraphQLArgument(GraphQLInt, default_value=2)},
        )
    )
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField(argOne: Int = 2): String
}
"""
    )


def test_prints_string_field_with_non_null_int_arg():
    output = print_single_field_schema(
        GraphQLField(
            type_=GraphQLString,
            args={"argOne": GraphQLArgument(GraphQLNonNull(GraphQLInt))},
        )
    )
    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField(argOne: Int!): String
}
"""
    )


def test_prints_string_field_with_multiple_args():
    output = print_single_field_schema(
        GraphQLField(
            type_=GraphQLString,
            args=OrderedDict(
                [
                    ("argOne", GraphQLArgument(GraphQLInt)),
                    ("argTwo", GraphQLArgument(GraphQLString)),
                ]
            ),
        )
    )

    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField(argOne: Int, argTwo: String): String
}
"""
    )


def test_prints_string_field_with_multiple_args_first_is_default():
    output = print_single_field_schema(
        GraphQLField(
            type_=GraphQLString,
            args=OrderedDict(
                [
                    ("argOne", GraphQLArgument(GraphQLInt, default_value=1)),
                    ("argTwo", GraphQLArgument(GraphQLString)),
                    ("argThree", GraphQLArgument(GraphQLBoolean)),
                ]
            ),
        )
    )

    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField(argOne: Int = 1, argTwo: String, argThree: Boolean): String
}
"""
    )


def test_prints_string_field_with_multiple_args_second_is_default():
    output = print_single_field_schema(
        GraphQLField(
            type_=GraphQLString,
            args=OrderedDict(
                [
                    ("argOne", GraphQLArgument(GraphQLInt)),
                    ("argTwo", GraphQLArgument(GraphQLString, default_value="foo")),
                    ("argThree", GraphQLArgument(GraphQLBoolean)),
                ]
            ),
        )
    )

    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField(argOne: Int, argTwo: String = "foo", argThree: Boolean): String
}
"""
    )


def test_prints_string_field_with_multiple_args_last_is_default():
    output = print_single_field_schema(
        GraphQLField(
            type_=GraphQLString,
            args=OrderedDict(
                [
                    ("argOne", GraphQLArgument(GraphQLInt)),
                    ("argTwo", GraphQLArgument(GraphQLString)),
                    ("argThree", GraphQLArgument(GraphQLBoolean, default_value=False)),
                ]
            ),
        )
    )

    assert (
        output
        == """
schema {
  query: Root
}

type Root {
  singleField(argOne: Int, argTwo: String, argThree: Boolean = false): String
}
"""
    )


def test_prints_interface():
    FooType = GraphQLInterfaceType(
        name="Foo",
        resolve_type=lambda *_: None,
        fields={"str": GraphQLField(GraphQLString)},
    )

    BarType = GraphQLObjectType(
        name="Bar", fields={"str": GraphQLField(GraphQLString)}, interfaces=[FooType]
    )

    Root = GraphQLObjectType(name="Root", fields={"bar": GraphQLField(BarType)})

    Schema = GraphQLSchema(Root, types=[BarType])
    output = print_for_test(Schema)

    assert (
        output
        == """
schema {
  query: Root
}

type Bar implements Foo {
  str: String
}

interface Foo {
  str: String
}

type Root {
  bar: Bar
}
"""
    )


def test_prints_multiple_interfaces():
    FooType = GraphQLInterfaceType(
        name="Foo",
        resolve_type=lambda *_: None,
        fields={"str": GraphQLField(GraphQLString)},
    )
    BaazType = GraphQLInterfaceType(
        name="Baaz",
        resolve_type=lambda *_: None,
        fields={"int": GraphQLField(GraphQLInt)},
    )

    BarType = GraphQLObjectType(
        name="Bar",
        fields=OrderedDict(
            [("str", GraphQLField(GraphQLString)), ("int", GraphQLField(GraphQLInt))]
        ),
        interfaces=[FooType, BaazType],
    )

    Root = GraphQLObjectType(name="Root", fields={"bar": GraphQLField(BarType)})

    Schema = GraphQLSchema(Root, types=[BarType])
    output = print_for_test(Schema)

    assert (
        output
        == """
schema {
  query: Root
}

interface Baaz {
  int: Int
}

type Bar implements Foo, Baaz {
  str: String
  int: Int
}

interface Foo {
  str: String
}

type Root {
  bar: Bar
}
"""
    )


def test_prints_unions():
    FooType = GraphQLObjectType(
        name="Foo", fields={"bool": GraphQLField(GraphQLBoolean)}
    )

    BarType = GraphQLObjectType(name="Bar", fields={"str": GraphQLField(GraphQLString)})

    SingleUnion = GraphQLUnionType(
        name="SingleUnion", resolve_type=lambda *_: None, types=[FooType]
    )

    MultipleUnion = GraphQLUnionType(
        name="MultipleUnion", resolve_type=lambda *_: None, types=[FooType, BarType]
    )

    Root = GraphQLObjectType(
        name="Root",
        fields=OrderedDict(
            [
                ("single", GraphQLField(SingleUnion)),
                ("multiple", GraphQLField(MultipleUnion)),
            ]
        ),
    )

    Schema = GraphQLSchema(Root)
    output = print_for_test(Schema)

    assert (
        output
        == """
schema {
  query: Root
}

type Bar {
  str: String
}

type Foo {
  bool: Boolean
}

union MultipleUnion = Foo | Bar

type Root {
  single: SingleUnion
  multiple: MultipleUnion
}

union SingleUnion = Foo
"""
    )


def test_prints_input_type():
    InputType = GraphQLInputObjectType(
        name="InputType", fields={"int": GraphQLInputObjectField(GraphQLInt)}
    )

    Root = GraphQLObjectType(
        name="Root",
        fields={
            "str": GraphQLField(
                GraphQLString, args={"argOne": GraphQLArgument(InputType)}
            )
        },
    )

    Schema = GraphQLSchema(Root)
    output = print_for_test(Schema)

    assert (
        output
        == """
schema {
  query: Root
}

input InputType {
  int: Int
}

type Root {
  str(argOne: InputType): String
}
"""
    )


def test_prints_custom_scalar():
    OddType = GraphQLScalarType(
        name="Odd", serialize=lambda v: v if v % 2 == 1 else None
    )

    Root = GraphQLObjectType(name="Root", fields={"odd": GraphQLField(OddType)})

    Schema = GraphQLSchema(Root)
    output = print_for_test(Schema)

    assert (
        output
        == """
schema {
  query: Root
}

scalar Odd

type Root {
  odd: Odd
}
"""
    )


def test_print_enum():
    RGBType = GraphQLEnumType(
        name="RGB",
        values=OrderedDict(
            [
                ("RED", GraphQLEnumValue(0)),
                ("GREEN", GraphQLEnumValue(1)),
                ("BLUE", GraphQLEnumValue(2)),
            ]
        ),
    )

    Root = GraphQLObjectType(name="Root", fields={"rgb": GraphQLField(RGBType)})

    Schema = GraphQLSchema(Root)
    output = print_for_test(Schema)

    assert (
        output
        == """
schema {
  query: Root
}

enum RGB {
  RED
  GREEN
  BLUE
}

type Root {
  rgb: RGB
}
"""
    )


def test_print_introspection_schema():
    Root = GraphQLObjectType(
        name="Root", fields={"onlyField": GraphQLField(GraphQLString)}
    )

    Schema = GraphQLSchema(Root)
    output = "\n" + print_introspection_schema(Schema)

    assert (
        output
        == '''
schema {
  query: Root
}

"""
Directs the executor to include this field or fragment only when the `if` argument is true.
"""
directive @include(
  """Included when true."""
  if: Boolean!
) on FIELD | FRAGMENT_SPREAD | INLINE_FRAGMENT

"""
Directs the executor to skip this field or fragment when the `if` argument is true.
"""
directive @skip(
  """Skipped when true."""
  if: Boolean!
) on FIELD | FRAGMENT_SPREAD | INLINE_FRAGMENT

"""Marks an element of a GraphQL schema as no longer supported."""
directive @deprecated(
  """
  Explains why this element was deprecated, usually also including a suggestion
  for how to access supported similar data. Formatted in
  [Markdown](https://daringfireball.net/projects/markdown/).
  """
  reason: String = "No longer supported"
) on FIELD_DEFINITION | ENUM_VALUE

"""
A Directive provides a way to describe alternate runtime execution and type validation behavior in a GraphQL document.

In some cases, you need to provide options to alter GraphQL's execution behavior
in ways field arguments will not suffice, such as conditionally including or
skipping a field. Directives provide this by describing additional information
to the executor.
"""
type __Directive {
  name: String!
  description: String
  locations: [__DirectiveLocation!]!
  args: [__InputValue!]!
  onOperation: Boolean! @deprecated(reason: "Use `locations`.")
  onFragment: Boolean! @deprecated(reason: "Use `locations`.")
  onField: Boolean! @deprecated(reason: "Use `locations`.")
}

"""
A Directive can be adjacent to many parts of the GraphQL language, a
__DirectiveLocation describes one such possible adjacencies.
"""
enum __DirectiveLocation {
  """Location adjacent to a query operation."""
  QUERY

  """Location adjacent to a mutation operation."""
  MUTATION

  """Location adjacent to a subscription operation."""
  SUBSCRIPTION

  """Location adjacent to a field."""
  FIELD

  """Location adjacent to a fragment definition."""
  FRAGMENT_DEFINITION

  """Location adjacent to a fragment spread."""
  FRAGMENT_SPREAD

  """Location adjacent to an inline fragment."""
  INLINE_FRAGMENT

  """Location adjacent to a schema definition."""
  SCHEMA

  """Location adjacent to a scalar definition."""
  SCALAR

  """Location adjacent to an object definition."""
  OBJECT

  """Location adjacent to a field definition."""
  FIELD_DEFINITION

  """Location adjacent to an argument definition."""
  ARGUMENT_DEFINITION

  """Location adjacent to an interface definition."""
  INTERFACE

  """Location adjacent to a union definition."""
  UNION

  """Location adjacent to an enum definition."""
  ENUM

  """Location adjacent to an enum value definition."""
  ENUM_VALUE

  """Location adjacent to an input object definition."""
  INPUT_OBJECT

  """Location adjacent to an input object field definition."""
  INPUT_FIELD_DEFINITION
}

"""
One possible value for a given Enum. Enum values are unique values, not a
placeholder for a string or numeric value. However an Enum value is returned in
a JSON response as a string.
"""
type __EnumValue {
  name: String!
  description: String
  isDeprecated: Boolean!
  deprecationReason: String
}

"""
Object and Interface types are described by a list of Fields, each of which has
a name, potentially a list of arguments, and a return type.
"""
type __Field {
  name: String!
  description: String
  args: [__InputValue!]!
  type: __Type!
  isDeprecated: Boolean!
  deprecationReason: String
}

"""
Arguments provided to Fields or Directives and the input fields of an
InputObject are represented as Input Values which describe their type and
optionally a default value.
"""
type __InputValue {
  name: String!
  description: String
  type: __Type!
  defaultValue: String
}

"""
A GraphQL Schema defines the capabilities of a GraphQL server. It exposes all
available types and directives on the server, as well as the entry points for
query, mutation and subscription operations.
"""
type __Schema {
  """A list of all types supported by this server."""
  types: [__Type!]!

  """The type that query operations will be rooted at."""
  queryType: __Type!

  """
  If this server supports mutation, the type that mutation operations will be rooted at.
  """
  mutationType: __Type

  """
  If this server support subscription, the type that subscription operations will be rooted at.
  """
  subscriptionType: __Type

  """A list of all directives supported by this server."""
  directives: [__Directive!]!
}

"""
The fundamental unit of any GraphQL Schema is the type. There are many kinds of
types in GraphQL as represented by the `__TypeKind` enum.

Depending on the kind of a type, certain fields describe information about that
type. Scalar types provide no information beyond a name and description, while
Enum types provide their values. Object and Interface types provide the fields
they describe. Abstract types, Union and Interface, provide the Object types
possible at runtime. List and NonNull types compose other types.
"""
type __Type {
  kind: __TypeKind!
  name: String
  description: String
  fields(includeDeprecated: Boolean = false): [__Field!]
  interfaces: [__Type!]
  possibleTypes: [__Type!]
  enumValues(includeDeprecated: Boolean = false): [__EnumValue!]
  inputFields: [__InputValue!]
  ofType: __Type
}

"""An enum describing what kind of type a given `__Type` is"""
enum __TypeKind {
  """Indicates this type is a scalar."""
  SCALAR

  """
  Indicates this type is an object. `fields` and `interfaces` are valid fields.
  """
  OBJECT

  """
  Indicates this type is an interface. `fields` and `possibleTypes` are valid fields.
  """
  INTERFACE

  """Indicates this type is a union. `possibleTypes` is a valid field."""
  UNION

  """Indicates this type is an enum. `enumValues` is a valid field."""
  ENUM

  """
  Indicates this type is an input object. `inputFields` is a valid field.
  """
  INPUT_OBJECT

  """Indicates this type is a list. `ofType` is a valid field."""
  LIST

  """Indicates this type is a non-null. `ofType` is a valid field."""
  NON_NULL
}
'''
    )
