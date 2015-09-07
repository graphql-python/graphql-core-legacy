from collections import namedtuple

__all__ = ['get_location', 'SourceLocation']

SourceLocation = namedtuple('SourceLocation', 'line column')


def get_location(source, position):
    lines = source.body[:position].splitlines()
    if lines:
        line = len(lines)
        column = len(lines[-1]) + 1
    else:
        line = 1
        column = 1
    return SourceLocation(line, column)
