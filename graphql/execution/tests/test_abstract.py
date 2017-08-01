from graphql import graphql
from graphql.type import GraphQLBoolean, GraphQLSchema, GraphQLString
from graphql.type.definition import (GraphQLField, GraphQLInterfaceType,
                                     GraphQLList, GraphQLObjectType,
                                     GraphQLUnionType)


class Dog(object):

    def __init__(self, name, woofs):
        self.name = name
        self.woofs = woofs


class Cat(object):

    def __init__(self, name, meows):
        self.name = name
        self.meows = meows


class Human(object):

    def __init__(self, name):
        self.name = name


is_type_of = lambda type: lambda obj, info: isinstance(obj, type)


def make_type_resolver(types):
    def resolve_type(obj, info):
        if callable(types):
            t = types()
        else:
            t = types

        for klass, type in t:
            if isinstance(obj, klass):
                return type

        return None

    return resolve_type


def test_is_type_of_used_to_resolve_runtime_type_for_interface():
    PetType = GraphQLInterfaceType(
        name='Pet',
        fields={
            'name': GraphQLField(GraphQLString)
        }
    )

    DogType = GraphQLObjectType(
        name='Dog',
        interfaces=[PetType],
        is_type_of=is_type_of(Dog),
        fields={
            'name': GraphQLField(GraphQLString),
            'woofs': GraphQLField(GraphQLBoolean)
        }
    )

    CatType = GraphQLObjectType(
        name='Cat',
        interfaces=[PetType],
        is_type_of=is_type_of(Cat),
        fields={
            'name': GraphQLField(GraphQLString),
            'meows': GraphQLField(GraphQLBoolean)
        }
    )

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields={
                'pets': GraphQLField(
                    GraphQLList(PetType),
                    resolver=lambda *_: [Dog('Odie', True), Cat('Garfield', False)]
                )
            }
        ),
        types=[CatType, DogType]
    )

    query = '''
    {
        pets {
            name
            ... on Dog {
                woofs
            }
            ... on Cat {
                meows
            }
        }
    }
    '''

    result = graphql(schema, query)
    assert not result.errors
    assert result.data == {'pets': [{'woofs': True, 'name': 'Odie'}, {'name': 'Garfield', 'meows': False}]}


def test_is_type_of_used_to_resolve_runtime_type_for_union():
    DogType = GraphQLObjectType(
        name='Dog',
        is_type_of=is_type_of(Dog),
        fields={
            'name': GraphQLField(GraphQLString),
            'woofs': GraphQLField(GraphQLBoolean)
        }
    )

    CatType = GraphQLObjectType(
        name='Cat',
        is_type_of=is_type_of(Cat),
        fields={
            'name': GraphQLField(GraphQLString),
            'meows': GraphQLField(GraphQLBoolean)
        }
    )

    PetType = GraphQLUnionType(
        name='Pet',
        types=[CatType, DogType]
    )

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields={
                'pets': GraphQLField(
                    GraphQLList(PetType),
                    resolver=lambda *_: [Dog('Odie', True), Cat('Garfield', False)]
                )
            }
        ),
        types=[CatType, DogType]
    )

    query = '''
    {
        pets {
            ... on Dog {
                name
                woofs
            }
            ... on Cat {
                name
                meows
            }
        }
    }
    '''

    result = graphql(schema, query)
    assert not result.errors
    assert result.data == {'pets': [{'woofs': True, 'name': 'Odie'}, {'name': 'Garfield', 'meows': False}]}


def test_resolve_type_on_interface_yields_useful_error():
    PetType = GraphQLInterfaceType(
        name='Pet',
        fields={
            'name': GraphQLField(GraphQLString)
        },
        resolve_type=make_type_resolver(lambda: [
            (Dog, DogType),
            (Cat, CatType),
            (Human, HumanType)
        ])
    )

    DogType = GraphQLObjectType(
        name='Dog',
        interfaces=[PetType],
        fields={
            'name': GraphQLField(GraphQLString),
            'woofs': GraphQLField(GraphQLBoolean)
        }
    )

    HumanType = GraphQLObjectType(
        name='Human',
        fields={
            'name': GraphQLField(GraphQLString),
        }
    )

    CatType = GraphQLObjectType(
        name='Cat',
        interfaces=[PetType],
        fields={
            'name': GraphQLField(GraphQLString),
            'meows': GraphQLField(GraphQLBoolean)
        }
    )

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields={
                'pets': GraphQLField(
                    GraphQLList(PetType),
                    resolver=lambda *_: [Dog('Odie', True), Cat('Garfield', False), Human('Jon')]
                )
            }
        ),
        types=[DogType, CatType]
    )

    query = '''
    {
        pets {
            name
            ... on Dog {
                woofs
            }
            ... on Cat {
                meows
            }
        }
    }
    '''

    result = graphql(schema, query)
    assert result.errors[0].message == 'Runtime Object type "Human" is not a possible type for "Pet".'
    assert result.data == {'pets': [{'woofs': True, 'name': 'Odie'}, {'name': 'Garfield', 'meows': False}, None]}


def test_resolve_type_on_union_yields_useful_error():
    DogType = GraphQLObjectType(
        name='Dog',
        fields={
            'name': GraphQLField(GraphQLString),
            'woofs': GraphQLField(GraphQLBoolean)
        }
    )

    HumanType = GraphQLObjectType(
        name='Human',
        fields={
            'name': GraphQLField(GraphQLString),
        }
    )

    CatType = GraphQLObjectType(
        name='Cat',
        fields={
            'name': GraphQLField(GraphQLString),
            'meows': GraphQLField(GraphQLBoolean)
        }
    )

    PetType = GraphQLUnionType(
        name='Pet',
        types=[DogType, CatType],
        resolve_type=make_type_resolver(lambda: [
            (Dog, DogType),
            (Cat, CatType),
            (Human, HumanType)
        ])
    )

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields={
                'pets': GraphQLField(
                    GraphQLList(PetType),
                    resolver=lambda *_: [Dog('Odie', True), Cat('Garfield', False), Human('Jon')]
                )
            }
        )
    )

    query = '''
    {
        pets {
            ... on Dog {
                name
                woofs
            }
            ... on Cat {
                name
                meows
            }
        }
    }
    '''

    result = graphql(schema, query)
    assert result.errors[0].message == 'Runtime Object type "Human" is not a possible type for "Pet".'
    assert result.data == {'pets': [{'woofs': True, 'name': 'Odie'}, {'name': 'Garfield', 'meows': False}, None]}


def test_resolve_type_can_use_type_string():

    def type_string_resolver(obj, *_):
        if isinstance(obj, Dog):
            return 'Dog'
        if isinstance(obj, Cat):
            return 'Cat'

    PetType = GraphQLInterfaceType(
        name='Pet',
        fields={
            'name': GraphQLField(GraphQLString)
        },
        resolve_type=type_string_resolver
    )

    DogType = GraphQLObjectType(
        name='Dog',
        interfaces=[PetType],
        fields={
            'name': GraphQLField(GraphQLString),
            'woofs': GraphQLField(GraphQLBoolean)
        }
    )

    CatType = GraphQLObjectType(
        name='Cat',
        interfaces=[PetType],
        fields={
            'name': GraphQLField(GraphQLString),
            'meows': GraphQLField(GraphQLBoolean)
        }
    )

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields={
                'pets': GraphQLField(
                    GraphQLList(PetType),
                    resolver=lambda *_: [Dog('Odie', True), Cat('Garfield', False)]
                )
            }
        ),
        types=[CatType, DogType]
    )

    query = '''
    {
        pets {
            name
            ... on Dog {
                woofs
            }
            ... on Cat {
                meows
            }
        }
    }
    '''

    result = graphql(schema, query)
    assert not result.errors
    assert result.data == {'pets': [{'woofs': True, 'name': 'Odie'}, {'name': 'Garfield', 'meows': False}]}
