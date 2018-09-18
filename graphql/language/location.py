from collections import namedtuple

if False:  # pragma: no cover
    from .source import Source  # noqa: F401

__all__ = ["get_location", "SourceLocation"]

SourceLocation = namedtuple("SourceLocation", "line,column")

# class SourceLocation(namedtuple("SourceLocation", "line,column")):
#     """Represents a location in a Source."""

#     def __init__(self, line, column):
#         # type: (int, int) -> None
#         self.line = line
#         self.column = column


def get_location(source, position):
    # type: (Source, int) -> SourceLocation
    """Get the line and column for a character position in the source.

    Takes a Source and a UTF-8 character offset, and returns the corresponding
    line and column as a SourceLocation.
    """
    return source.get_location(position)
