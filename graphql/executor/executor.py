# -*- coding: utf-8 -*-
import collections
import re
from graphql.error import GraphQLError, format_error
from graphql.utils import type_from_ast, is_nullish
from graphql.language import kinds as Kind
from graphql.executor.values import get_variable_values, get_argument_values
from graphql.type.definition import (
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLList,
    GraphQLNonNull,
)
from graphql.type.introspection import (
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
)
from graphql.type.directives import (
    GraphQLIncludeDirective,
    GraphQLSkipDirective,
)

Undefined = object()


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


class ExecutionContext(object):
    """Data that must be available at all points during query execution.

    Namely, schema of the type system that is currently executing,
    and the fragments defined in the query document"""
    def __init__(self, schema, root, ast, operation_name, args, errors):
        """Constructs a ExecutionContext object from the arguments passed
        to execute, which we will pass throughout the other execution
        methods."""
        operations = {}
        fragments = {}
        for statement in ast['definitions']:
            if statement['kind'] == Kind.OPERATION_DEFINITION:
                name = ''
                if statement.get('name'):
                    name = statement['name']['value']
                operations[name] = statement
            elif statement['kind'] == Kind.FRAGMENT_DEFINITION:
                fragments[statement['name']['value']] = statement
        if not operation_name and len(operations) != 1:
            raise GraphQLError('Must provide operation name '
                'if query contains multiple operations')
        op_name = operation_name or operations.keys()[0]
        operation = operations.get(op_name)
        if not operation:
            raise GraphQLError('Unknown operation name: {}'.format(op_name))
        variables = get_variable_values(schema, operation['variableDefinitions'] or [], args)

        self.schema = schema
        self.fragments = fragments
        self.root = root
        self.operation = operation
        self.variables = variables
        self.errors = errors


class ExecutionResult(object):
    """The result of execution. `data` is the result of executing the
    query, `errors` is null if no errors occurred, and is a
    non-empty array if an error occurred."""

    def __init__(self, data, errors=None):
        self.data = data
        self.errors = errors


def execute(schema, root, ast, operation_name='', args=None):
    """Implements the "Evaluating requests" section of the spec."""
    assert schema, 'Must provide schema'
    errors = []
    try:
        ctx = ExecutionContext(schema, root, ast, operation_name, args, errors)
        data = execute_operation(ctx, root, ctx.operation)
    except Exception as e:
        errors.append(e)
        data = None
    if not errors:
        return ExecutionResult(data)
    return ExecutionResult(data, map(format_error, errors))


def execute_operation(ctx, root, operation):
    """Implements the "Evaluating operations" section of the spec."""
    type = get_operation_root_type(ctx.schema, operation)
    fields = collect_fields(ctx, type, operation['selectionSet'], {}, set())
    if operation['operation'] == 'mutation':
        return execute_fields_serially(ctx, type, root, fields)
    return execute_fields(ctx, type, root, fields)


def get_operation_root_type(schema, operation):
    op = operation['operation']
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


def execute_fields_serially(ctx, parent_type, source, fields):
    """Implements the "Evaluating selection sets" section of the spec
    for "write" mode."""
    results = {}
    for response_name, field_asts in fields.items():
        result = resolve_field(ctx, parent_type, source, field_asts)
        if result is not Undefined:
            results[response_name] = result
    return results


def execute_fields(ctx, parent_type, source, fields):
    """Implements the "Evaluating selection sets" section of the spec
    for "read" mode."""
    # FIXME: just fallback to serial execution for now.
    return execute_fields_serially(ctx, parent_type, source, fields)


def collect_fields(ctx, type, selection_set, fields, prev_fragment_names):
    for selection in selection_set['selections']:
        kind = selection['kind']
        directives = selection.get('directives')
        if kind == Kind.FIELD:
            if not should_include_node(ctx, directives):
                continue
            name = get_field_entry_key(selection)
            if name not in fields:
                fields[name] = []
            fields[name].append(selection)
        elif kind == Kind.INLINE_FRAGMENT:
            if not should_include_node(ctx, directives) or \
                not does_fragment_condition_match(ctx, selection, type):
                continue
            collect_fields(ctx, type, selection['selectionSet'],
                fields, prev_fragment_names)
        elif kind == Kind.FRAGMENT_SPREAD:
            frag_name = selection['name']['value']
            if frag_name in prev_fragment_names or \
                not should_include_node(ctx, directives):
                continue
            prev_fragment_names.add(frag_name)
            fragment = ctx.fragments.get(frag_name)
            frag_directives = fragment.get('directives')
            if not fragment or \
                not should_include_node(ctx, directives) or \
                not does_fragment_condition_match(ctx, fragment, type):
                continue
            collect_fields(ctx, type, fragment['selectionSet'],
                fields, prev_fragment_names)
    return fields


def should_include_node(ctx, directives):
    """Determines if a field should be included based on the @include and
    @skip directives, where @skip has higher precidence than @include."""
    if directives:
        skip_ast = None
        for directive in directives:
            if directive['name']['value'] == GraphQLSkipDirective.name:
                skip_ast = directive
                break
        if skip_ast:
            args = get_argument_values(
                GraphQLSkipDirective.args,
                skip_ast['arguments'],
                ctx.variables,
            )
            return not args.get('if')

        include_ast = None
        for directive in directives:
            if directive['name']['value'] == GraphQLIncludeDirective.name:
                include_ast = directive
                break
        if include_ast:
            args = get_argument_values(
                GraphQLIncludeDirective.args,
                include_ast['arguments'],
                ctx.variables,
            )
            return bool(args.get('if'))

    return True


def does_fragment_condition_match(ctx, fragment, type_):
    conditional_type = type_from_ast(ctx.schema, fragment['typeCondition'])
    if type(conditional_type) == type(type_):
        return True
    if isinstance(conditional_type, GraphQLInterfaceType) or \
        isinstance(conditional_type, GraphQLUnionType):
        return conditional_type.is_possible_type(type_)
    return False


def get_field_entry_key(node):
    """Implements the logic to compute the key of a given field’s entry"""
    if node['alias']:
        return node['alias']['value']
    return node['name']['value']


def resolve_field(ctx, parent_type, source, field_asts):
    """A wrapper function for resolving the field, that catches the error
    and adds it to the context's global if the error is not rethrowable."""
    field_ast = field_asts[0]

    field_def = get_field_def(ctx.schema, parent_type, field_ast)
    if not field_def:
        return Undefined

    field_type = field_def.type
    resolve_fn = field_def.resolver or default_resolve_fn

    # Build a dict of arguments from the field.arguments AST, using the variables scope to fulfill any variable references.
    # TODO: find a way to memoize, in case this field is within a list type.
    if field_def.args is not None:
        args = get_argument_values(
            field_def.args, field_ast['arguments'], ctx.variables
        )
    else:
        args = None

    # If an error occurs while calling the field `resolve` function, ensure that it is wrapped as a GraphQLError with locations. Log this error and return null if allowed, otherwise throw the error so the parent field can handle it.
    try:
        result = resolve_fn(source, args, ctx.root,
            # TODO: provide all fieldASTs, not just the first field
            field_ast,
            field_type, parent_type, ctx.schema
        )
    except Exception as e:
        reported_error = GraphQLError(str(e), [field_ast], e)
        if isinstance(field_type, GraphQLNonNull):
            raise reported_error
        ctx.errors.append(reported_error)
        return None
    
    return complete_value_catching_error(
        ctx, field_type, field_asts, result
    )


def complete_value_catching_error(ctx, field_type, field_asts, result):
    # If the field type is non-nullable, then it is resolved without any
    # protection from errors.
    if isinstance(field_type, GraphQLNonNull):
        return complete_value(ctx, field_type, field_asts, result)

    # Otherwise, error protection is applied, logging the error and
    # resolving a null value for this field if one is encountered.
    try:
        return complete_value(ctx, field_type, field_asts, result)
    except Exception as e:
        ctx.errors.append(e)
        return None


def complete_value(ctx, field_type, field_asts, result):
    """Implements the instructions for completeValue as defined in the
    "Field entries" section of the spec.

    If the field type is Non-Null, then this recursively completes the value for the inner type. It throws a field error if that completion returns null, as per the "Nullability" section of the spec.

    If the field type is a List, then this recursively completes the value for the inner type on each item in the list.

    If the field type is a Scalar or Enum, ensures the completed value is a legal value of the type by calling the `coerce` method of GraphQL type definition.

    Otherwise, the field type expects a sub-selection set, and will complete the value by evaluating all sub-selections."""
    # If field type is NonNull, complete for inner type, and throw field error if result is null.
    if isinstance(field_type, GraphQLNonNull):
        completed = complete_value(
            ctx, field_type.of_type, field_asts, result
        )
        if completed is None:
            raise GraphQLError(
                'Cannot return null for non-nullable type.',
                field_asts
            )
        return completed

    # If result is null-like, return null.
    if is_nullish(result):
        return None

    # If field type is List, complete each item in the list with the inner type
    if isinstance(field_type, GraphQLList):
        assert isinstance(result, collections.Iterable), \
            'User Error: expected iterable, but did not find one.'

        item_type = field_type.of_type
        return [complete_value_catching_error(
            ctx, item_type, field_asts, item
        ) for item in result]

    # If field type is Scalar or Enum, coerce to a valid value, returning null if coercion is not possible.
    if isinstance(field_type, GraphQLScalarType) or \
        isinstance(field_type, GraphQLEnumType):
        coerced_result = field_type.coerce(result)
        if is_nullish(coerced_result):
            return None
        return coerced_result

    # Field type must be Object, Interface or Union and expect sub-selections.
    if isinstance(field_type, GraphQLObjectType):
        object_type = field_type
    elif isinstance(field_type, GraphQLInterfaceType) or \
        isinstance(field_type, GraphQLUnionType):
        object_type = field_type.resolve_type(result)
    else:
        object_type = None

    if not object_type:
        return None

    # Collect sub-fields to execute to complete this value.
    subfield_asts = {}
    visited_fragment_names = set()
    for field_ast in field_asts:
        selection_set = field_ast.get('selectionSet')
        if selection_set:
            subfield_asts = collect_fields(ctx, object_type, selection_set,
                subfield_asts, visited_fragment_names)
    
    return execute_fields(ctx, object_type, result, subfield_asts)


CAMEL_CASE_PATTERN = re.compile(r'([a-z])([A-Z]+)')


def camel_to_snake_case(name):
    return CAMEL_CASE_PATTERN.sub(lambda m: m.group(1) + '_' + m.group(2).lower(), name)


def default_resolve_fn(source, args, root, field_ast, *_):
    """If a resolve function is not given, then a default resolve behavior is used which takes the property of the source object of the same name as the field and returns it as the result, or if it's a function, returns the result of calling that function."""
    name = field_ast['name']['value']
    property = getattr(source, name, None)
    if property is None:
        property = getattr(source, camel_to_snake_case(name), None)
    if callable(property):
        return property()
    return property


def get_field_def(schema, parent_type, field_ast):
    """This method looks up the field on the given type defintion.
    It has special casing for the two introspection fields, __schema
    and __typename. __typename is special because it can always be
    queried as a field, even in situations where no other fields
    are allowed, like on a Union. __schema could get automatically
    added to the query type, but that would require mutating type
    definitions, which would cause issues."""
    name = field_ast['name']['value']
    if name == SchemaMetaFieldDef.name and \
        schema.get_query_type() == parent_type:
        return SchemaMetaFieldDef
    elif name == TypeMetaFieldDef.name and \
        schema.get_query_type() == parent_type:
        return TypeMetaFieldDef
    elif name == TypeNameMetaFieldDef.name:
        return TypeNameMetaFieldDef
    return parent_type.get_fields().get(name)
