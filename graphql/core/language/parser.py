from .source import Source
from .error import LanguageError
from .lexer import Lexer, TokenKind, get_token_kind_desc, get_token_desc
from . import ast

__all__ = ['parse']


def parse(source, **kwargs):
    """Given a GraphQL source, parses it into a Document."""
    options = {'no_location': False, 'no_source': False}
    options.update(kwargs)
    source_obj = source
    if isinstance(source, basestring):
        source_obj = Source(source)
    parser = Parser(source_obj, options)
    return parse_document(parser)


class Parser(object):
    def __init__(self, source, options):
        self.lexer = Lexer(source)
        self.source = source
        self.options = options
        self.prev_end = 0
        self.token = self.lexer.next_token()


def loc(parser, start):
    """Returns a location object, used to identify the place in
    the source that created a given parsed object."""
    if parser.options['no_location']:
        return None
    if parser.options['no_source']:
        return {
            'start': start,
            'end': parser.prev_end
        }
    return {
        'start': start,
        'end': parser.prev_end,
        'source': parser.source
    }


def advance(parser):
    """Moves the internal parser object to the next lexed token."""
    prev_end = parser.token.end
    parser.prev_end = prev_end
    parser.token = parser.lexer.next_token(prev_end)


def peek(parser, kind):
    """Determines if the next token is of a given kind"""
    return parser.token.kind == kind


def skip(parser, kind):
    """If the next token is of the given kind, return true after advancing
    the parser. Otherwise, do not change the parser state
    and return False."""
    match = parser.token.kind == kind
    if match:
        advance(parser)
    return match


def expect(parser, kind):
    """If the next token is of the given kind, return that token after
    advancing the parser. Otherwise, do not change the parser state and
    return False."""
    token = parser.token
    if token.kind == kind:
        advance(parser)
        return token
    raise LanguageError(
        parser.source,
        token.start,
        'Expected {}, found {}'.format(
            get_token_kind_desc(kind),
            get_token_desc(token)
        )
    )


def expect_keyword(parser, value):
    """If the next token is a keyword with the given value, return that
    token after advancing the parser. Otherwise, do not change the parser
    state and return False."""
    token = parser.token
    if token.kind == TokenKind.NAME and token.value == value:
        advance(parser)
        return token
    raise LanguageError(
        parser.source,
        token.start,
        'Expected "{}", found {}'.format(value, get_token_desc(token))
    )


def unexpected(parser, at_token=None):
    """Helper function for creating an error when an unexpected lexed token
    is encountered."""
    token = at_token or parser.token
    return LanguageError(
        parser.source,
        token.start,
        'Unexpected {}'.format(get_token_desc(token))
    )


def any(parser, open_kind, parse_fn, close_kind):
    """Returns a possibly empty list of parse nodes, determined by
    the parse_fn. This list begins with a lex token of openKind
    and ends with a lex token of closeKind. Advances the parser
    to the next lex token after the closing token."""
    expect(parser, open_kind)
    nodes = []
    while not skip(parser, close_kind):
        nodes.append(parse_fn(parser))
    return nodes


def many(parser, open_kind, parse_fn, close_kind):
    """Returns a non-empty list of parse nodes, determined by
    the parse_fn. This list begins with a lex token of openKind
    and ends with a lex token of closeKind. Advances the parser
    to the next lex token after the closing token."""
    expect(parser, open_kind)
    nodes = [parse_fn(parser)]
    while not skip(parser, close_kind):
        nodes.append(parse_fn(parser))
    return nodes


def parse_name(parser):
    """Converts a name lex token into a name parse node."""
    token = expect(parser, TokenKind.NAME)
    return ast.Name(
        value=token.value,
        loc=loc(parser, token.start)
    )


# Implements the parsing rules in the Document section.

def parse_document(parser):
    start = parser.token.start
    definitions = []
    while True:
        if peek(parser, TokenKind.BRACE_L):
            definitions.append(parse_operation_definition(parser))
        elif peek(parser, TokenKind.NAME):
            if parser.token.value in ('query', 'mutation'):
                definitions.append(parse_operation_definition(parser))
            elif parser.token.value == 'fragment':
                definitions.append(parse_fragment_definition(parser))
            else:
                raise unexpected(parser)
        else:
            raise unexpected(parser)
        if skip(parser, TokenKind.EOF):
            break
    return ast.Document(
        definitions=definitions,
        loc=loc(parser, start)
    )


# Implements the parsing rules in the Operations section.

def parse_operation_definition(parser):
    start = parser.token.start
    if peek(parser, TokenKind.BRACE_L):
        return ast.OperationDefinition(
            operation='query',
            name=None,
            variable_definitions=None,
            directives=[],
            selection_set=parse_selection_set(parser),
            loc=loc(parser, start)
        )
    operation_token = expect(parser, TokenKind.NAME)
    operation = operation_token.value
    return ast.OperationDefinition(
        operation=operation,
        name=parse_name(parser),
        variable_definitions=parse_variable_definitions(parser),
        directives=parse_directives(parser),
        selection_set=parse_selection_set(parser),
        loc=loc(parser, start)
    )


def parse_variable_definitions(parser):
    if peek(parser, TokenKind.PAREN_L):
        return many(
            parser,
            TokenKind.PAREN_L,
            parse_variable_definition,
            TokenKind.PAREN_R
        )
    return []


def parse_variable_definition(parser):
    start = parser.token.start
    variable = parse_variable(parser)
    type = (expect(parser, TokenKind.COLON), parse_type(parser))[1]
    if skip(parser, TokenKind.EQUALS):
        default_value = parse_value(parser, True)
    else:
        default_value = None
    return ast.VariableDefinition(
        variable=variable,
        type=type,
        default_value=default_value,
        loc=loc(parser, start)
    )


def parse_variable(parser):
    start = parser.token.start
    expect(parser, TokenKind.DOLLAR)
    return ast.Variable(
        name=parse_name(parser),
        loc=loc(parser, start)
    )


def parse_selection_set(parser):
    start = parser.token.start
    return ast.SelectionSet(
        selections=many(parser, TokenKind.BRACE_L, parse_selection, TokenKind.BRACE_R),
        loc=loc(parser, start)
    )


def parse_selection(parser):
    if peek(parser, TokenKind.SPREAD):
        return parse_fragment(parser)
    else:
        return parse_field(parser)


def parse_field(parser):
    # Corresponds to both Field and Alias in the spec
    start = parser.token.start

    name_or_alias = parse_name(parser)
    if skip(parser, TokenKind.COLON):
        alias = name_or_alias
        name = parse_name(parser)
    else:
        alias = None
        name = name_or_alias

    arguments = parse_arguments(parser)
    directives = parse_directives(parser)
    if peek(parser, TokenKind.BRACE_L):
        selection_set = parse_selection_set(parser)
    else:
        selection_set = None
    return ast.Field(
        alias=alias,
        name=name,
        arguments=arguments,
        directives=directives,
        selection_set=selection_set,
        loc=loc(parser, start)
    )


def parse_arguments(parser):
    if peek(parser, TokenKind.PAREN_L):
        return many(
            parser, TokenKind.PAREN_L,
            parse_argument, TokenKind.PAREN_R)
    return []


def parse_argument(parser):
    start = parser.token.start
    return ast.Argument(
        name=parse_name(parser),
        value=(
            expect(parser, TokenKind.COLON),
            parse_value(parser, False))[1],
        loc=loc(parser, start)
    )


# Implements the parsing rules in the Fragments section.

def parse_fragment(parser):
    # Corresponds to both FragmentSpread and InlineFragment in the spec
    start = parser.token.start
    expect(parser, TokenKind.SPREAD)
    if parser.token.value == 'on':
        advance(parser)
        return ast.InlineFragment(
            type_condition=parse_named_type(parser),
            directives=parse_directives(parser),
            selection_set=parse_selection_set(parser),
            loc=loc(parser, start)
        )
    return ast.FragmentSpread(
        name=parse_name(parser),
        directives=parse_directives(parser),
        loc=loc(parser, start)
    )


def parse_fragment_definition(parser):
    start = parser.token.start
    expect_keyword(parser, 'fragment')
    return ast.FragmentDefinition(
        name=parse_name(parser),
        type_condition=(
            expect_keyword(parser, 'on'),
            parse_named_type(parser))[1],
        directives=parse_directives(parser),
        selection_set=parse_selection_set(parser),
        loc=loc(parser, start)
    )


# Implements the parsing rules in the Values section.

def parse_variable_value(parser):
    return parse_value(parser, False)


def parse_const_value(parser):
    return parse_value(parser, True)


def parse_value(parser, is_const):
    token = parser.token
    if token.kind == TokenKind.BRACKET_L:
        return parse_array(parser, is_const)
    elif token.kind == TokenKind.BRACE_L:
        return parse_object(parser, is_const)
    elif token.kind == TokenKind.INT:
        advance(parser)
        return ast.IntValue(value=token.value, loc=loc(parser, token.start))
    elif token.kind == TokenKind.FLOAT:
        advance(parser)
        return ast.FloatValue(value=token.value, loc=loc(parser, token.start))
    elif token.kind == TokenKind.STRING:
        advance(parser)
        return ast.StringValue(value=token.value, loc=loc(parser, token.start))
    elif token.kind == TokenKind.NAME:
        advance(parser)
        if token.value in ('true', 'false'):
            return ast.BooleanValue(value=token.value == 'true', loc=loc(parser, token.start))
        return ast.EnumValue(value=token.value, loc=loc(parser, token.start))
    elif token.kind == TokenKind.DOLLAR:
        if not is_const:
            return parse_variable(parser)
    raise unexpected(parser)


def parse_array(parser, is_const):
    start = parser.token.start
    if is_const:
        item = parse_const_value
    else:
        item = parse_variable_value
    return ast.ListValue(
        values=any(
            parser, TokenKind.BRACKET_L,
            item, TokenKind.BRACKET_R),
        loc=loc(parser, start)
    )


def parse_object(parser, is_const):
    start = parser.token.start
    expect(parser, TokenKind.BRACE_L)
    field_names = set()
    fields = []
    while not skip(parser, TokenKind.BRACE_R):
        fields.append(parse_object_field(parser, is_const, field_names))
    return ast.ObjectValue(fields=fields, loc=loc(parser, start))


def parse_object_field(parser, is_const, field_names):
    start = parser.token.start
    name = parse_name(parser)
    if name.value in field_names:
        raise LanguageError(
            parser.source,
            start,
            "Duplicate input object field {}.".format(name.value)
        )
    field_names.add(name.value)
    return ast.ObjectField(
        name=name,
        value=(
            expect(parser, TokenKind.COLON),
            parse_value(parser, is_const))[1],
        loc=loc(parser, start)
    )


# Implements the parsing rules in the Directives section.

def parse_directives(parser):
    directives = []
    while peek(parser, TokenKind.AT):
        directives.append(parse_directive(parser))
    return directives


def parse_directive(parser):
    start = parser.token.start
    expect(parser, TokenKind.AT)
    node = ast.Directive(
        name=parse_name(parser),
        arguments=parse_arguments(parser),
        loc=loc(parser, start),
    )
    return node


# Implements the parsing rules in the Types section.

def parse_type(parser):
    """Handles the 'Type': TypeName, ListType, and NonNullType
    parsing rules."""
    start = parser.token.start
    type = None
    if skip(parser, TokenKind.BRACKET_L):
        type = parse_type(parser)
        expect(parser, TokenKind.BRACKET_R)
        type = ast.ListType(type=type, loc=loc(parser, start))
    else:
        type = parse_named_type(parser)
    if skip(parser, TokenKind.BANG):
        return ast.NonNullType(type=type, loc=loc(parser, start))
    return type


def parse_named_type(parser):
    start = parser.token.start
    return ast.NamedType(
        name=parse_name(parser),
        loc=loc(parser, start),
    )
