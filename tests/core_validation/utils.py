from graphql.core.validation import validate
from graphql.core.language.parser import parse
from graphql.core.type import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLArgument,
    GraphQLID,
    GraphQLString,
    GraphQLBoolean,
    GraphQLInterfaceType, GraphQLEnumType, GraphQLEnumValue, GraphQLInputObjectType)
from graphql.core.error import format_error

Pet = GraphQLInterfaceType('Pet', {
    'name': GraphQLField(GraphQLString, {
        'surname': GraphQLArgument(GraphQLBoolean),
    }),
})

Dog = GraphQLObjectType('Dog', {
    'barks': GraphQLField(GraphQLBoolean),
}, interfaces=[Pet])

Cat = GraphQLObjectType('Cat', lambda: {
    'furColor': GraphQLField(FurColor)
}, interfaces=[Pet])

Human = GraphQLObjectType('Human', {
    'name': GraphQLField(GraphQLString, {
        'surname': GraphQLArgument(GraphQLBoolean),
    })
})

FurColor = GraphQLEnumType('FurColor', {
    'BROWN': GraphQLEnumValue(0),
    'BLACK': GraphQLEnumValue(1),
    'TAN': GraphQLEnumValue(2),
    'SPOTTED': GraphQLEnumValue(3),
})

ComplexInput = GraphQLInputObjectType('ComplexInput', {
    'stringField': GraphQLField(GraphQLString)
})

ComplicatedArgs = GraphQLObjectType('ComplicatedArgs', {
    'complexArgField': GraphQLField(GraphQLString, {
        'complexArg': GraphQLArgument(ComplexInput),
    })
})

QueryRoot = GraphQLObjectType('QueryRoot', {
    'human': GraphQLField(Human, {
        'id': GraphQLArgument(GraphQLID)
    }),
    'pet': GraphQLField(Pet),
    'complicatedArgs': GraphQLField(ComplicatedArgs),
})

default_schema = GraphQLSchema(query=QueryRoot)


def expect_valid(schema, rules, query):
    errors = validate(schema, parse(query), rules)
    assert errors == [], 'Should validate'


def expect_invalid(schema, rules, query, expected_errors):
    errors = validate(schema, parse(query), rules)
    assert errors, 'Should not validate'
    assert map(format_error, errors) == expected_errors


def expect_passes_rule(rule, query):
    return expect_valid(default_schema, [rule], query)


def expect_fails_rule(rule, query, errors):
    return expect_invalid(default_schema, [rule], query, errors)
