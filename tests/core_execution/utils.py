from graphql.core.pyutils.defer import Deferred, DeferredException


class RaisingDeferred(Deferred):
    def _next(self):
        """Process the next callback."""
        if self._running or self.paused:
            return
        while self.callbacks:
            # Get the next callback pair
            next_pair = self.callbacks.pop(0)
            # Continue with the errback if the last result was an exception
            callback, args, kwargs = next_pair[isinstance(self.result,
                                                          DeferredException)]
            try:
                self.result = callback(self.result, *args, **kwargs)
            except:
                self.result = DeferredException()
            finally:
                self._running = False

            if isinstance(self.result, Deferred):
                # If a Deferred was returned add this deferred as callbacks to
                # the returned one. As a result the processing of this Deferred
                # will be paused until all callbacks of the returned Deferred
                # have been performed
                self.result.add_callbacks(self._continue, self._continue)
                self.paused == True
                break

        if isinstance(self.result, DeferredException):
            # Print the exception to stderr and stop if there aren't any
            # further errbacks to process
            self.result.raise_exception()


def raise_callback_results(deferred, callback):
    d = RaisingDeferred()
    d.add_callback(lambda r: r)
    d.callback(deferred)
    d.add_callback(callback)


