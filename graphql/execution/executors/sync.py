class SyncExecutor(object):

    def wait_until_finished(self):
        pass

    def clean(self):
        pass

    def execute(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)
