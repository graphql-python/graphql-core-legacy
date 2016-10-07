import mock
import pytest

from promise import Promise

from ....error import GraphQLError, GraphQLLocatedError
from ....language import ast
from ....type import (GraphQLEnumType, GraphQLField, GraphQLInt,
                      GraphQLInterfaceType, GraphQLList, GraphQLNonNull,
                      GraphQLObjectType, GraphQLScalarType, GraphQLSchema,
                      GraphQLString, GraphQLUnionType)
from ..fragment import Fragment
from ..resolver import field_resolver, type_resolver


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
    assert resolved is None
    assert len(exe_context.errors) == 1
    assert str(exe_context.errors[0]) == 'raises'


def test_nonnull_field_resolver_mask_exception():
    info = mock.MagicMock()
    info.parent_type = 'parent_type'
    info.field_name = 'field_name'
    exe_context = mock.MagicMock()
    exe_context.errors = []
    field = GraphQLField(GraphQLNonNull(GraphQLString), resolver=raises)
    resolver = field_resolver(field, info=info, exe_context=exe_context)
    with pytest.raises(GraphQLLocatedError) as exc_info:
        resolver()
    assert str(exc_info.value) == 'raises'


def test_nonnull_field_resolver_fails_on_null_value():
    info = mock.MagicMock()
    info.parent_type = 'parent_type'
    info.field_name = 'field_name'
    exe_context = mock.MagicMock()
    exe_context.errors = []
    field = GraphQLField(GraphQLNonNull(GraphQLString), resolver=lambda *_: None)
    resolver = field_resolver(field, info=info, exe_context=exe_context)
    with pytest.raises(GraphQLError) as exc_info:
        resolver()

    assert str(exc_info.value) == 'Cannot return null for non-nullable field parent_type.field_name.'


def test_nonnull_list_field_resolver_fails_silently_on_null_value():
    info = mock.MagicMock()
    info.parent_type = 'parent_type'
    info.field_name = 'field_name'
    exe_context = mock.MagicMock()
    exe_context.errors = []
    field = GraphQLField(GraphQLList(GraphQLNonNull(GraphQLString)), resolver=lambda *_: ['1', None])
    resolver = field_resolver(field, info=info, exe_context=exe_context)
    assert resolver() is None

    assert len(exe_context.errors) == 1
    assert str(exe_context.errors[0]) == 'Cannot return null for non-nullable field parent_type.field_name.'


def test_nonnull_list_field_resolver_fails_on_null_value_top():
    DataType = GraphQLObjectType('DataType', {
        'nonNullString': GraphQLField(GraphQLNonNull(GraphQLString), resolver=lambda *_: None),
    })
    info = mock.MagicMock()
    info.parent_type = 'parent_type'
    info.field_name = 'field_name'
    exe_context = mock.MagicMock()
    exe_context.errors = []
    field = GraphQLField(GraphQLNonNull(DataType), resolver=lambda *_: 1)
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='nonNullString'),
        )
    ])
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    datetype_fragment = Fragment(type=DataType, selection_set=selection_set, context=exe_context)
    resolver = field_resolver(field, info=info, exe_context=exe_context, fragment=datetype_fragment)
    with pytest.raises(GraphQLError) as exc_info:
        resolver()

    assert not exe_context.errors
    assert str(exc_info.value) == 'Cannot return null for non-nullable field parent_type.field_name.'


def test_nonnull_list_field_resolver_fails_on_null_value_top():
    DataType = GraphQLObjectType('DataType', {
        'nonNullString': GraphQLField(GraphQLString, resolver=lambda *_: None),
    })
    info = mock.MagicMock()
    info.parent_type = 'parent_type'
    info.field_name = 'field_name'
    exe_context = mock.MagicMock()
    exe_context.errors = []
    field = GraphQLField(GraphQLNonNull(DataType), resolver=lambda *_: 1)
    selection_set = ast.SelectionSet(selections=[
        ast.Field(
            name=ast.Name(value='nonNullString'),
        )
    ])
    # node_fragment = Fragment(type=Node, field_asts=node_field_asts)
    datetype_fragment = Fragment(type=DataType, selection_set=selection_set, context=exe_context)
    resolver = field_resolver(field, info=info, exe_context=exe_context, fragment=datetype_fragment)
    data = resolver()
    assert data == {
        'nonNullString': None
    }
