from __future__ import absolute_import

from gevent import get_hub, spawn
from gevent.event import AsyncResult
from graphql.core.defer import Deferred, DeferredException


def _run_resolver_in_greenlet(d, resolver):
    try:
        result = resolver()
        get_hub().loop.run_callback(d.callback, result)
    except:
        e = DeferredException()
        get_hub().loop.run_callback(d.errback, e)


def run_in_greenlet(f):
    """
        Marks a resolver to run inside a greenlet.

        @run_in_greenlet
        def resolve_something(context, _*):
            gevent.sleep(1)
            return 5

    """
    f._run_in_greenlet = True
    return f


class GeventExecutionMiddleware(object):
    def run_resolve_fn(self, resolver, original_resolver):
        if hasattr(original_resolver, '_run_in_greenlet'):
            d = Deferred()
            spawn(_run_resolver_in_greenlet, d, resolver)
            return d

        return resolver()

    def execution_result(self, executor):
        result = AsyncResult()
        deferred = executor()
        assert isinstance(deferred, Deferred), 'Another middleware has converted the execution result ' \
                                               'away from a Deferred.'

        deferred.add_callbacks(result.set, lambda e: result.set_exception(e.value, (e.type, e.value, e.traceback)))
        return result.get()
