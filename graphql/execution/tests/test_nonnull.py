
from graphql.error import format_error
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (GraphQLField, GraphQLNonNull, GraphQLObjectType,
                          GraphQLSchema, GraphQLString)

from .utils import rejected, resolved

sync_error = Exception('sync')
non_null_sync_error = Exception('nonNullSync')
promise_error = Exception('promise')
non_null_promise_error = Exception('nonNullPromise')


class ThrowingData(object):

    def sync(self):
        raise sync_error

    def nonNullSync(self):
        raise non_null_sync_error

    def promise(self):
        return rejected(promise_error)

    def nonNullPromise(self):
        return rejected(non_null_promise_error)

    def nest(self):
        return ThrowingData()

    def nonNullNest(self):
        return ThrowingData()

    def promiseNest(self):
        return resolved(ThrowingData())

    def nonNullPromiseNest(self):
        return resolved(ThrowingData())


class NullingData(object):

    def sync(self):
        return None

    def nonNullSync(self):
        return None

    def promise(self):
        return resolved(None)

    def nonNullPromise(self):
        return resolved(None)

    def nest(self):
        return NullingData()

    def nonNullNest(self):
        return NullingData()

    def promiseNest(self):
        return resolved(NullingData())

    def nonNullPromiseNest(self):
        return resolved(NullingData())


DataType = GraphQLObjectType('DataType', lambda: {
    'sync': GraphQLField(GraphQLString),
    'nonNullSync': GraphQLField(GraphQLNonNull(GraphQLString)),
    'promise': GraphQLField(GraphQLString),
    'nonNullPromise': GraphQLField(GraphQLNonNull(GraphQLString)),
    'nest': GraphQLField(DataType),
    'nonNullNest': GraphQLField(GraphQLNonNull(DataType)),
    'promiseNest': GraphQLField(DataType),
    'nonNullPromiseNest': GraphQLField(GraphQLNonNull(DataType))
})

schema = GraphQLSchema(DataType)


def check(doc, data, expected):
    ast = parse(doc)
    response = execute(schema, ast, data)

    if response.errors:
        result = {
            'data': response.data,
            'errors': [format_error(e) for e in response.errors]
        }
    else:
        result = {
            'data': response.data
        }

    assert result == expected


def test_nulls_a_nullable_field_that_throws_sync():
    doc = '''
        query Q {
            sync
        }
    '''

    check(doc, ThrowingData(), {
        'data': {'sync': None},
        'errors': [{'locations': [{'column': 13, 'line': 3}], 'message': str(sync_error)}]
    })


def test_nulls_a_nullable_field_that_throws_in_a_promise():
    doc = '''
        query Q {
            promise
        }
    '''

    check(doc, ThrowingData(), {
        'data': {'promise': None},
        'errors': [{'locations': [{'column': 13, 'line': 3}], 'message': str(promise_error)}]
    })


def test_nulls_a_sync_returned_object_that_contains_a_non_nullable_field_that_throws():
    doc = '''
        query Q {
            nest {
                nonNullSync,
            }
        }
    '''

    check(doc, ThrowingData(), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 17, 'line': 4}],
                    'message': str(non_null_sync_error)}]
    })


def test_nulls_a_synchronously_returned_object_that_contains_a_non_nullable_field_that_throws_in_a_promise():
    doc = '''
        query Q {
            nest {
                nonNullPromise,
            }
        }
    '''

    check(doc, ThrowingData(), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 17, 'line': 4}],
                    'message': str(non_null_promise_error)}]
    })


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_throws_synchronously():
    doc = '''
        query Q {
            promiseNest {
                nonNullSync,
            }
        }
    '''

    check(doc, ThrowingData(), {
        'data': {'promiseNest': None},
        'errors': [{'locations': [{'column': 17, 'line': 4}],
                    'message': str(non_null_sync_error)}]
    })


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_throws_in_a_promise():
    doc = '''
        query Q {
            promiseNest {
                nonNullPromise,
            }
        }
    '''

    check(doc, ThrowingData(), {
        'data': {'promiseNest': None},
        'errors': [{'locations': [{'column': 17, 'line': 4}],
                    'message': str(non_null_promise_error)}]
    })


def test_nulls_a_complex_tree_of_nullable_fields_that_throw():
    doc = '''
      query Q {
        nest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
        promiseNest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
      }
    '''
    check(doc, ThrowingData(), {
        'data': {'nest': {'nest': {'promise': None, 'sync': None},
                          'promise': None,
                          'promiseNest': {'promise': None, 'sync': None},
                          'sync': None},
                 'promiseNest': {'nest': {'promise': None, 'sync': None},
                                 'promise': None,
                                 'promiseNest': {'promise': None, 'sync': None},
                                 'sync': None}},
        'errors': [{'locations': [{'column': 11, 'line': 4}], 'message': str(sync_error)},
                   {'locations': [{'column': 11, 'line': 5}], 'message': str(promise_error)},
                   {'locations': [{'column': 13, 'line': 7}], 'message': str(sync_error)},
                   {'locations': [{'column': 13, 'line': 8}], 'message': str(promise_error)},
                   {'locations': [{'column': 13, 'line': 11}], 'message': str(sync_error)},
                   {'locations': [{'column': 13, 'line': 12}], 'message': str(promise_error)},
                   {'locations': [{'column': 11, 'line': 16}], 'message': str(sync_error)},
                   {'locations': [{'column': 11, 'line': 17}], 'message': str(promise_error)},
                   {'locations': [{'column': 13, 'line': 19}], 'message': str(sync_error)},
                   {'locations': [{'column': 13, 'line': 20}], 'message': str(promise_error)},
                   {'locations': [{'column': 13, 'line': 23}], 'message': str(sync_error)},
                   {'locations': [{'column': 13, 'line': 24}], 'message': str(promise_error)}]
    })


def test_nulls_the_first_nullable_object_after_a_field_throws_in_a_long_chain_of_fields_that_are_non_null():
    doc = '''
    query Q {
        nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        anotherNest: nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
        anotherPromiseNest: promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
      }
    '''
    check(doc, ThrowingData(), {
        'data': {'nest': None, 'promiseNest': None, 'anotherNest': None, 'anotherPromiseNest': None},
        'errors': [{'locations': [{'column': 19, 'line': 8}],
                    'message': str(non_null_sync_error)},
                   {'locations': [{'column': 19, 'line': 19}],
                    'message': str(non_null_sync_error)},
                   {'locations': [{'column': 19, 'line': 30}],
                    'message': str(non_null_promise_error)},
                   {'locations': [{'column': 19, 'line': 41}],
                    'message': str(non_null_promise_error)}]
    })


def test_nulls_a_nullable_field_that_returns_null():
    doc = '''
        query Q {
            sync
        }
    '''

    check(doc, NullingData(), {
        'data': {'sync': None}
    })


def test_nulls_a_nullable_field_that_returns_null_in_a_promise():
    doc = '''
        query Q {
            promise
        }
    '''

    check(doc, NullingData(), {
        'data': {'promise': None}
    })


def test_nulls_a_sync_returned_object_that_contains_a_non_nullable_field_that_returns_null_synchronously():
    doc = '''
        query Q {
            nest {
                nonNullSync,
            }
        }
    '''
    check(doc, NullingData(), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 17, 'line': 4}],
                    'message': 'Cannot return null for non-nullable field DataType.nonNullSync.'}]
    })


def test_nulls_a_synchronously_returned_object_that_contains_a_non_nullable_field_that_returns_null_in_a_promise():
    doc = '''
        query Q {
            nest {
                nonNullPromise,
            }
        }
    '''
    check(doc, NullingData(), {
        'data': {'nest': None},
        'errors': [{'locations': [{'column': 17, 'line': 4}],
                    'message': 'Cannot return null for non-nullable field DataType.nonNullPromise.'}]
    })


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_returns_null_synchronously():
    doc = '''
        query Q {
            promiseNest {
                nonNullSync,
            }
        }
    '''
    check(doc, NullingData(), {
        'data': {'promiseNest': None},
        'errors': [{'locations': [{'column': 17, 'line': 4}],
                    'message': 'Cannot return null for non-nullable field DataType.nonNullSync.'}]
    })


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_returns_null_ina_a_promise():
    doc = '''
        query Q {
            promiseNest {
                nonNullPromise
            }
        }
    '''

    check(doc, NullingData(), {
        'data': {'promiseNest': None},
        'errors': [
            {'locations': [{'column': 17, 'line': 4}],
             'message': 'Cannot return null for non-nullable field DataType.nonNullPromise.'}
        ]
    })


def test_nulls_a_complex_tree_of_nullable_fields_that_returns_null():
    doc = '''
      query Q {
        nest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
        promiseNest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
      }
    '''
    check(doc, NullingData(), {
        'data': {
            'nest': {
                'sync': None,
                'promise': None,
                'nest': {
                    'sync': None,
                    'promise': None,
                },
                'promiseNest': {
                    'sync': None,
                    'promise': None,
                }
            },
            'promiseNest': {
                'sync': None,
                'promise': None,
                'nest': {
                    'sync': None,
                    'promise': None,
                },
                'promiseNest': {
                    'sync': None,
                    'promise': None,
                }
            }
        }
    })


def test_nulls_the_first_nullable_object_after_a_field_returns_null_in_a_long_chain_of_fields_that_are_non_null():
    doc = '''
      query Q {
        nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        anotherNest: nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
        anotherPromiseNest: promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
      }
    '''

    check(doc, NullingData(), {
        'data': {
            'nest': None,
            'promiseNest': None,
            'anotherNest': None,
            'anotherPromiseNest': None
        },
        'errors': [
            {'locations': [{'column': 19, 'line': 8}],
             'message': 'Cannot return null for non-nullable field DataType.nonNullSync.'},
            {'locations': [{'column': 19, 'line': 19}],
             'message': 'Cannot return null for non-nullable field DataType.nonNullSync.'},
            {'locations': [{'column': 19, 'line': 30}],
             'message': 'Cannot return null for non-nullable field DataType.nonNullPromise.'},
            {'locations': [{'column': 19, 'line': 41}],
             'message': 'Cannot return null for non-nullable field DataType.nonNullPromise.'}
        ]
    })


def test_nulls_the_top_level_if_sync_non_nullable_field_throws():
    doc = '''
        query Q { nonNullSync }
    '''
    check(doc, ThrowingData(), {
        'data': None,
        'errors': [
            {'locations': [{'column': 19, 'line': 2}],
             'message': str(non_null_sync_error)}
        ]
    })


def test_nulls_the_top_level_if_async_non_nullable_field_errors():
    doc = '''
        query Q { nonNullPromise }
    '''

    check(doc, ThrowingData(), {
        'data': None,
        'errors': [
            {'locations': [{'column': 19, 'line': 2}],
             'message': str(non_null_promise_error)}
        ]
    })


def test_nulls_the_top_level_if_sync_non_nullable_field_returns_null():
    doc = '''
        query Q { nonNullSync }
    '''
    check(doc, NullingData(), {
        'data': None,
        'errors': [
            {'locations': [{'column': 19, 'line': 2}],
             'message': 'Cannot return null for non-nullable field DataType.nonNullSync.'}
        ]
    })


def test_nulls_the_top_level_if_async_non_nullable_field_resolves_null():
    doc = '''
        query Q { nonNullPromise }
    '''
    check(doc, NullingData(), {
        'data': None,
        'errors': [
            {'locations': [{'column': 19, 'line': 2}],
             'message': 'Cannot return null for non-nullable field DataType.nonNullPromise.'}
        ]
    })
