import logging

from rx import Observable

from promise import Promise

from ..type import GraphQLSchema
from .base import ExecutionResult
from .executors.sync import SyncExecutor
from .common import (
    prepare_execution_context,
    get_promise_executor,
    get_on_rejected,
    get_on_resolve,
)

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Optional, Union
    from ..language.ast import Document

logger = logging.getLogger(__name__)


def subscribe(*args, **kwargs):
    # type: (*Any, **Any) -> Union[ExecutionResult, Observable]
    allow_subscriptions = kwargs.pop("allow_subscriptions", True)
    return execute(  # type: ignore
        *args, allow_subscriptions=allow_subscriptions, **kwargs
    )


def execute(
    schema,  # type: GraphQLSchema
    document_ast,  # type: Document
    root=None,  # type: Any
    context=None,  # type: Optional[Any]
    variables=None,  # type: Optional[Any]
    operation_name=None,  # type: Optional[str]
    executor=None,  # type: Any
    return_promise=False,  # type: bool
    middleware=None,  # type: Optional[Any]
    allow_subscriptions=False,  # type: bool
    **options  # type: Any
):
    # type: (...) -> Union[ExecutionResult, Promise[ExecutionResult]]

    if executor is None:
        executor = SyncExecutor()

    exe_context = prepare_execution_context(
        schema,
        document_ast,
        root,
        context,
        variables,
        operation_name,
        executor,
        middleware,
        allow_subscriptions,
        **options
    )

    promise_executor = get_promise_executor(exe_context, root)
    on_rejected = get_on_rejected(exe_context)
    on_resolve = get_on_resolve(exe_context)
    promise = (
        Promise.resolve(None).then(promise_executor).catch(on_rejected).then(on_resolve)
    )

    if not return_promise:
        exe_context.executor.wait_until_finished()
        return promise.get()
    else:
        clean = getattr(exe_context.executor, "clean", None)
        if clean:
            clean()

    return promise
