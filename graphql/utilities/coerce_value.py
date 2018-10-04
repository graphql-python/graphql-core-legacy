from typing import Any, Dict, Iterable, List, Optional, Union, cast
from collections import namedtuple

from ..error import GraphQLError, INVALID
from ..language import Node
from ..pyutils import is_invalid, or_list, suggestion_list, OrderedDict
from ..type import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLList,
    GraphQLScalarType,
    is_enum_type,
    is_input_object_type,
    is_list_type,
    is_non_null_type,
    is_scalar_type,
    GraphQLNonNull,
)
from ..pyutils.compat import string_types

__all__ = ["coerce_value", "CoercedValue"]


CoercedValue = namedtuple("CoercedValue", ("errors", "value"))


Path = namedtuple("CoercedValue", ("prev", "key"))


def coerce_value(value, type_, blame_node=None, path=None):
    """Coerce a Python value given a GraphQL Type.

    Returns either a value which is valid for the provided type or a list of
    encountered coercion errors.
    """
    # A value must be provided if the type is non-null.
    if is_non_null_type(type_):
        if value is None or value is INVALID:
            return of_errors(
                [
                    coercion_error(
                        "Expected non-nullable type {} not to be null".format(type_),
                        blame_node,
                        path,
                    )
                ]
            )
        type_ = type_
        return coerce_value(value, type_.of_type, blame_node, path)

    if value is None or value is INVALID:
        # Explicitly return the value null.
        return of_value(None)

    if is_scalar_type(type_):
        # Scalars determine if a value is valid via parse_value(), which can
        # throw to indicate failure. If it throws, maintain a reference to
        # the original error.
        type_ = type_
        try:
            parse_result = type_.parse_value(value)
            if is_invalid(parse_result):
                return of_errors(
                    [
                        coercion_error(
                            "Expected type {}".format(type_.name), blame_node, path
                        )
                    ]
                )
            return of_value(parse_result)
        except (TypeError, ValueError) as error:
            return of_errors(
                [
                    coercion_error(
                        "Expected type {}".format(type_.name),
                        blame_node,
                        path,
                        str(error),
                        error,
                    )
                ]
            )

    if is_enum_type(type_):
        type_ = type_
        values = type_.values
        if isinstance(value, string_types):
            enum_value = values.get(value)
            if enum_value:
                return of_value(value if enum_value.value is None else enum_value.value)
        suggestions = suggestion_list(str(value), values)
        did_you_mean = (
            "did you mean {}?".format(or_list(suggestions)) if suggestions else None
        )
        return of_errors(
            [
                coercion_error(
                    "Expected type {}".format(type_.name),
                    blame_node,
                    path,
                    did_you_mean,
                )
            ]
        )

    if is_list_type(type_):
        type_ = type_
        item_type = type_.of_type
        if isinstance(value, Iterable) and not isinstance(value, string_types):
            errors = None
            coerced_value_list = []
            append_item = coerced_value_list.append
            for index, item_value in enumerate(value):
                coerced_item = coerce_value(
                    item_value, item_type, blame_node, at_path(path, index)
                )
                if coerced_item.errors:
                    errors = add(errors, *coerced_item.errors)
                elif not errors:
                    append_item(coerced_item.value)
            return of_errors(errors) if errors else of_value(coerced_value_list)
        # Lists accept a non-list value as a list of one.
        coerced_item = coerce_value(value, item_type, blame_node)
        return coerced_item if coerced_item.errors else of_value([coerced_item.value])

    if is_input_object_type(type_):
        type_ = type_
        if not isinstance(value, dict):
            return of_errors(
                [
                    coercion_error(
                        "Expected type {} to be a dict".format(type_.name),
                        blame_node,
                        path,
                    )
                ]
            )
        errors = None
        coerced_value_dict = OrderedDict()
        fields = type_.fields

        # Ensure every defined field is valid.
        for field_name, field in fields.items():
            field_value = value.get(field_name, INVALID)
            if is_invalid(field_value):
                if not is_invalid(field.default_value):
                    coerced_value_dict[field_name] = field.default_value
                elif is_non_null_type(field.type):
                    errors = add(
                        errors,
                        coercion_error(
                            ("Field {}" " of required type {} was not provided").format(
                                print_path(at_path(path, field_name)), field.type
                            ),
                            blame_node,
                        ),
                    )
            else:
                coerced_field = coerce_value(
                    field_value, field.type, blame_node, at_path(path, field_name)
                )
                if coerced_field.errors:
                    errors = add(errors, *coerced_field.errors)
                else:
                    coerced_value_dict[field_name] = coerced_field.value

        # Ensure every provided field is defined.
        for field_name in value:
            if field_name not in fields:
                suggestions = suggestion_list(field_name, fields)
                did_you_mean = (
                    "did you mean {}?".format(or_list(suggestions))
                    if suggestions
                    else None
                )
                errors = add(
                    errors,
                    coercion_error(
                        ("Field '{}'" " is not defined by type {}").format(
                            field_name, type_.name
                        ),
                        blame_node,
                        path,
                        did_you_mean,
                    ),
                )

        return of_errors(errors) if errors else of_value(coerced_value_dict)

    raise TypeError("Unexpected type: {type_}.")


def of_value(value):
    return CoercedValue(None, value)


def of_errors(errors):
    return CoercedValue(errors, INVALID)


def add(errors, *more_errors):
    return (errors or []) + list(more_errors)


def at_path(prev, key):
    return Path(prev, key)


def coercion_error(
    message, blame_node=None, path=None, sub_message=None, original_error=None
):
    """Return a GraphQLError instance"""
    if path:
        path_str = print_path(path)
        message += " at {}".format(path_str)
    message += "; {}".format(sub_message) if sub_message else "."
    # noinspection PyArgumentEqualDefault
    return GraphQLError(message, blame_node, None, None, None, original_error)


def print_path(path):
    """Build string describing the path into the value where error was found"""
    path_str = ""
    current_path = path
    while current_path:
        path_str = (
            ".{}".format(current_path.key)
            if isinstance(current_path.key, string_types)
            else "[{}]".format(current_path.key)
        ) + path_str
        current_path = current_path.prev
    return "value{}".format(path_str) if path_str else ""
