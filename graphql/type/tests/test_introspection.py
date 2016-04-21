import json
from collections import OrderedDict

from graphql import graphql
from graphql.error import format_error
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (GraphQLArgument, GraphQLEnumType, GraphQLEnumValue,
                          GraphQLField, GraphQLInputObjectField,
                          GraphQLInputObjectType, GraphQLList,
                          GraphQLObjectType, GraphQLSchema, GraphQLString)
from graphql.utils.introspection_query import introspection_query
from graphql.validation.rules import ProvidedNonNullArguments


def test_executes_an_introspection_query():
    EmptySchema = GraphQLSchema(GraphQLObjectType('QueryRoot', {'f': GraphQLField(GraphQLString)}))

    result = graphql(EmptySchema, introspection_query)
    assert not result.errors
    expected = {
        '__schema': {'directives': [{'args': [{'defaultValue': None,
                                               'description': u'Directs the executor to include this field or fragment only when the `if` argument is true.',
                                               'name': u'if',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'Boolean',
                                                                   'ofType': None}}}],
                                     'description': None,
                                     'name': u'include',
                                     'onField': True,
                                     'onFragment': True,
                                     'onOperation': False},
                                    {'args': [{'defaultValue': None,
                                               'description': u'Directs the executor to skip this field or fragment only when the `if` argument is true.',
                                               'name': u'if',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'Boolean',
                                                                   'ofType': None}}}],
                                     'description': None,
                                     'name': u'skip',
                                     'onField': True,
                                     'onFragment': True,
                                     'onOperation': False}],
                     'mutationType': None,
                     'queryType': {'name': u'QueryRoot'},
                     'subscriptionType': None,
                     'types': [{'description': None,
                                'enumValues': None,
                                'fields': [{'args': [],
                                            'deprecationReason': None,
                                            'description': None,
                                            'isDeprecated': False,
                                            'name': u'f',
                                            'type': {'kind': 'SCALAR',
                                                     'name': u'String',
                                                     'ofType': None}}],
                                'inputFields': None,
                                'interfaces': [],
                                'kind': 'OBJECT',
                                'name': u'QueryRoot',
                                'possibleTypes': None},
                               {
                                   'description': u'The `String` scalar type represents textual data, represented as UTF-8 character sequences. The String type is most often used by GraphQL to represent free-form human-readable text.',
                                   'enumValues': None,
                                   'fields': None,
                                   'inputFields': None,
                                   'interfaces': None,
                                   'kind': 'SCALAR',
                                   'name': u'String',
                                   'possibleTypes': None},
                               {
                                   'description': u'A GraphQL Schema defines the capabilities of a GraphQL server. It exposes all available types and directives on the server, as well as the entry points for query, mutation and subscription operations.',
                                   'enumValues': None,
                                   'fields': [{'args': [],
                                               'deprecationReason': None,
                                               'description': u'A list of all types supported by this server.',
                                               'isDeprecated': False,
                                               'name': u'types',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'LIST',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'NON_NULL',
                                                                              'name': None,
                                                                              'ofType': {'kind': 'OBJECT',
                                                                                         'name': u'__Type'}}}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': u'The type that query operations will be rooted at.',
                                               'isDeprecated': False,
                                               'name': u'queryType',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'OBJECT',
                                                                   'name': u'__Type',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': u'If this server supports mutation, the type that mutation operations will be rooted at.',
                                               'isDeprecated': False,
                                               'name': u'mutationType',
                                               'type': {'kind': 'OBJECT',
                                                        'name': u'__Type',
                                                        'ofType': None}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': u'If this server support subscription, the type that subscription operations will be rooted at.',
                                               'isDeprecated': False,
                                               'name': u'subscriptionType',
                                               'type': {'kind': 'OBJECT',
                                                        'name': u'__Type',
                                                        'ofType': None}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': u'A list of all directives supported by this server.',
                                               'isDeprecated': False,
                                               'name': u'directives',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'LIST',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'NON_NULL',
                                                                              'name': None,
                                                                              'ofType': {'kind': 'OBJECT',
                                                                                         'name': u'__Directive'}}}}}],
                                   'inputFields': None,
                                   'interfaces': [],
                                   'kind': 'OBJECT',
                                   'name': u'__Schema',
                                   'possibleTypes': None},
                               {
                                   'description': u'The fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the `__TypeKind` enum.\n\nDepending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.',
                                   'enumValues': None,
                                   'fields': [{'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'kind',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'ENUM',
                                                                   'name': u'__TypeKind',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'name',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'description',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}},
                                              {'args': [{'defaultValue': u'false',
                                                         'description': None,
                                                         'name': u'includeDeprecated',
                                                         'type': {'kind': 'SCALAR',
                                                                  'name': u'Boolean',
                                                                  'ofType': None}}],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'fields',
                                               'type': {'kind': 'LIST',
                                                        'name': None,
                                                        'ofType': {'kind': 'NON_NULL',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'OBJECT',
                                                                              'name': u'__Field',
                                                                              'ofType': None}}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'interfaces',
                                               'type': {'kind': 'LIST',
                                                        'name': None,
                                                        'ofType': {'kind': 'NON_NULL',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'OBJECT',
                                                                              'name': u'__Type',
                                                                              'ofType': None}}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'possibleTypes',
                                               'type': {'kind': 'LIST',
                                                        'name': None,
                                                        'ofType': {'kind': 'NON_NULL',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'OBJECT',
                                                                              'name': u'__Type',
                                                                              'ofType': None}}}},
                                              {'args': [{'defaultValue': u'false',
                                                         'description': None,
                                                         'name': u'includeDeprecated',
                                                         'type': {'kind': 'SCALAR',
                                                                  'name': u'Boolean',
                                                                  'ofType': None}}],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'enumValues',
                                               'type': {'kind': 'LIST',
                                                        'name': None,
                                                        'ofType': {'kind': 'NON_NULL',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'OBJECT',
                                                                              'name': u'__EnumValue',
                                                                              'ofType': None}}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'inputFields',
                                               'type': {'kind': 'LIST',
                                                        'name': None,
                                                        'ofType': {'kind': 'NON_NULL',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'OBJECT',
                                                                              'name': u'__InputValue',
                                                                              'ofType': None}}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'ofType',
                                               'type': {'kind': 'OBJECT',
                                                        'name': u'__Type',
                                                        'ofType': None}}],
                                   'inputFields': None,
                                   'interfaces': [],
                                   'kind': 'OBJECT',
                                   'name': u'__Type',
                                   'possibleTypes': None},
                               {'description': u'An enum describing what kind of type a given `__Type` is',
                                'enumValues': [{'deprecationReason': None,
                                                'description': u'Indicates this type is a scalar.',
                                                'isDeprecated': False,
                                                'name': u'SCALAR'},
                                               {'deprecationReason': None,
                                                'description': u'Indicates this type is an object. `fields` and `interfaces` are valid fields.',
                                                'isDeprecated': False,
                                                'name': u'OBJECT'},
                                               {'deprecationReason': None,
                                                'description': u'Indicates this type is an interface. `fields` and `possibleTypes` are valid fields.',
                                                'isDeprecated': False,
                                                'name': u'INTERFACE'},
                                               {'deprecationReason': None,
                                                'description': u'Indicates this type is a union. `possibleTypes` is a valid field.',
                                                'isDeprecated': False,
                                                'name': u'UNION'},
                                               {'deprecationReason': None,
                                                'description': u'Indicates this type is an enum. `enumValues` is a valid field.',
                                                'isDeprecated': False,
                                                'name': u'ENUM'},
                                               {'deprecationReason': None,
                                                'description': u'Indicates this type is an input object. `inputFields` is a valid field.',
                                                'isDeprecated': False,
                                                'name': u'INPUT_OBJECT'},
                                               {'deprecationReason': None,
                                                'description': u'Indicates this type is a list. `ofType` is a valid field.',
                                                'isDeprecated': False,
                                                'name': u'LIST'},
                                               {'deprecationReason': None,
                                                'description': u'Indicates this type is a non-null. `ofType` is a valid field.',
                                                'isDeprecated': False,
                                                'name': u'NON_NULL'}],
                                'fields': None,
                                'inputFields': None,
                                'interfaces': None,
                                'kind': 'ENUM',
                                'name': u'__TypeKind',
                                'possibleTypes': None},
                               {'description': u'The `Boolean` scalar type represents `true` or `false`.',
                                'enumValues': None,
                                'fields': None,
                                'inputFields': None,
                                'interfaces': None,
                                'kind': 'SCALAR',
                                'name': u'Boolean',
                                'possibleTypes': None},
                               {
                                   'description': u'Object and Interface types are described by a list of Fields, each of which has a name, potentially a list of arguments, and a return type.',
                                   'enumValues': None,
                                   'fields': [{'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'name',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'String',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'description',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'args',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'LIST',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'NON_NULL',
                                                                              'name': None,
                                                                              'ofType': {'kind': 'OBJECT',
                                                                                         'name': u'__InputValue'}}}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'type',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'OBJECT',
                                                                   'name': u'__Type',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'isDeprecated',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'Boolean',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'deprecationReason',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}}],
                                   'inputFields': None,
                                   'interfaces': [],
                                   'kind': 'OBJECT',
                                   'name': u'__Field',
                                   'possibleTypes': None},
                               {
                                   'description': u'Arguments provided to Fields or Directives and the input fields of an InputObject are represented as Input Values which describe their type and optionally a default value.',
                                   'enumValues': None,
                                   'fields': [{'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'name',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'String',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'description',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'type',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'OBJECT',
                                                                   'name': u'__Type',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'defaultValue',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}}],
                                   'inputFields': None,
                                   'interfaces': [],
                                   'kind': 'OBJECT',
                                   'name': u'__InputValue',
                                   'possibleTypes': None},
                               {
                                   'description': u'One possible value for a given Enum. Enum values are unique values, not a placeholder for a string or numeric value. However an Enum value is returned in a JSON response as a string.',
                                   'enumValues': None,
                                   'fields': [{'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'name',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'String',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'description',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'isDeprecated',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'Boolean',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'deprecationReason',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}}],
                                   'inputFields': None,
                                   'interfaces': [],
                                   'kind': 'OBJECT',
                                   'name': u'__EnumValue',
                                   'possibleTypes': None},
                               {
                                   'description': u"A Directive provides a way to describe alternate runtime execution and type validation behavior in a GraphQL document.\n\nIn some cases, you need to provide options to alter GraphQL's execution behavior in ways field arguments will not suffice, such as conditionally including or skipping a field. Directives provide this by describing additional information to the executor.",
                                   'enumValues': None,
                                   'fields': [{'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'name',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'String',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'description',
                                               'type': {'kind': 'SCALAR',
                                                        'name': u'String',
                                                        'ofType': None}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'args',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'LIST',
                                                                   'name': None,
                                                                   'ofType': {'kind': 'NON_NULL',
                                                                              'name': None,
                                                                              'ofType': {'kind': 'OBJECT',
                                                                                         'name': u'__InputValue'}}}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'onOperation',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'Boolean',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'onFragment',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'Boolean',
                                                                   'ofType': None}}},
                                              {'args': [],
                                               'deprecationReason': None,
                                               'description': None,
                                               'isDeprecated': False,
                                               'name': u'onField',
                                               'type': {'kind': 'NON_NULL',
                                                        'name': None,
                                                        'ofType': {'kind': 'SCALAR',
                                                                   'name': u'Boolean',
                                                                   'ofType': None}}}],
                                   'inputFields': None,
                                   'interfaces': [],
                                   'kind': 'OBJECT',
                                   'name': u'__Directive',
                                   'possibleTypes': None}]}}
    assert result.data == expected


def test_introspects_on_input_object():
    TestInputObject = GraphQLInputObjectType('TestInputObject', OrderedDict([
        ('a', GraphQLInputObjectField(GraphQLString, default_value='foo')),
        ('b', GraphQLInputObjectField(GraphQLList(GraphQLString)))
    ]))
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
    assert {'kind': 'INPUT_OBJECT',
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
                  'defaultValue': None}]} in result.data['__schema']['types']


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
    TestType = GraphQLObjectType('TestType', OrderedDict([
        ('nonDeprecated', GraphQLField(GraphQLString)),
        ('deprecated', GraphQLField(GraphQLString, deprecation_reason='Removed in 1.0'))
    ]))
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
    assert result.data == {'__type': {
        'name': 'TestType',
        'fields': [
            {'name': 'nonDeprecated', 'isDeprecated': False, 'deprecationReason': None},
            {'name': 'deprecated', 'isDeprecated': True,
             'deprecationReason': 'Removed in 1.0'},
        ]
    }}


def test_respects_the_includedeprecated_parameter_for_fields():
    TestType = GraphQLObjectType('TestType', OrderedDict([
        ('nonDeprecated', GraphQLField(GraphQLString)),
        ('deprecated', GraphQLField(GraphQLString, deprecation_reason='Removed in 1.0'))
    ]))
    schema = GraphQLSchema(TestType)
    request = '''{__type(name: "TestType") {
        name
        trueFields: fields(includeDeprecated: true) { name }
        falseFields: fields(includeDeprecated: false) { name }
        omittedFields: fields { name }
    } }'''
    result = graphql(schema, request)
    assert not result.errors
    assert result.data == {'__type': {
        'name': 'TestType',
        'trueFields': [{'name': 'nonDeprecated'}, {'name': 'deprecated'}],
        'falseFields': [{'name': 'nonDeprecated'}],
        'omittedFields': [{'name': 'nonDeprecated'}],
    }}


def test_identifies_deprecated_enum_values():
    TestEnum = GraphQLEnumType('TestEnum', OrderedDict([
        ('NONDEPRECATED', GraphQLEnumValue(0)),
        ('DEPRECATED', GraphQLEnumValue(1, deprecation_reason='Removed in 1.0')),
        ('ALSONONDEPRECATED', GraphQLEnumValue(2))
    ]))
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
    assert result.data == {'__type': {
        'name': 'TestEnum',
        'enumValues': [
            {'name': 'NONDEPRECATED', 'isDeprecated': False, 'deprecationReason': None},
            {'name': 'DEPRECATED', 'isDeprecated': True, 'deprecationReason': 'Removed in 1.0'},
            {'name': 'ALSONONDEPRECATED', 'isDeprecated': False, 'deprecationReason': None},
        ]}}


def test_respects_the_includedeprecated_parameter_for_enum_values():
    TestEnum = GraphQLEnumType('TestEnum', OrderedDict([
        ('NONDEPRECATED', GraphQLEnumValue(0)),
        ('DEPRECATED', GraphQLEnumValue(1, deprecation_reason='Removed in 1.0')),
        ('ALSONONDEPRECATED', GraphQLEnumValue(2))
    ]))
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
    assert result.data == {'__type': {
        'name': 'TestEnum',
        'trueValues': [{'name': 'NONDEPRECATED'}, {'name': 'DEPRECATED'},
                       {'name': 'ALSONONDEPRECATED'}],
        'falseValues': [{'name': 'NONDEPRECATED'},
                        {'name': 'ALSONONDEPRECATED'}],
        'omittedValues': [{'name': 'NONDEPRECATED'},
                          {'name': 'ALSONONDEPRECATED'}],
    }}


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
    QueryRoot = GraphQLObjectType('QueryRoot', {'f': GraphQLField(GraphQLString)})
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
    assert result.data == {'schemaType': {
        'name': '__Schema',
        'description': 'A GraphQL Schema defines the capabilities of a ' +
                       'GraphQL server. It exposes all available types and ' +
                       'directives on the server, as well as the entry ' +
                       'points for query, mutation and subscription operations.',
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
                'description': 'If this server supports mutation, the type that '
                               'mutation operations will be rooted at.'
            },
            {
                'name': 'subscriptionType',
                'description': 'If this server support subscription, the type '
                               'that subscription operations will be rooted at.'
            },
            {
                'name': 'directives',
                'description': 'A list of all directives supported by this server.'
            }
        ]
    }}


def test_exposes_descriptions_on_enums():
    QueryRoot = GraphQLObjectType('QueryRoot', {'f': GraphQLField(GraphQLString)})
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
    assert result.data == {'typeKindType': {
        'name': '__TypeKind',
        'description': 'An enum describing what kind of type a given `__Type` is',
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
    }}
