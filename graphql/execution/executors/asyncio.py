from __future__ import absolute_import

from asyncio import Future, ensure_future, get_event_loop, iscoroutine, wait


class AsyncioExecutor(object):

    def __init__(self):
        self.loop = get_event_loop()
        self.futures = []

    def wait_until_finished(self):
        # if there are futures to wait for
        if self.futures:
            # wait for the futures to finish
            self.loop.run_until_complete(wait(self.futures))

    def execute(self, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        if isinstance(result, Future) or iscoroutine(result):
            future = ensure_future(result)
            self.futures.append(future)
            return future
        return result
