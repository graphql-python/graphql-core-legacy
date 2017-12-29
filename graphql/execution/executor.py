import collections
import functools
import logging
import sys

from promise import Promise, promise_for_dict, is_thenable
from rx import Observable

from graphql.execution.utils import complete_nonnull_value
from .base import (ExecutionContext, ExecutionResult, ResolveInfo,
                   collect_fields, default_resolve_fn, get_field_def,
                   get_operation_root_type, SubscriberExecutionContext)
from .executors.sync import SyncExecutor
from .middleware import MiddlewareManager
from ..error import GraphQLError, GraphQLLocatedError
from ..pyutils.default_ordered_dict import DefaultOrderedDict
from ..pyutils.ordereddict import OrderedDict
from ..type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                    GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                    GraphQLSchema, GraphQLUnionType)
from ..utils.undefined import Undefined

logger = logging.getLogger(__name__)


def subscribe(*args, **kwargs):
    allow_subscriptions = kwargs.pop('allow_subscriptions', True)
    return execute(*args, allow_subscriptions=allow_subscriptions, **kwargs)


def execute(schema, document_ast, root_value=None, context_value=None,
            variable_values=None, operation_name=None, executor=None,
            return_promise=False, middleware=None, allow_subscriptions=False):
    assert schema, 'Must provide schema'
    assert isinstance(schema, GraphQLSchema), (
        'Schema must be an instance of GraphQLSchema. Also ensure that there are ' +
        'not multiple versions of GraphQL installed in your node_modules directory.'
    )
    if middleware:
        if not isinstance(middleware, MiddlewareManager):
            middleware = MiddlewareManager(*middleware)

        assert isinstance(middleware, MiddlewareManager), (
            'middlewares have to be an instance'
            ' of MiddlewareManager. Received "{}".'.format(middleware)
        )

    if executor is None:
        executor = SyncExecutor()

    context = ExecutionContext(
        schema,
        document_ast,
        root_value,
        context_value,
        variable_values,
        operation_name,
        executor,
        middleware,
        allow_subscriptions
    )

    def executor(v):
        return execute_operation(context, context.operation, root_value)

    def on_rejected(error):
        context.errors.append(error)
        return None

    def on_resolve(data):
        if isinstance(data, Observable):
            return data

        if not context.errors:
            return ExecutionResult(data=data)
        return ExecutionResult(data=data, errors=context.errors)

    promise = Promise.resolve(None).then(
        executor).catch(on_rejected).then(on_resolve)

    if not return_promise:
        context.executor.wait_until_finished()
        return promise.get()

    return promise


def execute_operation(exe_context, operation, root_value):
    type = get_operation_root_type(exe_context.schema, operation)
    fields = collect_fields(
        exe_context,
        type,
        operation.selection_set,
        DefaultOrderedDict(list),
        set()
    )

    if operation.operation == 'mutation':
        return execute_fields_serially(exe_context, type, root_value, fields)

    if operation.operation == 'subscription':
        if not exe_context.allow_subscriptions:
            raise Exception(
                "Subscriptions are not allowed. "
                "You will need to either use the subscribe function "
                "or pass allow_subscriptions=True"
            )
        return subscribe_fields(exe_context, type, root_value, fields)

    return execute_fields(exe_context, type, root_value, fields)


def execute_fields_serially(exe_context, parent_type, source_value, fields):
    def execute_field_callback(results, response_name):
        field_asts = fields[response_name]
        result = resolve_field(
            exe_context,
            parent_type,
            source_value,
            field_asts
        )
        if result is Undefined:
            return results

        if is_thenable(result):
            def collect_result(resolved_result):
                results[response_name] = resolved_result
                return results

            return result.then(collect_result, None)

        results[response_name] = result
        return results

    def execute_field(prev_promise, response_name):
        return prev_promise.then(lambda results: execute_field_callback(results, response_name))

    return functools.reduce(execute_field, fields.keys(), Promise.resolve(collections.OrderedDict()))


def execute_fields(exe_context, parent_type, source_value, fields):
    contains_promise = False

    final_results = OrderedDict()

    for response_name, field_asts in fields.items():
        result = resolve_field(exe_context, parent_type,
                               source_value, field_asts)
        if result is Undefined:
            continue

        final_results[response_name] = result
        if is_thenable(result):
            contains_promise = True

    if not contains_promise:
        return final_results

    return promise_for_dict(final_results)


def subscribe_fields(exe_context, parent_type, source_value, fields):
    exe_context = SubscriberExecutionContext(exe_context)

    def on_error(error):
        exe_context.report_error(error)

    def map_result(data):
        if exe_context.errors:
            result = ExecutionResult(data=data, errors=exe_context.errors)
        else:
            result = ExecutionResult(data=data)
        exe_context.reset()
        return result

    observables = []

    # assert len(fields) == 1, "Can only subscribe one element at a time."

    for response_name, field_asts in fields.items():

        result = subscribe_field(exe_context, parent_type,
                                 source_value, field_asts)
        if result is Undefined:
            continue

        def catch_error(error):
            exe_context.errors.append(error)
            return Observable.just(None)

        # Map observable results
        observable = result.catch_exception(catch_error).map(
            lambda data: map_result({response_name: data}))
        return observable
        observables.append(observable)

    return Observable.merge(observables)


def resolve_field(exe_context, parent_type, source, field_asts):
    field_ast = field_asts[0]
    field_name = field_ast.name.value

    field_def = get_field_def(exe_context.schema, parent_type, field_name)
    if not field_def:
        return Undefined

    return_type = field_def.type
    resolve_fn = field_def.resolver or default_resolve_fn

    # We wrap the resolve_fn from the middleware
    resolve_fn_middleware = exe_context.get_field_resolver(resolve_fn)

    # Build a dict of arguments from the field.arguments AST, using the variables scope to
    # fulfill any variable references.
    args = exe_context.get_argument_values(field_def, field_ast)

    # The resolve function's optional third argument is a context value that
    # is provided to every resolve function within an execution. It is commonly
    # used to represent an authenticated user, or request-specific caches.
    context = exe_context.context_value

    # The resolve function's optional third argument is a collection of
    # information about the current execution state.
    info = ResolveInfo(
        field_name,
        field_asts,
        return_type,
        parent_type,
        schema=exe_context.schema,
        fragments=exe_context.fragments,
        root_value=exe_context.root_value,
        operation=exe_context.operation,
        variable_values=exe_context.variable_values,
        context=context
    )

    executor = exe_context.executor
    result = resolve_or_error(resolve_fn_middleware,
                              source, info, args, executor)

    return complete_value_catching_error(
        exe_context,
        return_type,
        field_asts,
        info,
        result
    )


def subscribe_field(exe_context, parent_type, source, field_asts):
    field_ast = field_asts[0]
    field_name = field_ast.name.value

    field_def = get_field_def(exe_context.schema, parent_type, field_name)
    if not field_def:
        return Undefined

    return_type = field_def.type
    resolve_fn = field_def.resolver or default_resolve_fn

    # We wrap the resolve_fn from the middleware
    resolve_fn_middleware = exe_context.get_field_resolver(resolve_fn)

    # Build a dict of arguments from the field.arguments AST, using the variables scope to
    # fulfill any variable references.
    args = exe_context.get_argument_values(field_def, field_ast)

    # The resolve function's optional third argument is a context value that
    # is provided to every resolve function within an execution. It is commonly
    # used to represent an authenticated user, or request-specific caches.
    context = exe_context.context_value

    # The resolve function's optional third argument is a collection of
    # information about the current execution state.
    info = ResolveInfo(
        field_name,
        field_asts,
        return_type,
        parent_type,
        schema=exe_context.schema,
        fragments=exe_context.fragments,
        root_value=exe_context.root_value,
        operation=exe_context.operation,
        variable_values=exe_context.variable_values,
        context=context
    )

    executor = exe_context.executor
    result = resolve_or_error(resolve_fn_middleware,
                              source, info, args, executor)

    if isinstance(result, Exception):
        raise result

    if not isinstance(result, Observable):
        raise GraphQLError(
            'Subscription must return Async Iterable or Observable. Received: {}'.format(repr(result)))

    return result.map(functools.partial(
        complete_value_catching_error,
        exe_context,
        return_type,
        field_asts,
        info,
    ))


def resolve_or_error(resolve_fn, source, info, args, executor):
    try:
        return executor.execute(resolve_fn, source, info, **args)
    except Exception as e:
        logger.exception("An error occurred while resolving field {}.{}".format(
            info.parent_type.name, info.field_name
        ))
        e.stack = sys.exc_info()[2]
        return e


def complete_value_catching_error(exe_context, return_type, field_asts, info, result):
    # If the field type is non-nullable, then it is resolved without any
    # protection from errors.
    if isinstance(return_type, GraphQLNonNull):
        return complete_value(exe_context, return_type, field_asts, info, result)

    # Otherwise, error protection is applied, logging the error and
    # resolving a null value for this field if one is encountered.
    try:
        completed = complete_value(
            exe_context, return_type, field_asts, info, result)
        if is_thenable(completed):
            def handle_error(error):
                traceback = completed._traceback
                exe_context.report_error(error, traceback)
                return None

            return completed.catch(handle_error)

        return completed
    except Exception as e:
        traceback = sys.exc_info()[2]
        exe_context.report_error(e, traceback)
        return None


def complete_value(exe_context, return_type, field_asts, info, result):
    """
    Implements the instructions for completeValue as defined in the
    "Field entries" section of the spec.

    If the field type is Non-Null, then this recursively completes the value for the inner type. It throws a field
    error if that completion returns null, as per the "Nullability" section of the spec.

    If the field type is a List, then this recursively completes the value for the inner type on each item in the
    list.

    If the field type is a Scalar or Enum, ensures the completed value is a legal value of the type by calling the
    `serialize` method of GraphQL type definition.

    If the field is an abstract type, determine the runtime type of the value and then complete based on that type.

    Otherwise, the field type expects a sub-selection set, and will complete the value by evaluating all
    sub-selections.
    """
    # If field type is NonNull, complete for inner type, and throw field error
    # if result is null.

    if is_thenable(result):
        return Promise.resolve(result).then(
            lambda resolved: complete_value(
                exe_context,
                return_type,
                field_asts,
                info,
                resolved
            ),
            lambda error: Promise.rejected(
                GraphQLLocatedError(field_asts, original_error=error))
        )

    # print return_type, type(result)
    if isinstance(result, Exception):
        raise GraphQLLocatedError(field_asts, original_error=result)

    if isinstance(return_type, GraphQLNonNull):
        return complete_nonnull_value(exe_context, return_type, field_asts, info, result)

    # If result is null-like, return null.
    if result is None:
        return None

    try:
        return_type.complete_value(exe_context, return_type, field_asts, info, result)
    except AttributeError:
        assert False, u'Cannot complete value of unexpected type "{}".'.format(
            return_type)

