from functools import partial
from six import string_types

from ..execution import execute, ExecutionResult
from ..language.base import parse, print_ast
from ..language import ast
from ..validation import validate

from .base import GraphQLBackend, GraphQLDocument


def execute_and_validate(schema, document_ast, *args, **kwargs):
    do_validation = kwargs.get('validate', True)
    if do_validation:
        validation_errors = validate(schema, document_ast)
        if validation_errors:
            return ExecutionResult(
                errors=validation_errors,
                invalid=True,
            )

    return execute(schema, document_ast, *args, **kwargs)


class GraphQLCoreBackend(GraphQLBackend):
    def __init__(self, executor=None, **kwargs):
        super(GraphQLCoreBackend, self).__init__(**kwargs)
        self.execute_params = {"executor": executor}

    def document_from_string(self, schema, document_string):
        if isinstance(document_string, ast.Document):
            document_ast = document_string
            document_string = print_ast(document_ast)
        else:
            assert isinstance(document_string, string_types), "The query must be a string"
            document_ast = parse(document_string)
        return GraphQLDocument(
            schema=schema,
            document_string=document_string,
            document_ast=document_ast,
            execute=partial(execute_and_validate, schema, document_ast, **self.execute_params),
        )
