from .base import GraphQLError


def format_error(error):
    formatted_error = {
        'message': str(error),
    }
    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error['locations'] = [
                {'line': loc.line, 'column': loc.column}
                for loc in error.locations
            ]

    return formatted_error
