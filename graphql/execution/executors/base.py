from abc import ABCMeta, abstractmethod
import six


class BaseExecutor(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def wait_until_finished(self):
        pass

    @abstractmethod
    def wait_until_finished_async(self):
        pass

    @abstractmethod
    def clean(self):
        pass
