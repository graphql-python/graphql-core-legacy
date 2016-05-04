def process(p, f, args, kwargs):
    try:
        val = f(*args, **kwargs)
        p.fulfill(val)
    except Exception as e:
        p.reject(e)
