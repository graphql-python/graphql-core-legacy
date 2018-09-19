import re
from typing import Optional

from ..language import Node
from ..error import GraphQLError

__all__ = ["assert_valid_name", "is_valid_name_error"]


re_name = re.compile("^[_a-zA-Z][_a-zA-Z0-9]*$")


def assert_valid_name(name):
    """Uphold the spec rules about naming."""
    error = is_valid_name_error(name)
    if error:
        raise error
    return name


def is_valid_name_error(name, node=None):
    """Return an Error if a name is invalid."""
    if not isinstance(name, str):
        raise TypeError("Expected string")
    if name.startswith("__"):
        return GraphQLError(
            (
                "Name {!r} must not begin with '__',"
                " which is reserved by GraphQL introspection."
            ).format(name),
            node,
        )
    if not re_name.match(name):
        return GraphQLError(
            "Names must match /^[_a-zA-Z][_a-zA-Z0-9]*$/"
            " but {!r} does not.".format(name),
            node,
        )
    return None
