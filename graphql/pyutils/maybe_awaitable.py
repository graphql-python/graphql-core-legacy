from typing import TypeVar, Union
from promise import Promise

__all__ = ["MaybeAwaitable"]


T = TypeVar("T")

MaybeAwaitable = Union[Promise, T]
