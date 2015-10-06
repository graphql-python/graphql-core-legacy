from .language.location import get_location


class Error(Exception):
    pass


class GraphQLError(Error):
    def __init__(self, message, nodes=None, stack=None, source=None, positions=None):
        super(GraphQLError, self).__init__(message)
        self.message = message
        self.nodes = nodes
        self.stack = stack or message
        self._source = source
        self._positions = positions

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
    return {
        'message': error.message,
        'locations': [
            {'line': loc.line, 'column': loc.column}
            for loc in error.locations
        ],
    }
