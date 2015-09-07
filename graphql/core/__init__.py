from .executor.executor import execute, ExecutionResult
from .language.source import Source
from .language.parser import parse
from .validation import validate


def graphql(schema, request='', root=None, vars=None, operation_name=None):
    source = Source(request, 'GraphQL request')
    ast = parse(source)
    validation_errors = validate(schema, ast)
    if validation_errors:
        return ExecutionResult(
            data=None,
            errors=validation_errors,
        )
    return execute(
        schema,
        root or object(),
        ast,
        vars or {},
        operation_name
    )
