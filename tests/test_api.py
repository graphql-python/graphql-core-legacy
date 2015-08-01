from pytest import raises
from graphql import graphql
from graphql.api import Schema

gql = Schema()


class Character(gql.InterfaceType):
    """A character in the Star Wars Trilogy"""
    id = gql.Field(
        gql.NonNull(gql.String),
        description='The id of the character.'
    )
    name = gql.Field(
        gql.String,
        description='The name of the character.'
    )
    friends = gql.Field(
        gql.List('Character'),
        description='The friends of the character, or an empty list if they have none.'
    )
    appearsIn = gql.Field(
        gql.List('Episode'),
        description='Which movies they appear in.'
    )


class Human(gql.ObjectType):
    """A humanoid creature in the Star Wars universe."""
    __interfaces__ = [Character]  # Interfaces should be declared first
    id = gql.Field(
        gql.NonNull(gql.String),
        description='The id of the character.'
    )
    name = gql.Field(
        gql.String,
        description='The name of the character.'
    )
    friends = gql.Field(
        gql.List('Character'),
        description='The friends of the character, or an empty list if they have none.'
    )
    appearsIn = gql.Field(
        gql.List('Episode'),
        description='Which movies they appear in.'
    )
    homePlanet = gql.Field(
        gql.String
    )


def sort_lists(value):
    if isinstance(value, dict):
        new_mapping = {}
        for k, v in value.iteritems():
            new_mapping[k] = sort_lists(v)
        return new_mapping
    elif isinstance(value, list):
        return sorted(map(sort_lists, value))
    return value


def test_define_enum_type():
    gql = Schema()

    class EpisodeEnum(gql.EnumType):
        """One of the films in the Star Wars Trilogy"""
        __typename__ = 'Episode'
        NEWHOPE = gql.EnumValue(4, description='Released in 1977.')
        EMPIRE = gql.EnumValue(5, description='Released in 1980.')
        JEDI = gql.EnumValue(6, description='Released in 1983.')

    class QueryRoot(gql.QueryRoot):
        episode = gql.Field(EpisodeEnum)

    result = graphql(gql.to_internal(), '''{
        type: __type(name: "Episode") {
            name
            description
            enumValues { name, description }
        }
    }''')
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({
        "type": {
            "name": "Episode",
            "description": "One of the films in the Star Wars Trilogy",
            "enumValues": [
                {"name": "NEWHOPE", "description": "Released in 1977."},
                {"name": "EMPIRE", "description": "Released in 1980."},
                {"name": "JEDI", "description": "Released in 1983."},
            ]
        }
    })


def test_define_object_type():
    gql = Schema()

    class EpisodeEnum(gql.EnumType):
        """One of the films in the Star Wars Trilogy"""
        __typename__ = 'Episode'
        NEWHOPE = gql.EnumValue(4, description='Released in 1977.')
        EMPIRE = gql.EnumValue(5, description='Released in 1980.')
        JEDI = gql.EnumValue(6, description='Released in 1983.')

    class QueryRoot(gql.QueryRoot):
        """description"""
        byPublicType = gql.Field(EpisodeEnum)
        byName = gql.Field('Episode')
        byInternalType = gql.Field(gql.String)
        byPublicTypeWrapped = gql.Field(gql.List(EpisodeEnum))
        byNameWrapped = gql.Field(gql.List('Episode'))
        byInternalTypeWrapped = gql.Field(gql.List(gql.String))

    result = graphql(gql.to_internal(), '''{
        type: __type(name: "QueryRoot") {
            name
            description
            fields { name, type { ...TypeRef } }
        }
    }
    fragment TypeRef on __Type {
        kind, name
        ofType {
            kind, name
            ofType { kind, name, ofType }
        }
    }''')
    assert not result.errors
    episode_type = {"kind": "ENUM", "name": "Episode", "ofType": None}
    string_type = {"kind": "SCALAR", "name": "String", "ofType": None}
    assert sort_lists(result.data) == sort_lists({
        "type": {
            "name": "QueryRoot",
            "description": "description",
            "fields": [
                {"name": "byPublicType", "type": episode_type},
                {"name": "byName", "type": episode_type},
                {"name": "byInternalType", "type": string_type},
                {"name": "byPublicTypeWrapped", "type": {"kind": "LIST", "name": None, "ofType": episode_type}},
                {"name": "byNameWrapped", "type": {"kind": "LIST", "name": None, "ofType": episode_type}},
                {"name": "byInternalTypeWrapped", "type": {"kind": "LIST", "name": None, "ofType": string_type}},
            ]
        }
    })


def test_field_arguments():
    gql = Schema()

    class A(gql.ObjectType):
        pass

    class QueryRoot(gql.QueryRoot):
        field = gql.Field(gql.String, {
            'byPublicType': gql.Argument(A),
            'byName': gql.Argument('A'),
            'byInternalType': gql.Argument(gql.String),
            'byPublicTypeWrapped': gql.Argument(gql.List(A)),
            'byNameWrapped': gql.Argument(gql.List('A')),
            'byInternalTypeWrapped': gql.Argument(gql.List(gql.String)),
        })

    result = graphql(gql.to_internal(), '''{
        type: __type(name: "QueryRoot") {
            fields {
                args {
                    name
                    type { ...TypeRef }
                }
            }
        }
    }
    fragment TypeRef on __Type {
        kind, name
        ofType {
            kind, name
            ofType { kind, name, ofType }
        }
    }''')
    assert not result.errors
    a_type = {"kind": "OBJECT", "name": "A", "ofType": None}
    string_type = {"kind": "SCALAR", "name": "String", "ofType": None}
    assert sort_lists(result.data) == sort_lists({
        "type": {
            "fields": [{"args": [
                {"name": "byPublicType", "type": a_type},
                {"name": "byName", "type": a_type},
                {"name": "byInternalType", "type": string_type},
                {"name": "byPublicTypeWrapped", "type": {"kind": "LIST", "name": None, "ofType": a_type}},
                {"name": "byNameWrapped", "type": {"kind": "LIST", "name": None, "ofType": a_type}},
                {"name": "byInternalTypeWrapped", "type": {"kind": "LIST", "name": None, "ofType": string_type}},
            ]}]
        }
    })


def test_prevent_defining_many_query_roots():
    gql = Schema()

    class QueryRoot(gql.QueryRoot):
        pass

    with raises(Exception):
        class SecondQueryRoot(gql.QueryRoot):
            pass


def test_define_union_type():
    gql = Schema()

    class A(gql.ObjectType):
        pass

    class B(gql.ObjectType):
        pass

    class UnionType(gql.UnionType):
        """description"""
        __typename__ = 'Union'
        types = [A, B]

    class QueryRoot(gql.QueryRoot):
        union = gql.Field(UnionType)

    result = graphql(gql.to_internal(), '''{
        type: __type(name: "Union") {
            kind
            name
            description
            possibleTypes { name }
        }
    }''')
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({
        "type": {
            "name": "Union",
            "description": "description",
            "kind": "UNION",
            "possibleTypes": [
                {"name": "A"},
                {"name": "B"},
                ]
        }
    })
