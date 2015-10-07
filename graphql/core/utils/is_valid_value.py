"""
    Implementation of isValidJSValue from graphql-js
"""

import collections
from six import string_types
from ..type import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
)
from .is_nullish import is_nullish


def is_valid_value(type, value):
    """Given a type and any value, return True if that value is valid."""
    if isinstance(type, GraphQLNonNull):
        if is_nullish(value):
            return False

        return is_valid_value(type.of_type, value)

    if is_nullish(value):
        return True

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if not isinstance(value, string_types) and \
                isinstance(value, collections.Iterable):
            return all(is_valid_value(item_type, item) for item in value)
        else:
            return is_valid_value(item_type, value)

    if isinstance(type, GraphQLInputObjectType):
        if not isinstance(value, collections.Mapping):
            return False

        fields = type.get_fields()

        # Ensure every provided field is defined.
        if any(field_name not in fields for field_name in value.keys()):
            return False

        # Ensure every defined field is valid.
        return all(
            is_valid_value(field.type, value.get(field_name))
            for field_name, field in fields.items()
        )

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), \
        'Must be input type'

    # Scalar/Enum input checks to ensure the type can parse the value to
    # a non-null value.
    return not is_nullish(type.parse_value(value))
