from ..execution import ExecutionResult
from ..validation import validate


# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Union
    from ..language.ast import Document
    from ..type.schema import GraphQLSchema


def validate_document_ast(
    schema,  # type: GraphQLSchema
    document_ast,  # type: Document
    **kwargs  # type: Any
):
    # type: (...) -> Union[ExecutionResult, None]
    do_validation = kwargs.get("validate", True)
    if do_validation:
        validation_errors = validate(schema, document_ast)
        if validation_errors:
            return ExecutionResult(errors=validation_errors, invalid=True)
    return None
