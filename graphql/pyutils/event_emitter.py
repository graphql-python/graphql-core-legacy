from collections import defaultdict

from rx.core import AnonymousObservable


__all__ = ["EventEmitter", "EventEmitterAsyncIterator"]


class EventEmitter(object):
    """A very simple EventEmitter."""

    def __init__(self):
        self.listeners = defaultdict(list)

    def add_listener(self, event_name, listener):
        """Add a listener."""
        self.listeners[event_name].append(listener)
        return self

    def remove_listener(self, event_name, listener):
        """Removes a listener."""
        self.listeners[event_name].remove(listener)
        return self

    def emit(self, event_name, *args, **kwargs):
        """Emit an event."""
        listeners = list(self.listeners[event_name])
        if not listeners:
            return False
        for listener in listeners:
            result = listener(*args, **kwargs)
        return True

    def complete(self):
        return self.emit(EventEmitterObservable.COMPLETE)


class EventEmitterObservable(AnonymousObservable):
    """Create an Observable from an EventEmitter.

    Useful for mocking a PubSub system for tests.
    """

    COMPLETE = "__COMPLETE__"

    def __init__(self, event_emitter, event_name):
        def push_from_emitter(observer):
            event_emitter.add_listener(event_name, observer.on_next)
            event_emitter.add_listener(self.COMPLETE, self.dispose)

            def remove_observer_listener():
                event_emitter.remove_listener(event_name, observer.on_next)
                event_emitter.remove_listener(self.COMPLETE, self.dispose)
                observer.on_completed()

            self.remove_observer_listener = remove_observer_listener

        self.event_emitter = event_emitter
        self.event_name = event_name
        # self.event_emitter.add_listener(event_name, self.on_next)
        super(EventEmitterObservable, self).__init__(push_from_emitter)

    # def on_next(self, value):
    #     self.last = value

    def dispose(self):
        self.remove_observer_listener()
        # self.event_emitter.remove_listener(event_name, self.on_next)
        # super(EventEmitterObservable, self).dispose()
