from sys import exc_info

if False:
    from ..base import ResolveInfo
    from promise import Promise
    from typing import Callable, Dict, Tuple, Union


def process(
    p,  # type: Promise
    f,  # type: Callable
    args,  # type: Tuple[Any, ResolveInfo]
    kwargs,  # type: Dict[str, Any]
):
    # type: (...) -> None
    try:
        val = f(*args, **kwargs)
        p.do_resolve(val)
    except Exception as e:
        traceback = exc_info()[2]
        e.stack = traceback
        p.do_reject(e, traceback=traceback)
