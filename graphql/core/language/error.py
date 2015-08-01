from ..error import Error
from .location import get_location

__all__ = ['LanguageError']


class LanguageError(Error):
    def __init__(self, source, position, description):
        self.source = source
        self.position = position
        self.description = description

    def __str__(self):
        # FIXME
        return unicode(self).encode(errors='replace')

    def __unicode__(self):
        location = get_location(self.source, self.position)
        return u'Syntax Error {} ({}:{}) {}\n\n{}'.format(
            self.source.name,
            location.line,
            location.column,
            self.description,
            highlight_source_at_location(self.source, location),
        )


def highlight_source_at_location(source, location):
    line = location.line
    lines = source.body.splitlines()
    pad_len = len(str(line + 1))
    result = u''
    format = (u'{:>' + str(pad_len) + '}: {}\n').format
    if line >= 2:
        result += format(line - 1, lines[line - 2])
    result += format(line, lines[line - 1])
    result += ' ' * (1 + pad_len + location.column) + '^\n'
    if line < len(lines):
        result += format(line + 1, lines[line])
    return result
