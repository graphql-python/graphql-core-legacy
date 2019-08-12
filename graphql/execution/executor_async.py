import asyncio

from promise import Promise

from ..type import GraphQLSchema

from .executors.asyncio import AsyncioExecutor
from .common import (
    prepare_execution_context,
    get_promise_executor,
    get_on_rejected,
    get_on_resolve,
)


# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Optional, Generator
    from ..language.ast import Document


@asyncio.coroutine
def execute_async(
    schema,  # type: GraphQLSchema
    document_ast,  # type: Document
    root=None,  # type: Any
    context=None,  # type: Optional[Any]
    variables=None,  # type: Optional[Any]
    operation_name=None,  # type: Optional[str]
    executor=None,  # type: Any
    middleware=None,  # type: Optional[Any]
    allow_subscriptions=False,  # type: bool
    **options  # type: Any
):
    # type: (...) -> Generator
    if executor is None:
        executor = AsyncioExecutor()
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

    yield from exe_context.executor.wait_until_finished_async()
    return promise.get()
