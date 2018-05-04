class _Undefined(object):
    """A representation of an Undefined value distinct from a None value"""

    def __eq__(self, other):
        return isinstance(other, _Undefined)

    def __bool__(self):
        # type: () -> bool
        return False

    __nonzero__ = __bool__

    def __repr__(self):
        # type: () -> str
        return "Undefined"


Undefined = _Undefined()
