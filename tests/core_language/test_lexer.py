from pytest import raises
from graphql.core.language.error import LanguageError
from graphql.core.language.source import Source
from graphql.core.language.lexer import Lexer, Token, TokenKind

def lex_one(s):
    return Lexer(Source(s)).next_token()


def test_skips_whitespace():
    assert lex_one("""

    foo


""") == Token(TokenKind.NAME, 6, 9, 'foo')

    assert lex_one("""
    #comment
    foo#comment
""") == Token(TokenKind.NAME, 18, 21, 'foo')

    assert lex_one(""",,,foo,,,""") == Token(TokenKind.NAME, 3, 6, 'foo')


def test_errors_respect_whitespace():
    with raises(LanguageError) as excinfo:
        lex_one("""

    ?


""")
    assert str(excinfo.value) == \
      'Syntax Error GraphQL (3:5) Unexpected character "?"\n' \
      '\n' \
      '2: \n' \
      '3:     ?\n' \
      '       ^\n' \
      '4: \n'

  
def test_lexes_strings():
    assert lex_one('"simple"') == Token(TokenKind.STRING, 0, 8, 'simple')
    assert lex_one('" white space "') == Token(TokenKind.STRING, 0, 15, ' white space ')
    assert lex_one('"quote \\""') == Token(TokenKind.STRING, 0, 10, 'quote "')
    assert lex_one('"escaped \\n\\r\\b\\t\\f"') == Token(TokenKind.STRING, 0, 20, 'escaped \n\r\b\t\f')
    assert lex_one('"slashes \\\\ \\/"') == Token( TokenKind.STRING, 0, 15, 'slashes \\ /')
    assert lex_one(u'"unicode \\u1234\\u5678\\u90AB\\uCDEF"') == Token(TokenKind.STRING, 0, 34, u'unicode \u1234\u5678\u90AB\uCDEF')


def test_lex_reports_useful_string_errors():
    with raises(LanguageError) as excinfo:
        lex_one('"no end quote')
    assert 'Syntax Error GraphQL (1:14) Unterminated string' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"multi\nline"')
    assert 'Syntax Error GraphQL (1:7) Unterminated string' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"multi\rline"')
    assert 'Syntax Error GraphQL (1:7) Unterminated string' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one(u'"multi\u2028line"')
    assert 'Syntax Error GraphQL (1:7) Unterminated string' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one(u'"multi\u2029line"')
    assert 'Syntax Error GraphQL (1:7) Unterminated string' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"bad \\z esc"')
    assert 'Syntax Error GraphQL (1:7) Bad character escape sequence' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"bad \\x esc"')
    assert 'Syntax Error GraphQL (1:7) Bad character escape sequence' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"bad \\u1 esc"')
    assert 'Syntax Error GraphQL (1:7) Bad character escape sequence' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"bad \\u0XX1 esc"')
    assert 'Syntax Error GraphQL (1:7) Bad character escape sequence' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"bad \\uXXXX esc"')
    assert 'Syntax Error GraphQL (1:7) Bad character escape sequence' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"bad \\uFXXX esc"')
    assert 'Syntax Error GraphQL (1:7) Bad character escape sequence' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('"bad \\uXXXF esc"')
    assert 'Syntax Error GraphQL (1:7) Bad character escape sequence' in str(excinfo.value)
  

def test_lexes_numbers():
    assert lex_one('4') == Token(TokenKind.INT, 0, 1, '4')
    assert lex_one('4.123') == Token(TokenKind.FLOAT, 0, 5, '4.123')
    assert lex_one('-4') == Token(TokenKind.INT, 0, 2, '-4')
    assert lex_one('9') == Token(TokenKind.INT, 0, 1, '9')
    assert lex_one('0') == Token(TokenKind.INT, 0, 1, '0')
    assert lex_one('00') == Token(TokenKind.INT, 0, 1, '0')
    assert lex_one('-4.123') == Token(TokenKind.FLOAT, 0, 6, '-4.123')
    assert lex_one('0.123') == Token(TokenKind.FLOAT, 0, 5, '0.123')
    assert lex_one('-1.123e4') == Token(TokenKind.FLOAT, 0, 8, '-1.123e4')
    assert lex_one('-1.123e-4') == Token(TokenKind.FLOAT, 0, 9, '-1.123e-4')
    assert lex_one('-1.123e4567') == Token(TokenKind.FLOAT, 0, 11, '-1.123e4567')
    

def test_lex_reports_useful_number_errors():
    with raises(LanguageError) as excinfo:
        lex_one('+1')
    assert 'Syntax Error GraphQL (1:1) Unexpected character "+"' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('1.')
    assert 'Syntax Error GraphQL (1:3) Invalid number' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('1.A')
    assert 'Syntax Error GraphQL (1:3) Invalid number' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('-A')
    assert 'Syntax Error GraphQL (1:2) Invalid number' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('1.0e+4')
    assert 'Syntax Error GraphQL (1:5) Invalid number' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('1.0e')
    assert 'Syntax Error GraphQL (1:5) Invalid number' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('1.0eA')
    assert 'Syntax Error GraphQL (1:5) Invalid number' in str(excinfo.value)

  
def test_lexes_punctuation():
    assert lex_one('!') == Token(TokenKind.BANG, 0, 1)
    assert lex_one('$') == Token(TokenKind.DOLLAR, 0, 1)
    assert lex_one('(') == Token(TokenKind.PAREN_L, 0, 1)
    assert lex_one(')') == Token(TokenKind.PAREN_R, 0, 1)
    assert lex_one('...') == Token(TokenKind.SPREAD, 0, 3)
    assert lex_one(':') == Token(TokenKind.COLON, 0, 1)
    assert lex_one('=') == Token(TokenKind.EQUALS, 0, 1)
    assert lex_one('@') == Token(TokenKind.AT, 0, 1)
    assert lex_one('[') == Token(TokenKind.BRACKET_L, 0, 1)
    assert lex_one(']') == Token(TokenKind.BRACKET_R, 0, 1)
    assert lex_one('{') == Token(TokenKind.BRACE_L, 0, 1)
    assert lex_one('|') == Token(TokenKind.PIPE, 0, 1)
    assert lex_one('}') == Token(TokenKind.BRACE_R, 0, 1)
    

def test_lex_reports_useful_unknown_character_error():
    with raises(LanguageError) as excinfo:
        lex_one('..')
    assert 'Syntax Error GraphQL (1:1) Unexpected character "."' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one('?')
    assert 'Syntax Error GraphQL (1:1) Unexpected character "?"' in str(excinfo.value)

    with raises(LanguageError) as excinfo:
        lex_one(u'\u203B')
    assert r'Syntax Error GraphQL (1:1) Unexpected character "\u203b"' in excinfo.value.message
