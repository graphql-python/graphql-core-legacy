from ...error import GraphQLError
from ...pyutils.defer import Deferred


class SynchronousExecutionMiddleware(object):

    @staticmethod
    def run_resolve_fn(resolver, original_resolver):
        result = resolver()
        if isinstance(result, Deferred):
            raise GraphQLError('You cannot return a Deferred from a resolver when using SynchronousExecutionMiddleware')

        return result

    @staticmethod
    def execution_result(executor):
        result = executor()
        return result.result
