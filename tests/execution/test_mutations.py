from pytest import mark
from promise import Promise

from graphql.execution import execute
from graphql.language import parse
from graphql.type import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInt,
    GraphQLObjectType,
    GraphQLSchema,
)


# noinspection PyPep8Naming
class NumberHolder:
    def __init__(self, originalNumber):
        self.theNumber = originalNumber


# noinspection PyPep8Naming
class Root:
    def __init__(self, originalNumber):
        self.numberHolder = NumberHolder(originalNumber)

    def immediately_change_the_number(self, newNumber):
        self.numberHolder.theNumber = newNumber
        return self.numberHolder

    def promise_to_change_the_number(self, new_number):
        return Promise.resolve(self.immediately_change_the_number(new_number))

    def fail_to_change_the_number(self, newNumber):
        return Promise.reject(
            RuntimeError("Cannot change the number to {}".format(newNumber))
        )

    def promise_and_fail_to_change_the_number(self, newNumber):
        return self.fail_to_change_the_number(newNumber)


numberHolderType = GraphQLObjectType(
    "NumberHolder", {"theNumber": GraphQLField(GraphQLInt)}
)

# noinspection PyPep8Naming
schema = GraphQLSchema(
    GraphQLObjectType("Query", {"numberHolder": GraphQLField(numberHolderType)}),
    GraphQLObjectType(
        "Mutation",
        {
            "immediatelyChangeTheNumber": GraphQLField(
                numberHolderType,
                args={"newNumber": GraphQLArgument(GraphQLInt)},
                resolve=lambda obj, _info, newNumber: obj.immediately_change_the_number(
                    newNumber
                ),
            ),
            "promiseToChangeTheNumber": GraphQLField(
                numberHolderType,
                args={"newNumber": GraphQLArgument(GraphQLInt)},
                resolve=lambda obj, _info, newNumber: obj.promise_to_change_the_number(
                    newNumber
                ),
            ),
            "failToChangeTheNumber": GraphQLField(
                numberHolderType,
                args={"newNumber": GraphQLArgument(GraphQLInt)},
                resolve=lambda obj, _info, newNumber: obj.fail_to_change_the_number(
                    newNumber
                ),
            ),
            "promiseAndFailToChangeTheNumber": GraphQLField(
                numberHolderType,
                args={"newNumber": GraphQLArgument(GraphQLInt)},
                resolve=lambda obj, _info, newNumber: obj.promise_and_fail_to_change_the_number(
                    newNumber
                ),
            ),
        },
    ),
)


def describe_execute_handles_mutation_execution_ordering():
    def evaluates_mutations_serially():
        doc = """
            mutation M {
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
            }
            """

        mutation_result = execute(schema, parse(doc), Root(6)).get()

        assert mutation_result == (
            {
                "first": {"theNumber": 1},
                "second": {"theNumber": 2},
                "third": {"theNumber": 3},
                "fourth": {"theNumber": 4},
                "fifth": {"theNumber": 5},
            },
            None,
        )

    def evaluates_mutations_correctly_in_presence_of_a_failed_mutation():
        doc = """
            mutation M {
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
            }
            """

        result = execute(schema, parse(doc), Root(6)).get()

        assert result == (
            {
                "first": {"theNumber": 1},
                "second": {"theNumber": 2},
                "third": None,
                "fourth": {"theNumber": 4},
                "fifth": {"theNumber": 5},
                "sixth": None,
            },
            [
                {
                    "message": "Cannot change the number to 3",
                    "locations": [(9, 15)],
                    "path": ["third"],
                },
                {
                    "message": "Cannot change the number to 6",
                    "locations": [(18, 15)],
                    "path": ["sixth"],
                },
            ],
        )
