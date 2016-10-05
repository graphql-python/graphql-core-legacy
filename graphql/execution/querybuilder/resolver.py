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


def on_complete_resolver(__func, exe_context, info, __resolver, *args, **kwargs):
    try:
        result = __resolver(*args, **kwargs)
    except Exception, e:
        exe_context.errors.append(e)
        return None

    if is_promise(result):
        return result.then(__func)
    return __func(result)


def complete_list_value(inner_resolver, exe_context, info, result):
    assert isinstance(result, collections.Iterable), \
        ('User Error: expected iterable, but did not find one ' +
         'for field {}.{}.').format(info.parent_type, info.field_name)

    completed_results = []
    for item in result:
        try:
            completed_item = inner_resolver(item)
        except Exception, e:
            completed_item = None
            exe_context.errors.append(e)
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


def field_resolver(field, fragment=None, exe_context=None, info=None):
    return type_resolver(field.type, field.resolver, fragment, exe_context, info)


def type_resolver(return_type, resolver, fragment=None, exe_context=None, info=None):
    if isinstance(return_type, GraphQLNonNull):
        return type_resolver_non_null(return_type, resolver, fragment, exe_context, info)

    if isinstance(return_type, (GraphQLScalarType, GraphQLEnumType)):
        return type_resolver_leaf(return_type, resolver, exe_context, info)

    if isinstance(return_type, (GraphQLList)):
        return type_resolver_list(return_type, resolver, fragment, exe_context, info)

    if isinstance(return_type, (GraphQLObjectType)):
        assert fragment and fragment.type == return_type
        return partial(on_complete_resolver, fragment.resolve, exe_context, info, resolver)
        # return partial(fragment.resolver, resolver)

    if isinstance(return_type, (GraphQLInterfaceType, GraphQLUnionType)):
        assert fragment
        return partial(on_complete_resolver, fragment.resolve, exe_context, info, resolver)
        # return partial(fragment.resolver, resolver)
        # return partial(fragment.abstract_resolver, resolver, return_type)

    raise Exception("The resolver have to be created for a fragment")


def type_resolver_non_null(return_type, resolver, fragment, exe_context, info):
    resolver = type_resolver(return_type.of_type, resolver)
    return partial(on_complete_resolver, complete_nonnull_value, exe_context, info, resolver)


def type_resolver_leaf(return_type, resolver, exe_context, info):
    return partial(on_complete_resolver, return_type.serialize, exe_context, info, resolver)


def type_resolver_list(return_type, resolver, fragment, exe_context, info):
    inner_resolver = type_resolver(return_type.of_type, lambda item: item, fragment)
    list_complete = partial(complete_list_value, inner_resolver, exe_context, info)
    return partial(on_complete_resolver, list_complete, exe_context, info, resolver)
