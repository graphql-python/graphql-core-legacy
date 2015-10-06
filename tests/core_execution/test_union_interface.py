from graphql.core.execution import execute
from graphql.core.language.parser import parse
from graphql.core.type import (
    GraphQLSchema,
    GraphQLField,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLList,
    GraphQLString,
    GraphQLBoolean
)


class Dog(object):
    def __init__(self, name, barks):
        self.name = name
        self.barks = barks


class Cat(object):
    def __init__(self, name, meows):
        self.name = name
        self.meows = meows


class Person(object):
    def __init__(self, name, pets, friends):
        self.name = name
        self.pets = pets
        self.friends = friends


NamedType = GraphQLInterfaceType('Named', {
    'name': GraphQLField(GraphQLString)
})

DogType = GraphQLObjectType(
    name='Dog',
    interfaces=[NamedType],
    fields={
        'name': GraphQLField(GraphQLString),
        'barks': GraphQLField(GraphQLBoolean),
    },
    is_type_of=lambda value, info: isinstance(value, Dog)
)

CatType = GraphQLObjectType(
    name='Cat',
    interfaces=[NamedType],
    fields={
        'name': GraphQLField(GraphQLString),
        'meows': GraphQLField(GraphQLBoolean),
    },
    is_type_of=lambda value, info: isinstance(value, Cat)
)


def resolve_pet_type(value):
    if isinstance(value, Dog):
        return DogType
    if isinstance(value, Cat):
        return CatType

PetType = GraphQLUnionType('Pet', [DogType, CatType],
                           resolve_type=resolve_pet_type)

PersonType = GraphQLObjectType(
    name='Person',
    interfaces=[NamedType],
    fields={
        'name': GraphQLField(GraphQLString),
        'pets': GraphQLField(GraphQLList(PetType)),
        'friends': GraphQLField(GraphQLList(NamedType)),
    },
    is_type_of=lambda value, info: isinstance(value, Person)
)

schema = GraphQLSchema(PersonType)

garfield = Cat('Garfield', False)
odie = Dog('Odie', True)
liz = Person('Liz', [], [])
john = Person('John', [garfield, odie], [liz, odie])

# Execute: Union and intersection types

def test_can_introspect_on_union_and_intersetion_types():
    # TODO
    pass


def test_executes_using_union_types():
    # NOTE: This is an *invalid* query, but it should be an *executable* query.
    ast = parse('''
        {
            __typename
            name
            pets {
                __typename
                name
                barks
                meows
            }
        }
    ''')
    result = execute(schema, john, ast)
    assert not result.errors
    assert result.data == {
        '__typename': 'Person',
        'name': 'John',
        'pets': [
            {'__typename': 'Cat', 'name': 'Garfield', 'meows': False},
            {'__typename': 'Dog', 'name': 'Odie', 'barks': True}
        ]
   }


def test_executes_union_types_with_inline_fragment():
    # This is the valid version of the query in the above test.
    ast = parse('''
      {
        __typename
        name
        pets {
          __typename
          ... on Dog {
            name
            barks
          }
          ... on Cat {
            name
            meows
          }
        }
      }
    ''')
    result = execute(schema, john, ast)
    assert not result.errors
    assert result.data == {
        '__typename': 'Person',
        'name': 'John',
        'pets': [
            {'__typename': 'Cat', 'name': 'Garfield', 'meows': False},
            {'__typename': 'Dog', 'name': 'Odie', 'barks': True}
        ]
    }


def test_executes_using_interface_types():
    # NOTE: This is an *invalid* query, but it should be an *executable* query.
    ast = parse('''
      {
        __typename
        name
        friends {
          __typename
          name
          barks
          meows
        }
      }
    ''')
    result = execute(schema, john, ast)
    assert not result.errors
    assert result.data == {
        '__typename': 'Person',
        'name': 'John',
        'friends': [
            {'__typename': 'Person', 'name': 'Liz'},
            {'__typename': 'Dog', 'name': 'Odie', 'barks': True}
        ]
    }


def test_executes_interface_types_with_inline_fragment():
    # This is the valid version of the query in the above test.
    ast = parse('''
      {
        __typename
        name
        friends {
          __typename
          name
          ... on Dog {
            barks
          }
          ... on Cat {
            meows
          }
        }
      }
    ''')
    result = execute(schema, john, ast)
    assert not result.errors
    assert result.data == {
        '__typename': 'Person',
        'name': 'John',
        'friends': [
            {'__typename': 'Person', 'name': 'Liz'},
            {'__typename': 'Dog', 'name': 'Odie', 'barks': True}
        ]
    }


def test_allows_fragment_conditions_to_be_abstract_types():
    ast = parse('''
      {
        __typename
        name
        pets { ...PetFields }
        friends { ...FriendFields }
      }
      fragment PetFields on Pet {
        __typename
        ... on Dog {
          name
          barks
        }
        ... on Cat {
          name
          meows
        }
      }
      fragment FriendFields on Named {
        __typename
        name
        ... on Dog {
          barks
        }
        ... on Cat {
          meows
        }
      }
    ''')
    result = execute(schema, john, ast)
    assert not result.errors
    assert result.data == {
        '__typename': 'Person',
        'name': 'John',
        'pets': [
            {'__typename': 'Cat', 'name': 'Garfield', 'meows': False},
            {'__typename': 'Dog', 'name': 'Odie', 'barks': True}
        ],
        'friends': [
            {'__typename': 'Person', 'name': 'Liz'},
            {'__typename': 'Dog', 'name': 'Odie', 'barks': True}
        ]
    }


def test_only_include_fields_from_matching_fragment_condition():
    ast = parse('''
      {
        pets { ...PetFields }
      }
      fragment PetFields on Pet {
        __typename
        ... on Dog {
          name
        }
      }
    ''')
    result = execute(schema, john, ast)
    assert not result.errors
    assert result.data == {
        'pets': [
            {'__typename': 'Cat'},
            {'__typename': 'Dog', 'name': 'Odie'}
        ],
    }
