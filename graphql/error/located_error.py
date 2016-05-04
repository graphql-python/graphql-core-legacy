import sys

from .base import GraphQLError

__all__ = ['GraphQLLocatedError']


class GraphQLLocatedError(GraphQLError):

    def __init__(self, nodes, original_error=None):
        if original_error:
            message = str(original_error)
        else:
            message = 'An unknown error occurred.'

        if isinstance(original_error, GraphQLError):
            stack = original_error.stack
        else:
            stack = sys.exc_info()[2]

        super(GraphQLLocatedError, self).__init__(
            message=message,
            nodes=nodes,
            stack=stack
        )
        self.original_error = original_error
