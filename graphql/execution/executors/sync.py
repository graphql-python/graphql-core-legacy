from .base import BaseExecutor

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Callable


class SyncExecutor(BaseExecutor):
    def wait_until_finished(self):
        # type: () -> None
        pass

    async def wait_until_finished_async(self):
        raise NotImplementedError

    def clean(self):
        pass

    def execute(self, fn, *args, **kwargs):
        # type: (Callable, *Any, **Any) -> Any
        return fn(*args, **kwargs)
