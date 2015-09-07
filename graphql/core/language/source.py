__all__ = ['Source']


class Source(object):
    def __init__(self, body, name='GraphQL'):
        self.body = body
        self.name = name

    def __eq__(self, other):
        if isinstance(other, Source):
            return self.body == other.body and self.name == other.name
        return False
