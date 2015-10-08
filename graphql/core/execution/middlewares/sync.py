from ...error import GraphQLError
from ...pyutils.defer import Deferred


class SynchronousExecutionMiddleware(object):
    def run_resolve_fn(self, resolver, original_resolver):
        result = resolver()
        if isinstance(result, Deferred):
            raise GraphQLError('You cannot return a Deferred from a resolver when using SynchronousExecutionMiddleware')

        return result

    def execution_result(self, executor):
        result = executor()
        return result.result
