from ...type import (GraphQLSchema,
                     GraphQLInterfaceType,
                     GraphQLObjectType,
                     GraphQLField,
                     GraphQLString)
from pytest import raises

interface_type = GraphQLInterfaceType(
    name='Interface',
    fields={
        'field_name': GraphQLField(
            type=GraphQLString,
            resolver=lambda *_: implementing_type
            )
    }
)

implementing_type = GraphQLObjectType(
    name='Object',
    interfaces=[interface_type],
    fields={
        'field_name': GraphQLField(type=GraphQLString, resolver=lambda *_: '')
    }
)


schema = GraphQLSchema(
    query=GraphQLObjectType(
        name='Query',
        fields={
            'get_object': GraphQLField(type=interface_type, resolver=lambda *_: {})
        }
    )
)

def test_throws_human_readable_error_if_schematypes_not_defined():
    with raises(AssertionError) as exci:
        schema.is_possible_type(interface_type, implementing_type)

    assert str(exci.value) == ('Could not find possible implementing types for $Interface in schema. Check that '
                               'schema.types is defined and is an array ofall possible types in the schema.')
