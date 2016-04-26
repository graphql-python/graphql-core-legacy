from __future__ import absolute_import

from asyncio import Future, ensure_future, get_event_loop, iscoroutine, wait

from graphql.pyutils.aplus import Promise


def process_future_result(promise):
    def handle_future_result(future):
        exception = future.exception()
        if exception:
            promise.reject(exception)
        else:
            promise.fulfill(future.result())

    return handle_future_result


class AsyncioExecutor(object):

    def __init__(self):
        self.loop = get_event_loop()
        self.futures = []

    def wait_until_finished(self):
        self.loop.run_until_complete(wait(self.futures))

    def execute(self, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        if isinstance(result, Future) or iscoroutine(result):
            promise = Promise()
            future = ensure_future(result)
            self.futures.append(future)
            future.add_done_callback(process_future_result(promise))
            return promise
        return result
