# We keep the following imports to preserve compatibility
from .utils import (
    ExecutionContext,
    SubscriberExecutionContext,
    get_operation_root_type,
    collect_fields,
    should_include_node,
    does_fragment_condition_match,
    get_field_entry_key,
    default_resolve_fn,
    get_field_def
)
from ..error.format_error import format_error as default_format_error


class ExecutionResult(object):
    """The result of execution. `data` is the result of executing the
    query, `errors` is null if no errors occurred, and is a
    non-empty array if an error occurred."""

    __slots__ = 'data', 'errors', 'invalid', 'extensions'

    def __init__(self, data=None, errors=None, invalid=False, extensions=None):
        self.data = data
        self.errors = errors
        self.extensions = extensions or dict()

        if invalid:
            assert data is None

        self.invalid = invalid

    def __eq__(self, other):
        return (
            self is other or (
                isinstance(other, ExecutionResult) and
                self.data == other.data and
                self.errors == other.errors and
                self.invalid == other.invalid
            )
        )

    def to_dict(self, format_error=None, dict_class=dict):
        if format_error is None:
            format_error = default_format_error

        response = dict_class()
        if self.errors:
            response['errors'] = [format_error(e) for e in self.errors]

        if not self.invalid:
            response['data'] = self.data

        return response


class ResolveInfo(object):
    __slots__ = ('field_name', 'field_asts', 'return_type', 'parent_type',
                 'schema', 'fragments', 'root_value', 'operation', 'variable_values', 'context', 'path')

    def __init__(self, field_name, field_asts, return_type, parent_type,
                 schema, fragments, root_value, operation, variable_values, context, path=None):
        self.field_name = field_name
        self.field_asts = field_asts
        self.return_type = return_type
        self.parent_type = parent_type
        self.schema = schema
        self.fragments = fragments
        self.root_value = root_value
        self.operation = operation
        self.variable_values = variable_values
        self.context = context
        self.path = path


__all__ = [
    'ExecutionResult',
    'ResolveInfo',
    'ExecutionContext',
    'SubscriberExecutionContext',
    'get_operation_root_type',
    'collect_fields',
    'should_include_node',
    'does_fragment_condition_match',
    'get_field_entry_key',
    'default_resolve_fn',
    'get_field_def',
]
