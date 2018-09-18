from typing import Any
from math import isfinite

if False:  # pragma: no cover
    from typing import Any

__all__ = ["is_integer"]


def is_integer(value):
    # type: (Any) -> bool
    """Return true if a value is an integer number."""
    return (isinstance(value, int) and not isinstance(value, bool)) or (
        isinstance(value, float) and isfinite(value) and int(value) == value
    )
