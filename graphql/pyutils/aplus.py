from threading import Event, RLock


class CountdownLatch(object):

    def __init__(self, count):
        assert count >= 0

        self._lock = RLock()
        self._count = count

    def dec(self):
        with self._lock:
            assert self._count > 0

            self._count -= 1

            # Return inside lock to return the correct value,
            # otherwise an other thread could already have
            # decremented again.
            return self._count

    @property
    def count(self):
        return self._count


class Promise(object):
    """
    This is a class that attempts to comply with the
    Promises/A+ specification and test suite:
    http://promises-aplus.github.io/promises-spec/
    """

    # These are the potential states of a promise
    PENDING = -1
    REJECTED = 0
    FULFILLED = 1

    def __init__(self, fn=None):
        """
        Initialize the Promise into a pending state.
        """
        self._state = self.PENDING
        self._value = None
        self._reason = None
        self._cb_lock = RLock()
        self._callbacks = []
        self._errbacks = []
        self._event = Event()
        if fn:
            self.do_resolve(fn)

    def do_resolve(self, fn):
        self._done = False

        def resolve_fn(x):
            if self._done:
                return
            self._done = True
            self.fulfill(x)

        def reject_fn(x):
            if self._done:
                return
            self._done = True
            self.reject(x)
        try:
            fn(resolve_fn, reject_fn)
        except Exception as e:
            self.reject(e)

    @staticmethod
    def fulfilled(x):
        p = Promise()
        p.fulfill(x)
        return p

    @staticmethod
    def rejected(reason):
        p = Promise()
        p.reject(reason)
        return p

    def fulfill(self, x):
        """
        Fulfill the promise with a given value.
        """

        if self is x:
            raise TypeError("Cannot resolve promise with itself.")
        elif _isPromise(x):
            try:
                _promisify(x).done(self.fulfill, self.reject)
            except Exception as e:
                self.reject(e)
        else:
            self._fulfill(x)

    resolve = fulfilled

    def _fulfill(self, value):
        with self._cb_lock:
            if self._state != Promise.PENDING:
                return

            self._value = value
            self._state = self.FULFILLED

            callbacks = self._callbacks
            # We will never call these callbacks again, so allow
            # them to be garbage collected.  This is important since
            # they probably include closures which are binding variables
            # that might otherwise be garbage collected.
            #
            # Prevent future appending
            self._callbacks = None

            # Notify all waiting
            self._event.set()

        for callback in callbacks:
            try:
                callback(value)
            except Exception:
                # Ignore errors in callbacks
                pass

    def reject(self, reason):
        """
        Reject this promise for a given reason.
        """
        assert isinstance(reason, Exception)

        with self._cb_lock:
            if self._state != Promise.PENDING:
                return

            self._reason = reason
            self._state = self.REJECTED

            errbacks = self._errbacks
            # We will never call these errbacks again, so allow
            # them to be garbage collected.  This is important since
            # they probably include closures which are binding variables
            # that might otherwise be garbage collected.
            #
            # Prevent future appending
            self._errbacks = None

            # Notify all waiting
            self._event.set()

        for errback in errbacks:
            try:
                errback(reason)
            except Exception:
                # Ignore errors in errback
                pass

    @property
    def isPending(self):
        """Indicate whether the Promise is still pending. Could be wrong the moment the function returns."""
        return self._state == self.PENDING

    @property
    def isFulfilled(self):
        """Indicate whether the Promise has been fulfilled. Could be wrong the moment the function returns."""
        return self._state == self.FULFILLED

    @property
    def isRejected(self):
        """Indicate whether the Promise has been rejected. Could be wrong the moment the function returns."""
        return self._state == self.REJECTED

    @property
    def value(self):
        return self._value

    @property
    def reason(self):
        return self._reason

    def get(self, timeout=None):
        """Get the value of the promise, waiting if necessary."""
        self.wait(timeout)

        if self._state == self.PENDING:
            raise ValueError("Value not available, promise is still pending")
        elif self._state == self.FULFILLED:
            return self._value
        else:
            raise self._reason

    def wait(self, timeout=None):
        """
        An implementation of the wait method which doesn't involve
        polling but instead utilizes a "real" synchronization
        scheme.
        """
        self._event.wait(timeout)

    def addCallback(self, f):
        """
        Add a callback for when this promis is fulfilled.  Note that
        if you intend to use the value of the promise somehow in
        the callback, it is more convenient to use the 'then' method.
        """
        assert _isFunction(f)

        with self._cb_lock:
            if self._state == self.PENDING:
                self._callbacks.append(f)
                return

        # This is a correct performance optimization in case of concurrency.
        # State can never change once it is not PENDING anymore and is thus safe to read
        # without acquiring the lock.
        if self._state == self.FULFILLED:
            f(self._value)
        else:
            pass

    def addErrback(self, f):
        """
        Add a callback for when this promis is rejected.  Note that
        if you intend to use the rejection reason of the promise
        somehow in the callback, it is more convenient to use
        the 'then' method.
        """
        assert _isFunction(f)

        with self._cb_lock:
            if self._state == self.PENDING:
                self._errbacks.append(f)
                return

        # This is a correct performance optimization in case of concurrency.
        # State can never change once it is not PENDING anymore and is thus safe to read
        # without acquiring the lock.
        if self._state == self.REJECTED:
            f(self._reason)
        else:
            pass

    def catch(self, f):
        return self.then(None, f)

    def done(self, success=None, failure=None):
        """
        This method takes two optional arguments.  The first argument
        is used if the "self promise" is fulfilled and the other is
        used if the "self promise" is rejected. In contrast to then,
        the return value of these callback is ignored and nothing is
        returned.
        """
        with self._cb_lock:
            if success is not None:
                self.addCallback(success)
            if failure is not None:
                self.addErrback(failure)

    def done_all(self, *handlers):
        """
        :type handlers: list[(object) -> object] | list[((object) -> object, (object) -> object)]
        """
        if len(handlers) == 0:
            return
        elif len(handlers) == 1 and isinstance(handlers[0], list):
            handlers = handlers[0]

        for handler in handlers:
            if isinstance(handler, tuple):
                s, f = handler

                self.done(s, f)
            elif isinstance(handler, dict):
                s = handler.get('success')
                f = handler.get('failure')

                self.done(s, f)
            else:
                self.done(success=handler)

    def then(self, success=None, failure=None):
        """
        This method takes two optional arguments.  The first argument
        is used if the "self promise" is fulfilled and the other is
        used if the "self promise" is rejected.  In either case, this
        method returns another promise that effectively represents
        the result of either the first of the second argument (in the
        case that the "self promise" is fulfilled or rejected,
        respectively).
        Each argument can be either:
          * None - Meaning no action is taken
          * A function - which will be called with either the value
            of the "self promise" or the reason for rejection of
            the "self promise".  The function may return:
            * A value - which will be used to fulfill the promise
              returned by this method.
            * A promise - which, when fulfilled or rejected, will
              cascade its value or reason to the promise returned
              by this method.
          * A value - which will be assigned as either the value
            or the reason for the promise returned by this method
            when the "self promise" is either fulfilled or rejected,
            respectively.
        :type success: (object) -> object
        :type failure: (object) -> object
        :rtype : Promise
        """
        ret = Promise()

        def callAndFulfill(v):
            """
            A callback to be invoked if the "self promise"
            is fulfilled.
            """
            try:
                if _isFunction(success):
                    ret.fulfill(success(v))
                else:
                    ret.fulfill(v)
            except Exception as e:
                ret.reject(e)

        def callAndReject(r):
            """
            A callback to be invoked if the "self promise"
            is rejected.
            """
            try:
                if _isFunction(failure):
                    ret.fulfill(failure(r))
                else:
                    ret.reject(r)
            except Exception as e:
                ret.reject(e)

        self.done(callAndFulfill, callAndReject)

        return ret

    def then_all(self, *handlers):
        """
        Utility function which calls 'then' for each handler provided. Handler can either
        be a function in which case it is used as success handler, or a tuple containing
        the success and the failure handler, where each of them could be None.
        :type handlers: list[(object) -> object] | list[((object) -> object, (object) -> object)]
        :param handlers
        :rtype : list[Promise]
        """
        if len(handlers) == 0:
            return []
        elif len(handlers) == 1 and isinstance(handlers[0], list):
            handlers = handlers[0]

        promises = []

        for handler in handlers:
            if isinstance(handler, tuple):
                s, f = handler

                promises.append(self.then(s, f))
            elif isinstance(handler, dict):
                s = handler.get('success')
                f = handler.get('failure')

                promises.append(self.then(s, f))
            else:
                promises.append(self.then(success=handler))

        return promises

    @staticmethod
    def all(values_or_promises):
        return listPromise(values_or_promises)


def _isFunction(v):
    """
    A utility function to determine if the specified
    value is a function.
    """
    return v is not None and hasattr(v, "__call__")


def _isPromise(obj):
    """
    A utility function to determine if the specified
    object is a promise using "duck typing".
    """
    return isinstance(obj, Promise) or (
        hasattr(obj, "done") and _isFunction(getattr(obj, "done"))) or (
        hasattr(obj, "then") and _isFunction(getattr(obj, "then")))


is_thenable = _isPromise


def _promisify(obj):
    if isinstance(obj, Promise):
        return obj
    elif hasattr(obj, "done") and _isFunction(getattr(obj, "done")):
        p = Promise()
        obj.done(p.fulfill, p.reject)
        return p
    elif hasattr(obj, "then") and _isFunction(getattr(obj, "then")):
        p = Promise()
        obj.then(p.fulfill, p.reject)
        return p
    else:
        raise TypeError("Object is not a Promise like object.")

promisify = _promisify


def listPromise(values_or_promises):
    """
    A special function that takes a bunch of promises
    and turns them into a promise for a vector of values.
    In other words, this turns an list of promises for values
    into a promise for a list of values.
    """
    promises = list(filter(_isPromise, values_or_promises))
    if len(promises) == 0:
        # All the values or promises are resolved
        return Promise.fulfilled(values_or_promises)

    ret = Promise()
    counter = CountdownLatch(len(promises))

    def handleSuccess(_):
        if counter.dec() == 0:
            values = list(map(lambda p: p.value if p in promises else p, values_or_promises))
            ret.fulfill(values)

    for p in promises:
        _promisify(p).done(handleSuccess, ret.reject)

    return ret


def dictPromise(m):
    """
    A special function that takes a dictionary of promises
    and turns them into a promise for a dictionary of values.
    In other words, this turns an dictionary of promises for values
    into a promise for a dictionary of values.
    """
    if not m:
        return Promise.fulfilled({})

    keys, values = zip(*m.items())
    dict_type = type(m)

    def handleSuccess(resolved_values):
        return dict_type(zip(keys, resolved_values))

    return Promise.all(values).then(handleSuccess)


promise_for_dict = dictPromise


def _process(p, f):
    try:
        val = f()
        p.fulfill(val)
    except Exception as e:
        p.reject(e)
