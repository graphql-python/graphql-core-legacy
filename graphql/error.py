__all__ = ['Error']

class Error(Exception):
    pass


class GraphQLError(Error):
    pass


def format_error(error):
    return error
