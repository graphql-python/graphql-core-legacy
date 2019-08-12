import asyncio

from .execution import ExecutionResult
from .backend import get_default_backend

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Union, Optional, Generator
    from .language.ast import Document
    from .type.schema import GraphQLSchema


@asyncio.coroutine
def graphql_async(*args, **kwargs):
    # type: (*Any, **Any) -> Generator
    result = yield from execute_graphql_async(*args, **kwargs)
    return result


@asyncio.coroutine
def execute_graphql_async(
    schema,  # type: GraphQLSchema
    request_string="",  # type: Union[Document, str]
    root=None,  # type: Any
    context=None,  # type: Optional[Any]
    variables=None,  # type: Optional[Any]
    operation_name=None,  # type: Optional[Any]
    middleware=None,  # type: Optional[Any]
    backend=None,  # type: Optional[Any]
    **execute_options  # type: Any
):
    # type: (...) -> Generator
    try:
        if backend is None:
            backend = get_default_backend()

        document = backend.document_from_string_async(schema, request_string)
        result = yield from document.execute(
            root=root,
            context=context,
            operation_name=operation_name,
            variables=variables,
            middleware=middleware,
            **execute_options
        )
        return result
    except Exception as e:
        return ExecutionResult(errors=[e], invalid=True)
