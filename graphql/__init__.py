'''
GraphQL provides a Python implementation for the GraphQL specification
but is also a useful utility for operating on GraphQL files and building
sophisticated tools.

This primary module exports a general purpose function for fulfilling all
steps of the GraphQL specification in a single operation, but also includes
utilities for every part of the GraphQL specification:

  - Parsing the GraphQL language.
  - Building a GraphQL type schema.
  - Validating a GraphQL request against a type schema.
  - Executing a GraphQL request against a type schema.

This also includes utility functions for operating on GraphQL types and
GraphQL documents to facilitate building tools.
'''

from .execution import ExecutionResult, execute
from .language.parser import parse
from .language.source import Source
from .validation import validate


def graphql(schema, request='', root=None, args=None, operation_name=None):
    try:
        source = Source(request, 'GraphQL request')
        ast = parse(source)
        validation_errors = validate(schema, ast)
        if validation_errors:
            return ExecutionResult(
                errors=validation_errors,
                invalid=True,
            )
        return execute(
            schema,
            root or object(),
            ast,
            operation_name,
            args or {},
        )
    except Exception as e:
        return ExecutionResult(
            errors=[e],
            invalid=True,
        )
