import collections
import functools
import logging
import sys

from promise import Promise, promise_for_dict, promisify

from ...error import GraphQLError, GraphQLLocatedError
from ...pyutils.default_ordered_dict import DefaultOrderedDict
from ...pyutils.ordereddict import OrderedDict
from ...type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                    GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                    GraphQLSchema, GraphQLUnionType)
from ..base import (ExecutionContext, ExecutionResult, ResolveInfo, Undefined,
                   collect_fields, default_resolve_fn, get_field_def,
                   get_operation_root_type)
from ..executors.sync import SyncExecutor
from ..middleware import MiddlewareManager

from .resolver import type_resolver
from .fragment import Fragment

logger = logging.getLogger(__name__)


def is_promise(obj):
    return type(obj) == Promise


def execute(schema, document_ast, root_value=None, context_value=None,
            variable_values=None, operation_name=None, executor=None,
            return_promise=False, middlewares=None):
    assert schema, 'Must provide schema'
    assert isinstance(schema, GraphQLSchema), (
        'Schema must be an instance of GraphQLSchema. Also ensure that there are ' +
        'not multiple versions of GraphQL installed in your node_modules directory.'
    )
    if middlewares:
        assert isinstance(middlewares, MiddlewareManager), (
            'middlewares have to be an instance'
            ' of MiddlewareManager. Received "{}".'.format(middlewares)
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
        middlewares
    )

    def executor(resolve, reject):
        return resolve(execute_operation(context, context.operation, root_value))

    def on_rejected(error):
        context.errors.append(error)
        return None

    def on_resolve(data):
        return ExecutionResult(data=data, errors=context.errors)

    promise = Promise(executor).catch(on_rejected).then(on_resolve)
    if return_promise:
        return promise
    context.executor.wait_until_finished()
    return promise.get()


def execute_operation(exe_context, operation, root_value):
    type = get_operation_root_type(exe_context.schema, operation)
    execute_serially = operation.operation == 'mutation'

    fragment = Fragment(type=type, selection_set=operation.selection_set, context=exe_context, execute_serially=execute_serially)
    return fragment.resolve(root_value)
