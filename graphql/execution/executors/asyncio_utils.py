from inspect import isasyncgen  # type: ignore
from asyncio import ensure_future, wait, CancelledError
from inspect import isasyncgen

from rx import AnonymousObserver, Observable
from rx.concurrency import current_thread_scheduler
from rx.core import (Disposable, Observable, ObservableBase, Observer,
                     ObserverBase)
from rx.core.anonymousobserver import AnonymousObserver
from rx.core.autodetachobserver import AutoDetachObserver
from rx import AnonymousObservable


# class AsyncgenDisposable(Disposable):
#     """Represents a Disposable that disposes the asyncgen automatically."""

#     def __init__(self, asyncgen):
#         """Initializes a new instance of the AsyncgenDisposable class."""

#         self.asyncgen = asyncgen
#         self.is_disposed = False

#         super(AsyncgenDisposable, self).__init__()

#     def dispose(self):
#         """Sets the status to disposed"""
#         self.asyncgen.aclose()
#         self.is_disposed = True


class AsyncgenObserver(AutoDetachObserver):
    def __init__(self, asyncgen, *args, **kwargs):
        self._asyncgen = asyncgen
        self.is_disposed = False
        super(AsyncgenObserver, self).__init__(*args, **kwargs)

    async def dispose_asyncgen(self):
        if self.is_disposed:
            return

        try:
            # await self._asyncgen.aclose()
            await self._asyncgen.athrow(StopAsyncIteration)
            self.is_disposed = True
        except:
            pass

    def dispose(self):
        if self.is_disposed:
            return
        disposed = super(AsyncgenObserver, self).dispose()
        # print("DISPOSE observer!", disposed)
        ensure_future(self.dispose_asyncgen())


class AsyncgenObservable(ObservableBase):
    """Class to create an Observable instance from a delegate-based
    implementation of the Subscribe method."""

    def __init__(self, subscribe, asyncgen):
        """Creates an observable sequence object from the specified
        subscription function.

        Keyword arguments:
        :param types.FunctionType subscribe: Subscribe method implementation.
        """

        self._subscribe = subscribe
        self._asyncgen = asyncgen
        super(AsyncgenObservable, self).__init__()

    def _subscribe_core(self, observer):
        # print("GET SUBSCRIBER", observer)
        return self._subscribe(observer)
        # print("SUBSCRIBER RESULT", subscriber)
        # return subscriber

    def subscribe(self, on_next=None, on_error=None, on_completed=None, observer=None):

        if isinstance(on_next, Observer):
            observer = on_next
        elif hasattr(on_next, "on_next") and callable(on_next.on_next):
            observer = on_next
        elif not observer:
            observer = AnonymousObserver(on_next, on_error, on_completed)

        auto_detach_observer = AsyncgenObserver(self._asyncgen, observer)

        def fix_subscriber(subscriber):
            """Fixes subscriber to make sure it returns a Disposable instead
            of None or a dispose function"""

            if not hasattr(subscriber, "dispose"):
                subscriber = Disposable.create(subscriber)

            return subscriber

        def set_disposable(scheduler=None, value=None):
            try:
                subscriber = self._subscribe_core(auto_detach_observer)
            except Exception as ex:
                if not auto_detach_observer.fail(ex):
                    raise
            else:
                auto_detach_observer.disposable = fix_subscriber(subscriber)

        def dispose():
            async def await_task():
                await task

            task.cancel()
            ensure_future(await_task(), loop=loop)

        return dispose

    return AnonymousObservable(emit)


async def iterate_asyncgen(asyncgen, observer):
    try:
        async for item in asyncgen:
            observer.on_next(item)
        observer.on_completed()
    except CancelledError:
        pass
    except Exception as e:
        observer.on_error(e)
