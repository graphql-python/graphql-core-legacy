from .graphql_error import GraphQLError

__all__ = ["GraphQLSyntaxError"]


class GraphQLSyntaxError(GraphQLError):
    """A GraphQLError representing a syntax error."""

    def __init__(self, source, position, description):
        super(GraphQLSyntaxError, self).__init__(
            "Syntax Error: {}".format(description), source=source, positions=[position]
        )
        self.description = description
