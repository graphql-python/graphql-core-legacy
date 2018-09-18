if False:  # pragma: no cover
    from typing import Any, Dict, TYPE_CHECKING
    from .graphql_error import GraphQLError  # noqa: F401


__all__ = ['format_error']


def format_error(error):
    # type: (GraphQLError) -> Dict
    """Format a GraphQL error

    Given a GraphQLError, format it according to the rules described by the
    Response Format, Errors section of the GraphQL Specification.
    """
    if not error:
        raise ValueError('Received null or undefined error.')
    formatted = dict(  # noqa: E701 (pycqa/flake8#394)
        message=error.message or 'An unknown error occurred.',
        locations=error.locations, path=error.path) # type: Dict[str, Any]
    if error.extensions:
        formatted.update(extensions=error.extensions)
    return formatted
