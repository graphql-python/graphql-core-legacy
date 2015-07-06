__all__ = ['Error']

class Error(Exception):
    pass


class GraphQLError(Error):
    def __init__(self, message, nodes=None, cause=None):
        super(GraphQLError, self).__init__(message)


def format_error(error):
    return error
