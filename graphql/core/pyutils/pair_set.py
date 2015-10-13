class PairSet(object):
    __slots__ = '_data',

    def __init__(self):
        self._data = set()

    def __contains__(self, item):
        return item in self._data

    def has(self, a, b):
        return (a, b) in self._data

    def add(self, a, b):
        self._data.add((a, b))
        self._data.add((b, a))
        return self

    def remove(self, a, b):
        self._data.discard((a, b))
        self._data.discard((b, a))
