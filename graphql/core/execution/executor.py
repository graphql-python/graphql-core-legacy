import collections
import functools
import logging

from ..error import GraphQLError
from ..language import ast
from ..language.parser import parse
from ..language.source import Source
from ..pyutils.default_ordered_dict import DefaultOrderedDict
from ..pyutils.defer import (Deferred, DeferredDict, DeferredList, defer,
                             succeed)
from ..type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                    GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                    GraphQLUnionType)
from ..validation import validate
from .base import (ExecutionContext, ExecutionResult, ResolveInfo, Undefined,
                   collect_fields, default_resolve_fn, get_field_def,
                   get_operation_root_type)


logger = logging.getLogger(__name__)


class Executor(object):

    def __init__(self, execution_middlewares=None, default_resolver=default_resolve_fn, map_type=dict):
        assert issubclass(map_type, collections.MutableMapping)

        self._execution_middlewares = execution_middlewares or []
        self._default_resolve_fn = default_resolver
        self._map_type = map_type
        self._enforce_strict_ordering = issubclass(map_type, collections.OrderedDict)

    @property
    def enforce_strict_ordering(self):
        return self._enforce_strict_ordering

    @property
    def map_type(self):
        return self._map_type

    def execute(self, schema, request='', root=None, args=None, operation_name=None, request_context=None,
                execute_serially=False, validate_ast=True):

        curried_execution_function = functools.partial(
            self._execute,
            schema,
            request,
            root,
            args,
            operation_name,
            request_context,
            execute_serially,
            validate_ast
        )

        for middleware in self._execution_middlewares:
            if hasattr(middleware, 'execution_result'):
                curried_execution_function = functools.partial(middleware.execution_result, curried_execution_function)

        return curried_execution_function()

    def _execute(self, schema, request, root, args, operation_name, request_context, execute_serially, validate_ast):
        if not isinstance(request, ast.Document):
            if not isinstance(request, Source):
                request = Source(request, 'GraphQL request')

            request = parse(request)

        if validate_ast:
            validation_errors = validate(schema, request)
            if validation_errors:
                return succeed(ExecutionResult(
                    errors=validation_errors,
                    invalid=True,
                ))

        return self._execute_graphql_query(
            schema,
            root or object(),
            request,
            operation_name,
            args or {},
            request_context or {},
            execute_serially)

    def _execute_graphql_query(self, schema, root, ast, operation_name, args, request_context, execute_serially=False):
        ctx = ExecutionContext(schema, root, ast, operation_name, args, request_context)

        return defer(self._execute_operation, ctx, root, ctx.operation, execute_serially) \
            .add_errback(
            lambda error: ctx.errors.append(error)
        ) \
            .add_callback(
            lambda data: ExecutionResult(data, ctx.errors),
        )

    def _execute_operation(self, ctx, root, operation, execute_serially):
        type = get_operation_root_type(ctx.schema, operation)

        if operation.operation == 'mutation' or execute_serially:
            execute_serially = True

        fields = DefaultOrderedDict(list) \
            if (execute_serially or self._enforce_strict_ordering) \
            else collections.defaultdict(list)

        fields = collect_fields(ctx, type, operation.selection_set, fields, set())

        if execute_serially:
            return self._execute_fields_serially(ctx, type, root, fields)

        return self._execute_fields(ctx, type, root, fields)

    def _execute_fields_serially(self, execution_context, parent_type, source_value, fields):
        def execute_field_callback(results, response_name):
            field_asts = fields[response_name]
            result = self._resolve_field(execution_context, parent_type, source_value, field_asts)
            if result is Undefined:
                return results

            def collect_result(resolved_result):
                results[response_name] = resolved_result
                return results

            if isinstance(result, Deferred):
                return succeed(result).add_callback(collect_result)

            else:
                return collect_result(result)

        def execute_field(prev_deferred, response_name):
            return prev_deferred.add_callback(execute_field_callback, response_name)

        return functools.reduce(execute_field, fields.keys(), succeed(self._map_type()))

    def _execute_fields(self, execution_context, parent_type, source_value, fields):
        contains_deferred = False

        results = self._map_type()
        for response_name, field_asts in fields.items():
            result = self._resolve_field(execution_context, parent_type, source_value, field_asts)
            if result is Undefined:
                continue

            results[response_name] = result
            if isinstance(result, Deferred):
                contains_deferred = True

        if not contains_deferred:
            return results

        return DeferredDict(results)

    def _resolve_field(self, execution_context, parent_type, source, field_asts):
        field_ast = field_asts[0]
        field_name = field_ast.name.value

        field_def = get_field_def(execution_context.schema, parent_type, field_name)
        if not field_def:
            return Undefined

        return_type = field_def.type
        resolve_fn = field_def.resolver or self._default_resolve_fn

        # Build a dict of arguments from the field.arguments AST, using the variables scope to
        # fulfill any variable references.
        args = execution_context.get_argument_values(field_def, field_ast)

        # The resolve function's optional third argument is a collection of
        # information about the current execution state.
        info = ResolveInfo(
            field_name,
            field_asts,
            return_type,
            parent_type,
            execution_context
        )

        result = self.resolve_or_error(resolve_fn, source, args, info)
        return self.complete_value_catching_error(
            execution_context, return_type, field_asts, info, result
        )

    def complete_value_catching_error(self, ctx, return_type, field_asts, info, result):
        # If the field type is non-nullable, then it is resolved without any
        # protection from errors.
        if isinstance(return_type, GraphQLNonNull):
            return self.complete_value(ctx, return_type, field_asts, info, result)

        # Otherwise, error protection is applied, logging the error and
        # resolving a null value for this field if one is encountered.
        try:
            completed = self.complete_value(ctx, return_type, field_asts, info, result)
            if isinstance(completed, Deferred):
                def handle_error(error):
                    ctx.errors.append(error)
                    return None

                return completed.add_errback(handle_error)

            return completed
        except Exception as e:
            ctx.errors.append(e)
            return None

    def complete_value(self, ctx, return_type, field_asts, info, result):
        """
        Implements the instructions for completeValue as defined in the
        "Field entries" section of the spec.

        If the field type is Non-Null, then this recursively completes the value for the inner type. It throws a field
        error if that completion returns null, as per the "Nullability" section of the spec.

        If the field type is a List, then this recursively completes the value for the inner type on each item in the
        list.

        If the field type is a Scalar or Enum, ensures the completed value is a legal value of the type by calling the
        `serialize` method of GraphQL type definition.

        Otherwise, the field type expects a sub-selection set, and will complete the value by evaluating all
        sub-selections.
        """
        # If field type is NonNull, complete for inner type, and throw field error if result is null.
        if isinstance(result, Deferred):
            return result.add_callbacks(
                lambda resolved: self.complete_value(
                    ctx,
                    return_type,
                    field_asts,
                    info,
                    resolved
                ),
                lambda error: GraphQLError(error.value and str(error.value), field_asts, error)
            )

        if isinstance(result, Exception):
            raise GraphQLError(str(result), field_asts, result)

        if isinstance(return_type, GraphQLNonNull):
            completed = self.complete_value(
                ctx, return_type.of_type, field_asts, info, result
            )
            if completed is None:
                raise GraphQLError(
                    'Cannot return null for non-nullable field {}.{}.'.format(info.parent_type, info.field_name),
                    field_asts
                )

            return completed

        # If result is null-like, return null.
        if result is None:
            return None

        # If field type is List, complete each item in the list with the inner type
        if isinstance(return_type, GraphQLList):
            assert isinstance(result, collections.Iterable), \
                ('User Error: expected iterable, but did not find one' +
                 'for field {}.{}').format(info.parent_type, info.field_name)

            item_type = return_type.of_type
            completed_results = []
            contains_deferred = False
            for item in result:
                completed_item = self.complete_value_catching_error(ctx, item_type, field_asts, info, item)
                if not contains_deferred and isinstance(completed_item, Deferred):
                    contains_deferred = True

                completed_results.append(completed_item)

            return DeferredList(completed_results) if contains_deferred else completed_results

        # If field type is Scalar or Enum, serialize to a valid value, returning null if coercion is not possible.
        if isinstance(return_type, (GraphQLScalarType, GraphQLEnumType)):
            serialized_result = return_type.serialize(result)

            if serialized_result is None:
                return None

            return serialized_result

        runtime_type = None

        # Field type must be Object, Interface or Union and expect sub-selections.
        if isinstance(return_type, GraphQLObjectType):
            runtime_type = return_type

        elif isinstance(return_type, (GraphQLInterfaceType, GraphQLUnionType)):
            runtime_type = return_type.resolve_type(result, info)
            if runtime_type and not return_type.is_possible_type(runtime_type):
                raise GraphQLError(
                    u'Runtime Object type "{}" is not a possible type for "{}".'.format(runtime_type, return_type),
                    field_asts
                )

        if not runtime_type:
            return None

        if runtime_type.is_type_of and not runtime_type.is_type_of(result, info):
            raise GraphQLError(
                u'Expected value of type "{}" but got {}.'.format(return_type, type(result).__name__),
                field_asts
            )

        # Collect sub-fields to execute to complete this value.
        subfield_asts = DefaultOrderedDict(list) if self._enforce_strict_ordering else collections.defaultdict(list)
        visited_fragment_names = set()
        for field_ast in field_asts:
            selection_set = field_ast.selection_set
            if selection_set:
                subfield_asts = collect_fields(
                    ctx, runtime_type, selection_set,
                    subfield_asts, visited_fragment_names
                )

        return self._execute_fields(ctx, runtime_type, result, subfield_asts)

    def resolve_or_error(self, resolve_fn, source, args, info):
        curried_resolve_fn = functools.partial(resolve_fn, source, args, info)

        try:
            for middleware in self._execution_middlewares:
                if hasattr(middleware, 'run_resolve_fn'):
                    curried_resolve_fn = functools.partial(middleware.run_resolve_fn, curried_resolve_fn, resolve_fn)

            return curried_resolve_fn()
        except Exception as e:
            logger.exception("An error occurred while resolving field %s.%s"
                             % (info.parent_type.name, info.field_name))
            return e
