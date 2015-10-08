# flake8: noqa
from asyncio import Future, ensure_future, iscoroutine

from ...pyutils.defer import Deferred


def process_future_result(deferred):
    def handle_future_result(future):
        exception = future.exception()
        if exception:
            deferred.errback(exception)

        else:
            deferred.callback(future.result())

    return handle_future_result


class AsyncioExecutionMiddleware(object):
    @staticmethod
    def run_resolve_fn(resolver, original_resolver):
        result = resolver()
        if isinstance(result, Future) or iscoroutine(result):
            future = ensure_future(result)
            d = Deferred()
            future.add_done_callback(process_future_result(d))
            return d

        return result

    @staticmethod
    def execution_result(executor):
        future = Future()
        result = executor()
        assert isinstance(result, Deferred), 'Another middleware has converted the execution result ' \
                                             'away from a Deferred.'

        result.add_callbacks(future.set_result, future.set_exception)
        return future
