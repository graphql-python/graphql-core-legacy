from inspect import isasyncgen
from asyncio import ensure_future
from rx import Observable


def asyncgen_to_observable(asyncgen):
    def emit(observer):
        ensure_future(iterate_asyncgen(asyncgen, observer))
    return Observable.create(emit)


async def iterate_asyncgen(asyncgen, observer):
    try:
        async for item in asyncgen:
            observer.on_next(item)
        observer.on_completed()
    except Exception as e:
        observer.on_error(e)
