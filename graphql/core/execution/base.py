# -*- coding: utf-8 -*-
from ..defer import DeferredException
from ..error import GraphQLError
from ..language import ast
from ..type.definition import (
    GraphQLInterfaceType,
    GraphQLUnionType,
)
from ..type.directives import (
    GraphQLIncludeDirective,
    GraphQLSkipDirective,
)
from ..type.introspection import (
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
)
from ..utils.type_from_ast import type_from_ast
from .values import get_argument_values, get_variable_values

Undefined = object()


class ExecutionContext(object):
    """Data that must be available at all points during query execution.

    Namely, schema of the type system that is currently executing,
    and the fragments defined in the query document"""

    def __init__(self, schema, root, document_ast, operation_name, args, request_context):
        """Constructs a ExecutionContext object from the arguments passed
        to execute, which we will pass throughout the other execution
        methods."""
        errors = []
        operations = {}
        fragments = {}
        for statement in document_ast.definitions:
            if isinstance(statement, ast.OperationDefinition):
                name = ''
                if statement.name:
                    name = statement.name.value
                operations[name] = statement
            elif isinstance(statement, ast.FragmentDefinition):
                fragments[statement.name.value] = statement
        if not operation_name and len(operations) != 1:
            raise GraphQLError(
                'Must provide operation name '
                'if query contains multiple operations')
        op_name = operation_name or next(iter(operations.keys()))
        operation = operations.get(op_name)
        if not operation:
            raise GraphQLError('Unknown operation name: {}'.format(op_name))
        variables = get_variable_values(schema, operation.variable_definitions or [], args)

        self.schema = schema
        self.fragments = fragments
        self.root = root
        self.operation = operation
        self.variables = variables
        self.errors = errors
        self.request_context = request_context


class ExecutionResult(object):
    """The result of execution. `data` is the result of executing the
    query, `errors` is null if no errors occurred, and is a
    non-empty array if an error occurred."""

    def __init__(self, data=None, errors=None, invalid=False):
        self.data = data
        if errors:
            errors = [
                error.value if isinstance(error, DeferredException) else error
                for error in errors
            ]
        self.errors = errors
        if invalid:
            assert data is None
        self.invalid = invalid


def get_operation_root_type(schema, operation):
    op = operation.operation
    if op == 'query':
        return schema.get_query_type()
    elif op == 'mutation':
        mutation_type = schema.get_mutation_type()
        if not mutation_type:
            raise GraphQLError(
                'Schema is not configured for mutations',
                [operation]
            )
        return mutation_type
    raise GraphQLError(
        'Can only execute queries and mutations',
        [operation]
    )


def collect_fields(ctx, type, selection_set, fields, prev_fragment_names):
    for selection in selection_set.selections:
        directives = selection.directives
        if isinstance(selection, ast.Field):
            if not should_include_node(ctx, directives):
                continue
            name = get_field_entry_key(selection)
            if name not in fields:
                fields[name] = []
            fields[name].append(selection)
        elif isinstance(selection, ast.InlineFragment):
            if not should_include_node(ctx, directives) or \
                    not does_fragment_condition_match(ctx, selection, type):
                continue
            collect_fields(
                ctx, type, selection.selection_set,
                fields, prev_fragment_names)
        elif isinstance(selection, ast.FragmentSpread):
            frag_name = selection.name.value
            if frag_name in prev_fragment_names or \
                    not should_include_node(ctx, directives):
                continue
            prev_fragment_names.add(frag_name)
            fragment = ctx.fragments.get(frag_name)
            frag_directives = fragment.directives
            if not fragment or \
                    not should_include_node(ctx, frag_directives) or \
                    not does_fragment_condition_match(ctx, fragment, type):
                continue
            collect_fields(
                ctx, type, fragment.selection_set,
                fields, prev_fragment_names)
    return fields


def should_include_node(ctx, directives):
    """Determines if a field should be included based on the @include and
    @skip directives, where @skip has higher precidence than @include."""
    if directives:
        skip_ast = None
        for directive in directives:
            if directive.name.value == GraphQLSkipDirective.name:
                skip_ast = directive
                break
        if skip_ast:
            args = get_argument_values(
                GraphQLSkipDirective.args,
                skip_ast.arguments,
                ctx.variables,
            )
            return not args.get('if')

        include_ast = None
        for directive in directives:
            if directive.name.value == GraphQLIncludeDirective.name:
                include_ast = directive
                break
        if include_ast:
            args = get_argument_values(
                GraphQLIncludeDirective.args,
                include_ast.arguments,
                ctx.variables,
            )
            return bool(args.get('if'))

    return True


def does_fragment_condition_match(ctx, fragment, type_):
    conditional_type = type_from_ast(ctx.schema, fragment.type_condition)
    if conditional_type == type_:
        return True
    if isinstance(conditional_type, (GraphQLInterfaceType, GraphQLUnionType)):
        return conditional_type.is_possible_type(type_)
    return False


def get_field_entry_key(node):
    """Implements the logic to compute the key of a given field's entry"""
    if node.alias:
        return node.alias.value
    return node.name.value


class ResolveInfo(object):
    def __init__(self, field_name, field_asts, return_type, parent_type, context):
        self.field_name = field_name
        self.field_asts = field_asts
        self.return_type = return_type
        self.parent_type = parent_type
        self.context = context

    @property
    def schema(self):
        return self.context.schema

    @property
    def fragments(self):
        return self.context.fragments

    @property
    def root_value(self):
        return self.context.root_value

    @property
    def operation(self):
        return self.context.operation

    @property
    def variable_values(self):
        return self.context.variables

    @property
    def request_context(self):
        return self.context.request_context


def default_resolve_fn(source, args, info):
    """If a resolve function is not given, then a default resolve behavior is used which takes the property of the source object
    of the same name as the field and returns it as the result, or if it's a function, returns the result of calling that function."""
    name = info.field_name
    property = getattr(source, name, None)
    if callable(property):
        return property()
    return property


def get_field_def(schema, parent_type, field_name):
    """This method looks up the field on the given type defintion.
    It has special casing for the two introspection fields, __schema
    and __typename. __typename is special because it can always be
    queried as a field, even in situations where no other fields
    are allowed, like on a Union. __schema could get automatically
    added to the query type, but that would require mutating type
    definitions, which would cause issues."""
    if field_name == SchemaMetaFieldDef.name and schema.get_query_type() == parent_type:
        return SchemaMetaFieldDef
    elif field_name == TypeMetaFieldDef.name and schema.get_query_type() == parent_type:
        return TypeMetaFieldDef
    elif field_name == TypeNameMetaFieldDef.name:
        return TypeNameMetaFieldDef
    return parent_type.get_fields().get(field_name)
