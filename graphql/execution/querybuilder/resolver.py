import collections
from functools import partial

from ...error import GraphQLError, GraphQLLocatedError
from ...type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                     GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                     GraphQLSchema, GraphQLUnionType)
from .fragment import Fragment


def non_null_resolver_wrapper(resolver, *args, **kwargs):
    completed = resolver(*args, **kwargs)
    if completed is None:
        field_asts = 'TODO'
        raise GraphQLError(
            'Cannot return null for non-nullable field {}.{}.'.format(info.parent_type, info.field_name),
            field_asts
        )
    return completed


def leaf_resolver_wrapper(serializer, resolver, *args, **kwargs):
    result = resolver(*args, **kwargs)
    return serializer(result)


def list_resolver_wrapper(resolver, inner_resolver, *args, **kwargs):
    result = resolver(*args, **kwargs)

    assert isinstance(result, collections.Iterable), \
        ('User Error: expected iterable, but did not find one ' +
         'for field {}.{}.').format(info.parent_type, info.field_name)

    completed_results = []
    for item in result:
        completed_item = inner_resolver(item)
        completed_results.append(completed_item)

    return completed_results


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
        assert fragment
        return partial(fragment.resolver, resolver)

    if isinstance(return_type, (GraphQLInterfaceType, GraphQLUnionType)):
        assert fragment
        return partial(fragment.abstract_resolver, resolver, return_type)

    raise Exception("The resolver have to be created for a fragment")


def type_resolver_non_null(return_type, resolver, fragment=None):
    resolver = type_resolver(return_type.of_type, resolver)
    return partial(non_null_resolver_wrapper, resolver)


def type_resolver_leaf(return_type, resolver):
    return partial(leaf_resolver_wrapper, return_type.serialize, resolver)


def type_resolver_list(return_type, resolver, fragment=None):
    inner_resolver = type_resolver(return_type.of_type, lambda item: item, fragment)
    return partial(list_resolver_wrapper, resolver, inner_resolver)
