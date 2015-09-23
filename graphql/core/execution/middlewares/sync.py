from graphql.core.defer import Deferred
from graphql.core.error import GraphQLError


class SynchronousExecutionMiddleware(object):
    def run_resolve_fn(self, resolver):
        result = resolver()
        if isinstance(result, Deferred):
            raise GraphQLError('You cannot return a Deferred from a resolver when using SynchronousExecutionMiddleware')

        return result

    def execution_result(self, executor):
        result = executor()
        return result.result
