from six import text_type

from .base import GraphQLError

if False:  # flake8: noqa
    from .base import GraphQLError
    from .located_error import GraphQLLocatedError
    from typing import Any, Dict, Union


def format_error(error):
    # type: (Union[GraphQLError, GraphQLLocatedError]) -> Dict[str, Any]
    formatted_error = {"message": text_type(error)}
    if isinstance(error, GraphQLError):
        if error.locations is not None:
            formatted_error["locations"] = [
                {"line": loc.line, "column": loc.column} for loc in error.locations
            ]
        if error.path is not None:
            formatted_error["path"] = error.path

    return formatted_error
