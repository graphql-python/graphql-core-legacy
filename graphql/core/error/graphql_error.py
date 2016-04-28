from ..language.location import get_location


class GraphQLError(Exception):
    __slots__ = 'message', 'nodes', '_source', '_positions', 'original_error'

    def __init__(self, message, nodes=None, source=None, positions=None, original_error=None):
        super(GraphQLError, self).__init__(message)
        self.message = message or 'An unknown error occurred.'
        self.nodes = nodes
        self._source = source
        self._positions = positions
        self.original_error = original_error

    @property
    def source(self):
        if self._source:
            return self._source
        if self.nodes:
            node = self.nodes[0]
            return node and node.loc and node.loc.source

    @property
    def positions(self):
        if self._positions:
            return self._positions
        if self.nodes is not None:
            node_positions = [node.loc and node.loc.start for node in self.nodes]
            if any(node_positions):
                return node_positions

    @property
    def locations(self):
        if self.positions and self.source:
            return [get_location(self.source, pos) for pos in self.positions]


def format_error(error):
    formatted_error = {
        'message': error.message,
    }
    if error.locations is not None:
        formatted_error['locations'] = [
            {'line': loc.line, 'column': loc.column}
            for loc in error.locations
        ]

    return formatted_error
