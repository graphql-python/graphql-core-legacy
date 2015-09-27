from .execution import ExecutionResult, execute
from .language.parser import parse
from .language.source import Source
from .validation import validate


def graphql(schema, request='', root=None, vars=None, operation_name=None):
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
            vars or {},
        )
    except Exception as e:
        return ExecutionResult(
            errors=[e],
            invalid=True,
        )
