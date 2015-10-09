from graphql.core.pyutils.defer import Deferred, DeferredException, _passthrough


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

            if callback is not _passthrough:
                self._running = True
                try:
                    self.result = callback(self.result, *args, **kwargs)

                except:
                    self.result = DeferredException()

                finally:
                    self._running = False

                if isinstance(self.result, Exception):
                    self.result = DeferredException(self.result)

        if isinstance(self.result, DeferredException):
            # Print the exception to stderr and stop if there aren't any
            # further errbacks to process
            self.result.raise_exception()


def raise_callback_results(deferred, callback):
    d = RaisingDeferred()
    d.add_callback(lambda r: r)
    d.callback(deferred)
    d.add_callback(callback)
