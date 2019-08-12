import asyncio

from .utils import validate_document_ast
from ..execution import execute_async

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Union
    from ..execution import ExecutionResult
    from ..language.ast import Document
    from ..type.schema import GraphQLSchema
    from rx import Observable


@asyncio.coroutine
def execute_and_validate_async(
    schema,  # type: GraphQLSchema
    document_ast,  # type: Document
    *args,  # type: Any
    **kwargs  # type: Any
):
    # type: (...) -> Union[ExecutionResult, Observable]
    execution_result = validate_document_ast(schema, document_ast, **kwargs)
    if execution_result:
        return execution_result
    result = yield from execute_async(schema, document_ast, *args, **kwargs)
    return result
