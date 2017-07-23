from sys import exc_info


def process(p, f, args, kwargs):
    try:
        val = f(*args, **kwargs)
        p.do_resolve(val)
    except Exception as e:
        traceback = exc_info()[2]
        e.stack = traceback
        p.do_reject(e, traceback=traceback)
