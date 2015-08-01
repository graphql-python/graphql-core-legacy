__all__ = ['Source']


class Source(object):
    def __init__(self, body, name='GraphQL'):
        self.body = body
        self.name = name
