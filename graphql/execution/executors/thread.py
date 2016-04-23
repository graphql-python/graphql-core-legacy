from threading import Thread
from ...pyutils.aplus import Promise
from .utils import process


class ThreadExecutor(object):
    def __init__(self):
        self.threads = []

    def wait_until_finished(self):
        for thread in self.threads:
            thread.join()

    def execute(self, fn, *args, **kwargs):
        promise = Promise()
        thread = Thread(target=process, args=(promise, fn, args, kwargs))
        thread.start()
        self.threads.append(thread)
        return promise
