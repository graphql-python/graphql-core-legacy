from promise import Promise

from graphql.execution import ExecutionResult
from graphql.language.parser import parse
from graphql.language.source import Source
from graphql.validation import validate

from ..executor import execute


def resolved(value):
    return Promise.fulfilled(value)


def rejected(error):
    return Promise.rejected(error)


def graphql(schema, request_string='', root_value=None, context_value=None,
            variable_values=None, operation_name=None, executor=None,
            return_promise=False, middleware=None):
    try:
        source = Source(request_string, 'GraphQL request')
        ast = parse(source)
        validation_errors = validate(schema, ast)
        if validation_errors:
            return ExecutionResult(
                errors=validation_errors,
                invalid=True,
            )
        return execute(
            schema,
            ast,
            root_value,
            context_value,
            operation_name=operation_name,
            variable_values=variable_values or {},
            executor=executor,
            return_promise=return_promise,
            middleware=middleware,
        )
    except Exception as e:
        return ExecutionResult(
            errors=[e],
            invalid=True,
        )
