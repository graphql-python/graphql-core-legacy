from six import text_type

from .base import GraphQLError


def format_error(error):
    formatted_error = {
        'message': text_type(error),
    }
    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error['locations'] = [
                {'line': loc.line, 'column': loc.column}
                for loc in error.locations
            ]
        if error.path is not None:
            formatted_error['path'] = error.path

    return formatted_error
