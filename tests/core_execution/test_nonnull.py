from graphql.core.language.parser import parse
from graphql.core.type import GraphQLObjectType, GraphQLField, GraphQLString, GraphQLNonNull, GraphQLSchema
from graphql.core.execution import execute

sync_error = Exception('sync')
non_null_sync_error = Exception('nonNullSync')


class ThrowingData(object):
    def sync(self):
        raise sync_error

    def nonNullSync(self):
        raise non_null_sync_error

    def nest(self):
        return ThrowingData()

    def nonNullNest(self):
        return ThrowingData()


class NullingData(object):
    def sync(self):
        return None

    def nonNullSync(self):
        return None

    def nest(self):
        return NullingData()

    def nonNullNest(self):
        return NullingData()


DataType = GraphQLObjectType('DataType', lambda: {
    'sync': GraphQLField(GraphQLString),
    'nonNullSync': GraphQLField(GraphQLNonNull(GraphQLString)),
    'nest': GraphQLField(DataType),
    'nonNullNest': GraphQLField(GraphQLNonNull(DataType)),
})

schema = GraphQLSchema(DataType)


def test_nulls_a_nullable_field_that_throws_sync():
    doc = '''
        query Q {
            sync
        }
    '''
    ast = parse(doc)
    result = execute(schema, ThrowingData(), ast, 'Q', {})
    assert len(result.errors) == 1
    # TODO: check error location
    assert result.errors[0]['message'] == sync_error.message
    assert result.data == {
        'sync': None
    }


def test_nulls_a_sync_returned_object_that_contains_a_non_nullable_field_that_throws():
    doc = '''
        query Q {
            nest {
                nonNullSync,
            }
        }
    '''
    ast = parse(doc)
    result = execute(schema, ThrowingData(), ast, 'Q', {})
    assert len(result.errors) == 1
    # TODO: check error location
    assert result.errors[0]['message'] == non_null_sync_error.message
    assert result.data == {
        'nest': None
    }


def test_nulls_a_complex_tree_of_nullable_fields_that_throw():
    doc = '''
      query Q {
        nest {
          sync
          #promise
          nest {
            sync
            #promise
          }
          #promiseNest {
          #  sync
          #  promise
          #}
        }
        #promiseNest {
        #  sync
        #  promise
        #  nest {
        #    sync
        #    promise
        #  }
        #  promiseNest {
        #    sync
        #    promise
        #  }
        #}
      }
    '''
    ast = parse(doc)
    result = execute(schema, ThrowingData(), ast, 'Q', {})
    assert len(result.errors) == 2
    # TODO: check error location
    assert result.errors[0]['message'] == sync_error.message
    assert result.errors[1]['message'] == sync_error.message
    assert result.data == {
        'nest': {
            'sync': None,
            'nest': {
                'sync': None
            }
        }
    }


def test_nulls_a_nullable_field_that_returns_null():
    doc = '''
        query Q {
            sync
        }
    '''
    ast = parse(doc)
    result = execute(schema, NullingData(), ast, 'Q', {})
    assert not result.errors
    assert result.data == {
        'sync': None
    }


def test_nulls_a_sync_returned_object_that_contains_a_non_nullable_field_that_returns_null():
    doc = '''
        query Q {
            nest {
                nonNullSync,
            }
        }
    '''
    ast = parse(doc)
    result = execute(schema, NullingData(), ast, 'Q', {})
    assert len(result.errors) == 1
    # TODO: check error location
    assert result.errors[0]['message'] == 'Cannot return null for non-nullable type.'
    assert result.data == {
        'nest': None
    }


def test_nulls_a_complex_tree_of_nullable_fields_that_returns_null():
    doc = '''
      query Q {
        nest {
          sync
          #promise
          nest {
            sync
            #promise
          }
          #promiseNest {
          #  sync
          #  promise
          #}
        }
        #promiseNest {
        #  sync
        #  promise
        #  nest {
        #    sync
        #    promise
        #  }
        #  promiseNest {
        #    sync
        #    promise
        #  }
        #}
      }
    '''
    ast = parse(doc)
    result = execute(schema, NullingData(), ast, 'Q', {})
    assert not result.errors
    assert result.data == {
        'nest': {
            'sync': None,
            'nest': {
                'sync': None
            }
        }
    }


def test_nulls_the_top_level_if_sync_non_nullable_field_throws():
    doc = '''
        query Q { nonNullSync }
    '''
    ast = parse(doc)
    result = execute(schema, ThrowingData(), ast)
    assert result.data is None
    assert len(result.errors) == 1
    # TODO: check error location
    assert result.errors[0]['message'] == non_null_sync_error.message


def test_nulls_the_top_level_if_sync_non_nullable_field_returns_null():
    doc = '''
        query Q { nonNullSync }
    '''
    ast = parse(doc)
    result = execute(schema, NullingData(), ast)
    assert result.data is None
    assert len(result.errors) == 1
    # TODO: check error location
    assert result.errors[0]['message'] == 'Cannot return null for non-nullable type.'
