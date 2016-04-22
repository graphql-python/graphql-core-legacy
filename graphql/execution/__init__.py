# -*- coding: utf-8 -*-
"""
Terminology

"Definitions" are the generic name for top-level statements in the document.
Examples of this include:
1) Operations (such as a query)
2) Fragments

"Operations" are a generic name for requests in the document.
Examples of this include:
1) query,
2) mutation

"Selections" are the statements that can appear legally and at
single level of the query. These include:
1) field references e.g "a"
2) fragment "spreads" e.g. "...c"
3) inline fragment "spreads" e.g. "...on Type { a }"
"""
from .execute import execute as _execute
from .base import ExecutionResult
# from .executor import Executor
# from .middlewares.sync import SynchronousExecutionMiddleware

def execute(schema, root, ast, operation_name='', args=None):
    return _execute(schema, ast, root, variable_values=args, operation_name=operation_name)

# def execute(schema, root, ast, operation_name='', args=None):
#     """
#     Executes an AST synchronously. Assumes that the AST is already validated.
#     """
#     return get_default_executor().execute(schema, ast, root, args, operation_name, validate_ast=False)


# _default_executor = None


# def get_default_executor():
#     """
#         Gets the default executor to be used in the `execute` function above.
#     """
#     global _default_executor
#     if _default_executor is None:
#         _default_executor = Executor([SynchronousExecutionMiddleware()])

#     return _default_executor


# def set_default_executor(executor):
#     """
#         Sets the default executor to be used in the `execute` function above.

#         If passed `None` will reset to the original default synchronous executor.
#     """
#     assert isinstance(executor, Executor) or executor is None
#     global _default_executor
#     _default_executor = executor


# __all__ = ['ExecutionResult', 'Executor', 'execute', 'get_default_executor', 'set_default_executor']
