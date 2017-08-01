from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (GraphQLArgument, GraphQLField, GraphQLInt,
                          GraphQLList, GraphQLObjectType, GraphQLSchema,
                          GraphQLString)


class NumberHolder(object):

    def __init__(self, n):
        self.theNumber = n


class Root(object):

    def __init__(self, n):
        self.numberHolder = NumberHolder(n)

    def immediately_change_the_number(self, n):
        self.numberHolder.theNumber = n
        return self.numberHolder

    def promise_to_change_the_number(self, n):
        # TODO: async
        return self.immediately_change_the_number(n)

    def fail_to_change_the_number(self, n):
        raise Exception('Cannot change the number')

    def promise_and_fail_to_change_the_number(self, n):
        # TODO: async
        self.fail_to_change_the_number(n)


NumberHolderType = GraphQLObjectType('NumberHolder', {
    'theNumber': GraphQLField(GraphQLInt)
})

QueryType = GraphQLObjectType('Query', {
    'numberHolder': GraphQLField(NumberHolderType)
})

MutationType = GraphQLObjectType('Mutation', {
    'immediatelyChangeTheNumber': GraphQLField(
        NumberHolderType,
        args={'newNumber': GraphQLArgument(GraphQLInt)},
        resolver=lambda obj, info, **args:
            obj.immediately_change_the_number(args['newNumber'])),
    'promiseToChangeTheNumber': GraphQLField(
        NumberHolderType,
        args={'newNumber': GraphQLArgument(GraphQLInt)},
        resolver=lambda obj, info, **args:
            obj.promise_to_change_the_number(args['newNumber'])),
    'failToChangeTheNumber': GraphQLField(
        NumberHolderType,
        args={'newNumber': GraphQLArgument(GraphQLInt)},
        resolver=lambda obj, info, **args:
            obj.fail_to_change_the_number(args['newNumber'])),
    'promiseAndFailToChangeTheNumber': GraphQLField(
        NumberHolderType,
        args={'newNumber': GraphQLArgument(GraphQLInt)},
        resolver=lambda obj, info, **args:
            obj.promise_and_fail_to_change_the_number(args['newNumber'])),
})

schema = GraphQLSchema(QueryType, MutationType)


def assert_evaluate_mutations_serially(executor=None):
    doc = '''mutation M {
      first: immediatelyChangeTheNumber(newNumber: 1) {
        theNumber
      },
      second: promiseToChangeTheNumber(newNumber: 2) {
        theNumber
      },
      third: immediatelyChangeTheNumber(newNumber: 3) {
        theNumber
      }
      fourth: promiseToChangeTheNumber(newNumber: 4) {
        theNumber
      },
      fifth: immediatelyChangeTheNumber(newNumber: 5) {
        theNumber
      }
    }'''
    ast = parse(doc)
    result = execute(schema, ast, Root(6), operation_name='M', executor=executor)
    assert not result.errors
    assert result.data == \
        {
            'first': {'theNumber': 1},
            'second': {'theNumber': 2},
            'third': {'theNumber': 3},
            'fourth': {'theNumber': 4},
            'fifth': {'theNumber': 5},
        }


def test_evaluates_mutations_serially():
    assert_evaluate_mutations_serially()


def test_evaluates_mutations_correctly_in_the_presense_of_a_failed_mutation():
    doc = '''mutation M {
      first: immediatelyChangeTheNumber(newNumber: 1) {
        theNumber
      },
      second: promiseToChangeTheNumber(newNumber: 2) {
        theNumber
      },
      third: failToChangeTheNumber(newNumber: 3) {
        theNumber
      }
      fourth: promiseToChangeTheNumber(newNumber: 4) {
        theNumber
      },
      fifth: immediatelyChangeTheNumber(newNumber: 5) {
        theNumber
      }
      sixth: promiseAndFailToChangeTheNumber(newNumber: 6) {
        theNumber
      }
    }'''
    ast = parse(doc)
    result = execute(schema, ast, Root(6), operation_name='M')
    assert result.data == \
        {
            'first': {'theNumber': 1},
            'second': {'theNumber': 2},
            'third': None,
            'fourth': {'theNumber': 4},
            'fifth': {'theNumber': 5},
            'sixth': None,
        }
    assert len(result.errors) == 2
    # TODO: check error location
    assert result.errors[0].message == 'Cannot change the number'
    assert result.errors[1].message == 'Cannot change the number'
