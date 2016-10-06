import pytest
import mock

from ....error import GraphQLError, GraphQLLocatedError

from ....language import ast
from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                      GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                      GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)
from ..resolver import type_resolver, field_resolver

from promise import Promise


@pytest.mark.parametrize("type,value,expected", [
    (GraphQLString, 1, "1"),
    (GraphQLInt, "1", 1),
    (GraphQLNonNull(GraphQLString), 0, "0"),
    (GraphQLNonNull(GraphQLInt), 0, 0),
    (GraphQLList(GraphQLString), [1, 2], ['1', '2']),
    (GraphQLList(GraphQLInt), ['1', '2'], [1, 2]),  
    (GraphQLList(GraphQLNonNull(GraphQLInt)), [0], [0]),
    (GraphQLNonNull(GraphQLList(GraphQLInt)), [], []),
])
def test_type_resolver(type, value, expected):
    resolver = type_resolver(type, lambda: value)
    resolved = resolver()
    assert resolved == expected


@pytest.mark.parametrize("type,value,expected", [
    (GraphQLString, 1, "1"),
    (GraphQLInt, "1", 1),
    (GraphQLNonNull(GraphQLString), 0, "0"),
    (GraphQLNonNull(GraphQLInt), 0, 0),
    (GraphQLList(GraphQLString), [1, 2], ['1', '2']),
    (GraphQLList(GraphQLInt), ['1', '2'], [1, 2]),  
    (GraphQLList(GraphQLNonNull(GraphQLInt)), [0], [0]),
    (GraphQLNonNull(GraphQLList(GraphQLInt)), [], []),
])
def test_type_resolver_promise(type, value, expected):
    promise_value = Promise()
    resolver = type_resolver(type, lambda: promise_value)
    resolved_promise = resolver()
    assert not resolved_promise.is_fulfilled
    promise_value.fulfill(value)
    assert resolved_promise.is_fulfilled
    resolved = resolved_promise.get()
    assert resolved == expected


def raises():
    raise Exception("raises")


def test_resolver_exception():
    info = mock.MagicMock()
    with pytest.raises(GraphQLLocatedError):
        resolver = type_resolver(GraphQLString, raises, info=info)
        resolver()


def test_field_resolver_mask_exception():
    info = mock.MagicMock()
    exe_context = mock.MagicMock()
    exe_context.errors = []
    field = GraphQLField(GraphQLString, resolver=raises)
    resolver = field_resolver(field, info=info, exe_context=exe_context)
    resolved = resolver()
    assert resolved == None
    assert len(exe_context.errors) == 1
    assert str(exe_context.errors[0]) == 'raises'


# def test_nonnull_field_resolver_mask_exception():
#     info = mock.MagicMock()
#     exe_context = mock.MagicMock()
#     exe_context.errors = []
#     field = GraphQLField(GraphQLNonNull(GraphQLString), resolver=raises)
#     resolver = field_resolver(field, info=info, exe_context=exe_context)
#     with pytest.raises(GraphQLLocatedError):
#         resolver()
