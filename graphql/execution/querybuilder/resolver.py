import collections
from functools import partial

from ...error import GraphQLError, GraphQLLocatedError
from ...type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                     GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                     GraphQLSchema, GraphQLUnionType)
from .fragment import Fragment

from promise import Promise


def is_promise(value):
    return type(value) == Promise


def on_complete_resolver(__func, __resolver, *args, **kwargs):
    result = __resolver(*args, **kwargs)
    if is_promise(result):
        return result.then(__func)
    return __func(result)


def complete_list_value(inner_resolver, result):
    assert isinstance(result, collections.Iterable), \
        ('User Error: expected iterable, but did not find one ' +
         'for field {}.{}.').format(info.parent_type, info.field_name)

    completed_results = []
    for item in result:
        completed_item = inner_resolver(item)
        completed_results.append(completed_item)

    return completed_results


def complete_nonnull_value(result):
    if result is None:
        field_asts = 'TODO'
        raise GraphQLError(
            'Cannot return null for non-nullable field {}.{}.'.format(info.parent_type, info.field_name),
            field_asts
        )
    return result


def field_resolver(field, fragment=None):
    return type_resolver(field.type, field.resolver, fragment)


def type_resolver(return_type, resolver, fragment=None):
    if isinstance(return_type, GraphQLNonNull):
        return type_resolver_non_null(return_type, resolver, fragment)

    if isinstance(return_type, (GraphQLScalarType, GraphQLEnumType)):
        return type_resolver_leaf(return_type, resolver)

    if isinstance(return_type, (GraphQLList)):
        return type_resolver_list(return_type, resolver, fragment)

    if isinstance(return_type, (GraphQLObjectType)):
        assert fragment and fragment.type == return_type
        return partial(on_complete_resolver, fragment.resolve, resolver)
        # return partial(fragment.resolver, resolver)

    if isinstance(return_type, (GraphQLInterfaceType, GraphQLUnionType)):
        assert fragment
        return partial(on_complete_resolver, fragment.resolve, resolver)
        # return partial(fragment.resolver, resolver)
        # return partial(fragment.abstract_resolver, resolver, return_type)

    raise Exception("The resolver have to be created for a fragment")


def type_resolver_non_null(return_type, resolver, fragment=None):
    resolver = type_resolver(return_type.of_type, resolver)
    return partial(on_complete_resolver, complete_nonnull_value, resolver)


def type_resolver_leaf(return_type, resolver):
    return partial(on_complete_resolver, return_type.serialize, resolver)


def type_resolver_list(return_type, resolver, fragment=None):
    inner_resolver = type_resolver(return_type.of_type, lambda item: item, fragment)
    list_complete = partial(complete_list_value, inner_resolver)
    return partial(on_complete_resolver, list_complete, resolver)
