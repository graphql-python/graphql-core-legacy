from math import isfinite

if False:  # pragma: no cover
    from typing import Any

__all__ = ["is_finite"]


def is_finite(value):
    # type: (Any) -> bool
    """Return true if a value is a finite number."""
    return isinstance(value, int) or (isinstance(value, float) and isfinite(value))
