import json
from graphql.core import graphql
from graphql.core.error import format_error
from graphql.core.language.parser import parse
from graphql.core.execution import execute
from graphql.core.type import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLArgument,
    GraphQLInputObjectType,
    GraphQLInputObjectField,
    GraphQLString,
    GraphQLList,
    GraphQLEnumType,
    GraphQLEnumValue,
)
from graphql.core.validation.rules import ProvidedNonNullArguments
from graphql.core.utils.introspection_query import introspection_query


def sort_lists(value):
    if isinstance(value, dict):
        new_mapping = []
        for k in sorted(value.keys()):
            new_mapping.append((k, sort_lists(value[k])))
        return new_mapping
    elif isinstance(value, list):
        return sorted(map(sort_lists, value), key=repr)
    return value


def test_executes_an_introspection_query():
    EmptySchema = GraphQLSchema(GraphQLObjectType('QueryRoot', {}))

    result = graphql(EmptySchema, introspection_query)
    assert not result.errors

    expected = {'__schema': {'directives': [{'args': [{'defaultValue': None,
                                                       'description': 'Directs the executor to include this field or fragment only when the `if` argument is true.',
                                                       'name': 'if',
                                                       'type': {'kind': 'NON_NULL',
                                                                'name': None,
                                                                'ofType': {'kind': 'SCALAR',
                                                                           'name': 'Boolean',
                                                                           'ofType': None}}}],
                                             'description': None,
                                             'name': 'include',
                                             'onField': True,
                                             'onFragment': True,
                                             'onOperation': False},
                                            {'args': [{'defaultValue': None,
                                                       'description': 'Directs the executor to skip this field or fragment only when the `if` argument is true.',
                                                       'name': 'if',
                                                       'type': {'kind': 'NON_NULL',
                                                                'name': None,
                                                                'ofType': {'kind': 'SCALAR',
                                                                           'name': 'Boolean',
                                                                           'ofType': None}}}],
                                             'description': None,
                                             'name': 'skip',
                                             'onField': True,
                                             'onFragment': True,
                                             'onOperation': False}],
                             'mutationType': None,
                             'queryType': {'name': 'QueryRoot'},
                             'types': [{'description': None,
                                        'enumValues': None,
                                        'fields': [{'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'isDeprecated',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'SCALAR',
                                                                        'name': 'Boolean',
                                                                        'ofType': None}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'deprecationReason',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'description',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'name',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}}}],
                                        'inputFields': None,
                                        'interfaces': [],
                                        'kind': 'OBJECT',
                                        'name': '__EnumValue',
                                        'possibleTypes': None},
                                       {'description': None,
                                        'enumValues': None,
                                        'fields': [{'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'onFragment',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'Boolean',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'onOperation',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'Boolean',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'onField',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'Boolean',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'name',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'args',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'LIST',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'NON_NULL',
                                                                                   'name': None,
                                                                                   'ofType': {'kind': 'OBJECT',
                                                                                              'name': '__InputValue'}}}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'description',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}}],
                                        'inputFields': None,
                                        'interfaces': [],
                                        'kind': 'OBJECT',
                                        'name': '__Directive',
                                        'possibleTypes': None},
                                       {'description': None,
                                        'enumValues': None,
                                        'fields': [{'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'name',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'description',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'isDeprecated',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'SCALAR',
                                                                        'name': 'Boolean',
                                                                        'ofType': None}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'args',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'LIST',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'NON_NULL',
                                                                                   'name': None,
                                                                                   'ofType': {'kind': 'OBJECT',
                                                                                              'name': '__InputValue'}}}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'deprecationReason',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'type',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'OBJECT',
                                                                        'name': '__Type',
                                                                        'ofType': None}}}],
                                        'inputFields': None,
                                        'interfaces': [],
                                        'kind': 'OBJECT',
                                        'name': '__Field',
                                        'possibleTypes': None},
                                       {'description': None,
                                        'enumValues': None,
                                        'fields': None,
                                        'inputFields': None,
                                        'interfaces': None,
                                        'kind': 'SCALAR',
                                        'name': 'Boolean',
                                        'possibleTypes': None},
                                       {'description': 'An enum describing what kind of type a given __Type is',
                                        'enumValues': [{'deprecationReason': None,
                                                        'description': 'Indicates this type is a scalar.',
                                                        'isDeprecated': False,
                                                        'name': 'SCALAR'},
                                                       {'deprecationReason': None,
                                                        'description': 'Indicates this type is a union. `possibleTypes` is a valid field.',
                                                        'isDeprecated': False,
                                                        'name': 'UNION'},
                                                       {'deprecationReason': None,
                                                        'description': 'Indicates this type is an object. `fields` and `interfaces` are valid fields.',
                                                        'isDeprecated': False,
                                                        'name': 'OBJECT'},
                                                       {'deprecationReason': None,
                                                        'description': 'Indicates this type is a non-null. `ofType` is a valid field.',
                                                        'isDeprecated': False,
                                                        'name': 'NON_NULL'},
                                                       {'deprecationReason': None,
                                                        'description': 'Indicates this type is an input object. `inputFields` is a valid field.',
                                                        'isDeprecated': False,
                                                        'name': 'INPUT_OBJECT'},
                                                       {'deprecationReason': None,
                                                        'description': 'Indicates this type is an enum. `enumValues` is a valid field.',
                                                        'isDeprecated': False,
                                                        'name': 'ENUM'},
                                                       {'deprecationReason': None,
                                                        'description': 'Indicates this type is an interface. `fields` and `possibleTypes` are valid fields.',
                                                        'isDeprecated': False,
                                                        'name': 'INTERFACE'},
                                                       {'deprecationReason': None,
                                                        'description': 'Indicates this type is a list. `ofType` is a valid field.',
                                                        'isDeprecated': False,
                                                        'name': 'LIST'}],
                                        'fields': None,
                                        'inputFields': None,
                                        'interfaces': None,
                                        'kind': 'ENUM',
                                        'name': '__TypeKind',
                                        'possibleTypes': None},
                                       {'description': None,
                                        'enumValues': None,
                                        'fields': None,
                                        'inputFields': None,
                                        'interfaces': None,
                                        'kind': 'SCALAR',
                                        'name': 'String',
                                        'possibleTypes': None},
                                       {'description': None,
                                        'enumValues': None,
                                        'fields': [{'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'possibleTypes',
                                                    'type': {'kind': 'LIST',
                                                             'name': None,
                                                             'ofType': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__Type',
                                                                                   'ofType': None}}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'description',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'kind',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'ENUM',
                                                                        'name': '__TypeKind',
                                                                        'ofType': None}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'ofType',
                                                    'type': {'kind': 'OBJECT',
                                                             'name': '__Type',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'inputFields',
                                                    'type': {'kind': 'LIST',
                                                             'name': None,
                                                             'ofType': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__InputValue',
                                                                                   'ofType': None}}}},
                                                   {'args': [{'defaultValue': 'false',
                                                              'description': None,
                                                              'name': 'includeDeprecated',
                                                              'type': {'kind': 'SCALAR',
                                                                       'name': 'Boolean',
                                                                       'ofType': None}}],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'enumValues',
                                                    'type': {'kind': 'LIST',
                                                             'name': None,
                                                             'ofType': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__EnumValue',
                                                                                   'ofType': None}}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'interfaces',
                                                    'type': {'kind': 'LIST',
                                                             'name': None,
                                                             'ofType': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__Type',
                                                                                   'ofType': None}}}},
                                                   {'args': [{'defaultValue': 'false',
                                                              'description': None,
                                                              'name': 'includeDeprecated',
                                                              'type': {'kind': 'SCALAR',
                                                                       'name': 'Boolean',
                                                                       'ofType': None}}],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'fields',
                                                    'type': {'kind': 'LIST',
                                                             'name': None,
                                                             'ofType': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__Field',
                                                                                   'ofType': None}}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'name',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}}],
                                        'inputFields': None,
                                        'interfaces': [],
                                        'kind': 'OBJECT',
                                        'name': '__Type',
                                        'possibleTypes': None},
                                       {'description': None,
                                        'enumValues': None,
                                        'fields': [],
                                        'inputFields': None,
                                        'interfaces': [],
                                        'kind': 'OBJECT',
                                        'name': 'QueryRoot',
                                        'possibleTypes': None},
                                       {'description': None,
                                        'enumValues': None,
                                        'fields': [{'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'defaultValue',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'description',
                                                    'type': {'kind': 'SCALAR',
                                                             'name': 'String',
                                                             'ofType': None}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'name',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}}},
                                                   {'args': [],
                                                    'deprecationReason': None,
                                                    'description': None,
                                                    'isDeprecated': False,
                                                    'name': 'type',
                                                    'type': {'kind': 'NON_NULL',
                                                             'name': None,
                                                             'ofType': {'kind': 'OBJECT',
                                                                        'name': '__Type',
                                                                        'ofType': None}}}],
                                        'inputFields': None,
                                        'interfaces': [],
                                        'kind': 'OBJECT',
                                        'name': '__InputValue',
                                        'possibleTypes': None},
                                       {
                                           'description': 'A GraphQL Schema defines the capabilities of a GraphQL server. It exposes all available types and directives on the server, as well as the entry points for query and mutation operations.',
                                           'enumValues': None,
                                           'fields': [{'args': [],
                                                       'deprecationReason': None,
                                                       'description': 'The type that query operations will be rooted at.',
                                                       'isDeprecated': False,
                                                       'name': 'queryType',
                                                       'type': {'kind': 'NON_NULL',
                                                                'name': None,
                                                                'ofType': {'kind': 'OBJECT',
                                                                           'name': '__Type',
                                                                           'ofType': None}}},
                                                      {'args': [],
                                                       'deprecationReason': None,
                                                       'description': 'A list of all directives supported by this server.',
                                                       'isDeprecated': False,
                                                       'name': 'directives',
                                                       'type': {'kind': 'NON_NULL',
                                                                'name': None,
                                                                'ofType': {'kind': 'LIST',
                                                                           'name': None,
                                                                           'ofType': {'kind': 'NON_NULL',
                                                                                      'name': None,
                                                                                      'ofType': {'kind': 'OBJECT',
                                                                                                 'name': '__Directive'}}}}},
                                                      {'args': [],
                                                       'deprecationReason': None,
                                                       'description': 'If this server supports mutation, the type that mutation operations will be rooted at.',
                                                       'isDeprecated': False,
                                                       'name': 'mutationType',
                                                       'type': {'kind': 'OBJECT',
                                                                'name': '__Type',
                                                                'ofType': None}},
                                                      {'args': [],
                                                       'deprecationReason': None,
                                                       'description': 'A list of all types supported by this server.',
                                                       'isDeprecated': False,
                                                       'name': 'types',
                                                       'type': {'kind': 'NON_NULL',
                                                                'name': None,
                                                                'ofType': {'kind': 'LIST',
                                                                           'name': None,
                                                                           'ofType': {'kind': 'NON_NULL',
                                                                                      'name': None,
                                                                                      'ofType': {'kind': 'OBJECT',
                                                                                                 'name': '__Type'}}}}}],
                                           'inputFields': None,
                                           'interfaces': [],
                                           'kind': 'OBJECT',
                                           'name': '__Schema',
                                           'possibleTypes': None}]}}

    assert sort_lists(result.data) == sort_lists(expected)


def test_introspects_on_input_object():
    TestInputObject = GraphQLInputObjectType('TestInputObject', {
        'a': GraphQLInputObjectField(GraphQLString, default_value='foo'),
        'b': GraphQLInputObjectField(GraphQLList(GraphQLString)),
    })
    TestType = GraphQLObjectType('TestType', {
        'field': GraphQLField(
            type=GraphQLString,
            args={'complex': GraphQLArgument(TestInputObject)},
            resolver=lambda obj, args, info: json.dumps(args.get('complex'))
        )
    })
    schema = GraphQLSchema(TestType)
    request = '''
      {
        __schema {
          types {
            kind
            name
            inputFields {
              name
              type { ...TypeRef }
              defaultValue
            }
          }
        }
      }
      fragment TypeRef on __Type {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
            }
          }
        }
      }
    '''
    result = graphql(schema, request)
    assert not result.errors
    assert sort_lists({'kind': 'INPUT_OBJECT',
                       'name': 'TestInputObject',
                       'inputFields':
                           [{'name': 'a',
                             'type':
                                 {'kind': 'SCALAR',
                                  'name': 'String',
                                  'ofType': None},
                             'defaultValue': '"foo"'},
                            {'name': 'b',
                             'type':
                                 {'kind': 'LIST',
                                  'name': None,
                                  'ofType':
                                      {'kind': 'SCALAR',
                                       'name': 'String',
                                       'ofType': None}},
                             'defaultValue': None}]}) in \
           sort_lists(result.data['__schema']['types'])


def test_supports_the_type_root_field():
    TestType = GraphQLObjectType('TestType', {
        'testField': GraphQLField(GraphQLString)
    })
    schema = GraphQLSchema(TestType)
    request = '{ __type(name: "TestType") { name } }'
    result = execute(schema, object(), parse(request))
    assert not result.errors
    assert result.data == {'__type': {'name': 'TestType'}}


def test_identifies_deprecated_fields():
    TestType = GraphQLObjectType('TestType', {
        'nonDeprecated': GraphQLField(GraphQLString),
        'deprecated': GraphQLField(GraphQLString,
                                   deprecation_reason='Removed in 1.0')
    })
    schema = GraphQLSchema(TestType)
    request = '''{__type(name: "TestType") {
        name
        fields(includeDeprecated: true) {
            name
            isDeprecated
            deprecationReason
        }
    } }'''
    result = graphql(schema, request)
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({'__type': {
        'name': 'TestType',
        'fields': [
            {'name': 'nonDeprecated', 'isDeprecated': False, 'deprecationReason': None},
            {'name': 'deprecated', 'isDeprecated': True,
             'deprecationReason': 'Removed in 1.0'},
        ]
    }})


def test_respects_the_includedeprecated_parameter_for_fields():
    TestType = GraphQLObjectType('TestType', {
        'nonDeprecated': GraphQLField(GraphQLString),
        'deprecated': GraphQLField(GraphQLString,
                                   deprecation_reason='Removed in 1.0')
    })
    schema = GraphQLSchema(TestType)
    request = '''{__type(name: "TestType") {
        name
        trueFields: fields(includeDeprecated: true) { name }
        falseFields: fields(includeDeprecated: false) { name }
        omittedFields: fields { name }
    } }'''
    result = graphql(schema, request)
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({'__type': {
        'name': 'TestType',
        'trueFields': [{'name': 'nonDeprecated'}, {'name': 'deprecated'}],
        'falseFields': [{'name': 'nonDeprecated'}],
        'omittedFields': [{'name': 'nonDeprecated'}],
    }})


def test_identifies_deprecated_enum_values():
    TestEnum = GraphQLEnumType('TestEnum', {
        'NONDEPRECATED': 0,
        'DEPRECATED': GraphQLEnumValue(1, deprecation_reason='Removed in 1.0'),
        'ALSONONDEPRECATED': 2
    })
    TestType = GraphQLObjectType('TestType', {
        'testEnum': GraphQLField(TestEnum)
    })
    schema = GraphQLSchema(TestType)
    request = '''{__type(name: "TestEnum") {
        name
        enumValues(includeDeprecated: true) {
            name
            isDeprecated
            deprecationReason
        }
    } }'''
    result = graphql(schema, request)
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({'__type': {
        'name': 'TestEnum',
        'enumValues': [
            {'name': 'NONDEPRECATED', 'isDeprecated': False, 'deprecationReason': None},
            {'name': 'DEPRECATED', 'isDeprecated': True, 'deprecationReason': 'Removed in 1.0'},
            {'name': 'ALSONONDEPRECATED', 'isDeprecated': False, 'deprecationReason': None},
        ]}})


def test_respects_the_includedeprecated_parameter_for_enum_values():
    TestEnum = GraphQLEnumType('TestEnum', {
        'NONDEPRECATED': 0,
        'DEPRECATED': GraphQLEnumValue(1, deprecation_reason='Removed in 1.0'),
        'ALSONONDEPRECATED': 2
    })
    TestType = GraphQLObjectType('TestType', {
        'testEnum': GraphQLField(TestEnum)
    })
    schema = GraphQLSchema(TestType)
    request = '''{__type(name: "TestEnum") {
        name
        trueValues: enumValues(includeDeprecated: true) { name }
        falseValues: enumValues(includeDeprecated: false) { name }
        omittedValues: enumValues { name }
    } }'''
    result = graphql(schema, request)
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({'__type': {
        'name': 'TestEnum',
        'trueValues': [{'name': 'NONDEPRECATED'}, {'name': 'DEPRECATED'},
                       {'name': 'ALSONONDEPRECATED'}],
        'falseValues': [{'name': 'NONDEPRECATED'},
                        {'name': 'ALSONONDEPRECATED'}],
        'omittedValues': [{'name': 'NONDEPRECATED'},
                          {'name': 'ALSONONDEPRECATED'}],
    }})


def test_fails_as_expected_on_the_type_root_field_without_an_arg():
    TestType = GraphQLObjectType('TestType', {
        'testField': GraphQLField(GraphQLString)
    })
    schema = GraphQLSchema(TestType)
    request = '''
    {
        __type {
           name
        }
    }'''
    result = graphql(schema, request)
    expected_error = {'message': ProvidedNonNullArguments.missing_field_arg_message('__type', 'name', 'String!'),
                      'locations': [dict(line=3, column=9)]}
    assert (expected_error in [format_error(error) for error in result.errors])


def test_exposes_descriptions_on_types_and_fields():
    QueryRoot = GraphQLObjectType('QueryRoot', {})
    schema = GraphQLSchema(QueryRoot)
    request = '''{
      schemaType: __type(name: "__Schema") {
          name,
          description,
          fields {
            name,
            description
          }
        }
      }
    '''
    result = graphql(schema, request)
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({'schemaType': {
        'name': '__Schema',
        'description': 'A GraphQL Schema defines the capabilities of a ' +
                       'GraphQL server. It exposes all available types and ' +
                       'directives on the server, as well as the entry ' +
                       'points for query and mutation operations.',
        'fields': [
            {
                'name': 'types',
                'description': 'A list of all types supported by this server.'
            },
            {
                'name': 'queryType',
                'description': 'The type that query operations will be rooted at.'
            },
            {
                'name': 'mutationType',
                'description': 'If this server supports mutation, the type that ' +
                               'mutation operations will be rooted at.'
            },
            {
                'name': 'directives',
                'description': 'A list of all directives supported by this server.'
            }
        ]
    }})


def test_exposes_descriptions_on_enums():
    QueryRoot = GraphQLObjectType('QueryRoot', {})
    schema = GraphQLSchema(QueryRoot)
    request = '''{
      typeKindType: __type(name: "__TypeKind") {
          name,
          description,
          enumValues {
            name,
            description
          }
        }
      }
    '''
    result = graphql(schema, request)
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({'typeKindType': {
        'name': '__TypeKind',
        'description': 'An enum describing what kind of type a given __Type is',
        'enumValues': [
            {
                'description': 'Indicates this type is a scalar.',
                'name': 'SCALAR'
            },
            {
                'description': 'Indicates this type is an object. ' +
                               '`fields` and `interfaces` are valid fields.',
                'name': 'OBJECT'
            },
            {
                'description': 'Indicates this type is an interface. ' +
                               '`fields` and `possibleTypes` are valid fields.',
                'name': 'INTERFACE'
            },
            {
                'description': 'Indicates this type is a union. ' +
                               '`possibleTypes` is a valid field.',
                'name': 'UNION'
            },
            {
                'description': 'Indicates this type is an enum. ' +
                               '`enumValues` is a valid field.',
                'name': 'ENUM'
            },
            {
                'description': 'Indicates this type is an input object. ' +
                               '`inputFields` is a valid field.',
                'name': 'INPUT_OBJECT'
            },
            {
                'description': 'Indicates this type is a list. ' +
                               '`ofType` is a valid field.',
                'name': 'LIST'
            },
            {
                'description': 'Indicates this type is a non-null. ' +
                               '`ofType` is a valid field.',
                'name': 'NON_NULL'
            }
        ]
    }})
