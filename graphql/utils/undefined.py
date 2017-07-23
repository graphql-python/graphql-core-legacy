class _Undefined(object):
    def __bool__(self):
        return False

    __nonzero__ = __bool__

    def __repr__(self):
        return 'Undefined'


Undefined = _Undefined()
