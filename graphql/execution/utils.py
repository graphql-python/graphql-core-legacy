import collections

from promise import is_thenable, Promise
from six.__init__ import string_types

from graphql import GraphQLInterfaceType, GraphQLUnionType, GraphQLObjectType, GraphQLError
from graphql.execution.executor import execute_fields, complete_value, complete_value_catching_error


def complete_leaf_value(exe_context, return_type, field_asts, info, result):
    """
    Complete a Scalar or Enum by serializing to a valid value, returning null if serialization is not possible.
    """
    # serialize = getattr(return_type, 'serialize', None)
    # assert serialize, 'Missing serialize method on type'

    return return_type.serialize(result)


def complete_abstract_value(exe_context, return_type, field_asts, info, result):
    """
    Complete an value of an abstract type by determining the runtime type of that value, then completing based
    on that type.
    """
    runtime_type = None

    # Field type must be Object, Interface or Union and expect sub-selections.
    if isinstance(return_type, (GraphQLInterfaceType, GraphQLUnionType)):
        if return_type.resolve_type:
            runtime_type = return_type.resolve_type(result, info)
        else:
            runtime_type = get_default_resolve_type_fn(
                result, info, return_type)

    if isinstance(runtime_type, string_types):
        runtime_type = info.schema.get_type(runtime_type)

    if not isinstance(runtime_type, GraphQLObjectType):
        raise GraphQLError(
            ('Abstract type {} must resolve to an Object type at runtime ' +
             'for field {}.{} with value "{}", received "{}".').format(
                 return_type,
                 info.parent_type,
                 info.field_name,
                 result,
                 runtime_type,
            ),
            field_asts
        )

    if not exe_context.schema.is_possible_type(return_type, runtime_type):
        raise GraphQLError(
            u'Runtime Object type "{}" is not a possible type for "{}".'.format(
                runtime_type, return_type),
            field_asts
        )

    return complete_object_value(exe_context, runtime_type, field_asts, info, result)


def get_default_resolve_type_fn(value, info, abstract_type):
    possible_types = info.schema.get_possible_types(abstract_type)
    for type in possible_types:
        if callable(type.is_type_of) and type.is_type_of(value, info):
            return type


def complete_object_value(exe_context, return_type, field_asts, info, result):
    """
    Complete an Object value by evaluating all sub-selections.
    """
    if return_type.is_type_of and not return_type.is_type_of(result, info):
        raise GraphQLError(
            u'Expected value of type "{}" but got: {}.'.format(
                return_type, type(result).__name__),
            field_asts
        )

    # Collect sub-fields to execute to complete this value.
    subfield_asts = exe_context.get_sub_fields(return_type, field_asts)
    return execute_fields(exe_context, return_type, result, subfield_asts)


def complete_nonnull_value(exe_context, return_type, field_asts, info, result):
    """
    Complete a NonNull value by completing the inner type
    """
    completed = complete_value(
        exe_context, return_type.of_type, field_asts, info, result
    )
    if completed is None:
        raise GraphQLError(
            'Cannot return null for non-nullable field {}.{}.'.format(
                info.parent_type, info.field_name),
            field_asts
        )

    return completed


def complete_list_value(exe_context, return_type, field_asts, info, result):
    """
    Complete a list value by completing each item in the list with the inner type
    """
    assert isinstance(result, collections.Iterable), \
        ('User Error: expected iterable, but did not find one ' +
         'for field {}.{}.').format(info.parent_type, info.field_name)

    item_type = return_type.of_type
    completed_results = []
    contains_promise = False
    for item in result:
        completed_item = complete_value_catching_error(
            exe_context, item_type, field_asts, info, item)
        if not contains_promise and is_thenable(completed_item):
            contains_promise = True

        completed_results.append(completed_item)

    return Promise.all(completed_results) if contains_promise else completed_results