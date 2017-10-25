from inspect import isasyncgen
from asyncio import ensure_future
from rx import Observable, AnonymousObserver
from rx.core import ObservableBase, Disposable, ObserverBase

from rx.concurrency import current_thread_scheduler

from rx.core import Observer, Observable, Disposable
from rx.core.anonymousobserver import AnonymousObserver
from rx.core.autodetachobserver import AutoDetachObserver


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

        # Subscribe needs to set up the trampoline before for subscribing.
        # Actually, the first call to Subscribe creates the trampoline so
        # that it may assign its disposable before any observer executes
        # OnNext over the CurrentThreadScheduler. This enables single-
        # threaded cancellation
        # https://social.msdn.microsoft.com/Forums/en-US/eb82f593-9684-4e27-
        # 97b9-8b8886da5c33/whats-the-rationale-behind-how-currentthreadsche
        # dulerschedulerequired-behaves?forum=rx
        if current_thread_scheduler.schedule_required():
            current_thread_scheduler.schedule(set_disposable)
        else:
            set_disposable()

        # Hide the identity of the auto detach observer
        return Disposable.create(auto_detach_observer.dispose)


def asyncgen_to_observable(asyncgen):
    def emit(observer):
        ensure_future(iterate_asyncgen(asyncgen, observer))
    return AsyncgenObservable(emit, asyncgen)


async def iterate_asyncgen(asyncgen, observer):
    try:
        async for item in asyncgen:
            observer.on_next(item)
        observer.on_completed()
    except Exception as e:
        observer.on_error(e)
