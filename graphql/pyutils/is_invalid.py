from typing import Any

from ..error import INVALID

if False:  # pragma: no cover
    from typing import Any

__all__ = ["is_invalid"]


def is_invalid(value):
    # type: (Any) -> bool
    """Return true if a value is undefined, or NaN."""
    return value is INVALID or value != value
