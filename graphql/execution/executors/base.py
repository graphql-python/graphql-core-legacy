from abc import ABC, abstractmethod


class BaseExecutor(ABC):

    @abstractmethod
    def wait_until_finished(self):
        pass

    @abstractmethod
    async def wait_until_finished_async(self):
        pass

    @abstractmethod
    def clean(self):
        pass
