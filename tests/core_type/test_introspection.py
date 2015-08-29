import json
from graphql.core import graphql
from graphql.core.language.parser import parse
from graphql.core.executor import execute
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

introspection_query = '''
  query IntrospectionQuery {
    __schema {
      queryType { name }
      mutationType { name }
      types {
        ...FullType
      }
      directives {
        name
        args {
          name
          type { ...TypeRef }
          defaultValue
        }
        onOperation
        onFragment
        onField
      }
    }
  }
  fragment FullType on __Type {
    kind
    name
    fields {
      name
      args {
        name
        type { ...TypeRef }
        defaultValue
      }
      type {
        ...TypeRef
      }
      isDeprecated
      deprecationReason
    }
    inputFields {
      name
      type { ...TypeRef }
      defaultValue
    }
    interfaces {
      ...TypeRef
    }
    enumValues {
      name
      isDeprecated
      deprecationReason
    }
    possibleTypes {
      ...TypeRef
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


def sort_lists(value):
    if isinstance(value, dict):
        new_mapping = {}
        for k, v in value.iteritems():
            new_mapping[k] = sort_lists(v)
        return new_mapping
    elif isinstance(value, list):
        return sorted(map(sort_lists, value))
    return value


def test_executes_an_introspection_query():
    EmptySchema = GraphQLSchema(GraphQLObjectType('QueryRoot', {}))

    result = graphql(EmptySchema, introspection_query)
    assert not result.errors
    assert sort_lists(result.data) == sort_lists({'__schema': {'directives': [{'args': [{'defaultValue': None,
                                                                  'name': 'if',
                                                                  'type': {'kind': 'NON_NULL',
                                                                           'name': None,
                                                                           'ofType': {'kind': 'SCALAR',
                                                                                      'name': 'Boolean',
                                                                                      'ofType': None}}}],
                                                        'name': 'include',
                                                        'onField': True,
                                                        'onFragment': True,
                                                        'onOperation': False},
                                                       {'args': [{'defaultValue': None,
                                                                  'name': 'if',
                                                                  'type': {'kind': 'NON_NULL',
                                                                           'name': None,
                                                                           'ofType': {'kind': 'SCALAR',
                                                                                      'name': 'Boolean',
                                                                                      'ofType': None}}}],
                                                        'name': 'skip',
                                                        'onField': True,
                                                        'onFragment': True,
                                                        'onOperation': False}],
                                        'mutationType': None,
                                        'queryType': {'name': 'QueryRoot'},
                                        'types': [{'enumValues': None,
                                                   'fields': [],
                                                   'inputFields': None,
                                                   'interfaces': [],
                                                   'kind': 'OBJECT',
                                                   'name': 'QueryRoot',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': [{'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'types',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'LIST',
                                                                                   'name': None,
                                                                                   'ofType': {'kind': 'NON_NULL',
                                                                                              'name': None,
                                                                                              'ofType': {'kind': 'OBJECT',
                                                                                                         'name': '__Type'}}}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'queryType',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__Type',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'mutationType',
                                                               'type': {'kind': 'OBJECT',
                                                                        'name': '__Type',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'directives',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'LIST',
                                                                                   'name': None,
                                                                                   'ofType': {'kind': 'NON_NULL',
                                                                                              'name': None,
                                                                                              'ofType': {'kind': 'OBJECT',
                                                                                                         'name': '__Directive'}}}}}],
                                                   'inputFields': None,
                                                   'interfaces': [],
                                                   'kind': 'OBJECT',
                                                   'name': '__Schema',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': [{'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'kind',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'ENUM',
                                                                                   'name': '__TypeKind',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'name',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'description',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}},
                                                              {'args': [{'defaultValue': 'false',
                                                                         'name': 'includeDeprecated',
                                                                         'type': {'kind': 'SCALAR',
                                                                                  'name': 'Boolean',
                                                                                  'ofType': None}}],
                                                               'deprecationReason': None,
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
                                                               'isDeprecated': False,
                                                               'name': 'interfaces',
                                                               'type': {'kind': 'LIST',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'NON_NULL',
                                                                                   'name': None,
                                                                                   'ofType': {'kind': 'OBJECT',
                                                                                              'name': '__Type',
                                                                                              'ofType': None}}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'possibleTypes',
                                                               'type': {'kind': 'LIST',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'NON_NULL',
                                                                                   'name': None,
                                                                                   'ofType': {'kind': 'OBJECT',
                                                                                              'name': '__Type',
                                                                                              'ofType': None}}}},
                                                              {'args': [{'defaultValue': 'false',
                                                                         'name': 'includeDeprecated',
                                                                         'type': {'kind': 'SCALAR',
                                                                                  'name': 'Boolean',
                                                                                  'ofType': None}}],
                                                               'deprecationReason': None,
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
                                                               'isDeprecated': False,
                                                               'name': 'inputFields',
                                                               'type': {'kind': 'LIST',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'NON_NULL',
                                                                                   'name': None,
                                                                                   'ofType': {'kind': 'OBJECT',
                                                                                              'name': '__InputValue',
                                                                                              'ofType': None}}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'ofType',
                                                               'type': {'kind': 'OBJECT',
                                                                        'name': '__Type',
                                                                        'ofType': None}}],
                                                   'inputFields': None,
                                                   'interfaces': [],
                                                   'kind': 'OBJECT',
                                                   'name': '__Type',
                                                   'possibleTypes': None},
                                                  {'enumValues': [{'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'SCALAR'},
                                                                  {'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'OBJECT'},
                                                                  {'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'INTERFACE'},
                                                                  {'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'UNION'},
                                                                  {'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'ENUM'},
                                                                  {'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'INPUT_OBJECT'},
                                                                  {'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'LIST'},
                                                                  {'deprecationReason': None,
                                                                   'isDeprecated': False,
                                                                   'name': 'NON_NULL'}],
                                                   'fields': None,
                                                   'inputFields': None,
                                                   'interfaces': None,
                                                   'kind': 'ENUM',
                                                   'name': '__TypeKind',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': None,
                                                   'inputFields': None,
                                                   'interfaces': None,
                                                   'kind': 'SCALAR',
                                                   'name': 'String',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': None,
                                                   'inputFields': None,
                                                   'interfaces': None,
                                                   'kind': 'SCALAR',
                                                   'name': 'Boolean',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': [{'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'name',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'SCALAR',
                                                                                   'name': 'String',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'description',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
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
                                                               'isDeprecated': False,
                                                               'name': 'type',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__Type',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'isDeprecated',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'SCALAR',
                                                                                   'name': 'Boolean',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'deprecationReason',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}}],
                                                   'inputFields': None,
                                                   'interfaces': [],
                                                   'kind': 'OBJECT',
                                                   'name': '__Field',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': [{'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'name',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'SCALAR',
                                                                                   'name': 'String',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'description',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'type',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'OBJECT',
                                                                                   'name': '__Type',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'defaultValue',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}}],
                                                   'inputFields': None,
                                                   'interfaces': [],
                                                   'kind': 'OBJECT',
                                                   'name': '__InputValue',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': [{'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'name',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'SCALAR',
                                                                                   'name': 'String',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'description',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'isDeprecated',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'SCALAR',
                                                                                   'name': 'Boolean',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'deprecationReason',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}}],
                                                   'inputFields': None,
                                                   'interfaces': [],
                                                   'kind': 'OBJECT',
                                                   'name': '__EnumValue',
                                                   'possibleTypes': None},
                                                  {'enumValues': None,
                                                   'fields': [{'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'name',
                                                               'type': {'kind': 'NON_NULL',
                                                                        'name': None,
                                                                        'ofType': {'kind': 'SCALAR',
                                                                                   'name': 'String',
                                                                                   'ofType': None}}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'description',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'String',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
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
                                                               'isDeprecated': False,
                                                               'name': 'onOperation',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'Boolean',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'onFragment',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'Boolean',
                                                                        'ofType': None}},
                                                              {'args': [],
                                                               'deprecationReason': None,
                                                               'isDeprecated': False,
                                                               'name': 'onField',
                                                               'type': {'kind': 'SCALAR',
                                                                        'name': 'Boolean',
                                                                        'ofType': None}}],
                                                   'inputFields': None,
                                                   'interfaces': [],
                                                   'kind': 'OBJECT',
                                                   'name': '__Directive',
                                                   'possibleTypes': None}]}})


def test_introspects_on_input_object():
    TestInputObject = GraphQLInputObjectType('TestInputObject', {
        'a': GraphQLInputObjectField(GraphQLString, default_value='foo'),
        'b': GraphQLInputObjectField(GraphQLList(GraphQLString)),
    })
    TestType = GraphQLObjectType('TestType', {
        'field': GraphQLField(
            type=GraphQLString,
            args={'complex': GraphQLArgument(TestInputObject)},
            resolver=lambda obj, args, *_: json.dumps(args.get('complex'))
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
    request = '{ __type { name } }'
    result = graphql(schema, request)
    # TODO: change after implementing validation
    assert not result.errors


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
