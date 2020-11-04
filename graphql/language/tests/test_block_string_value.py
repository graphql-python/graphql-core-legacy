from graphql.language.lexer import block_string_value


def test_uniform_indentation():
    _input = [
        '',
        '    Hello,',
        '      World!',
        '',
        '    Yours,',
        '      GraphQL.',
    ]
    expectation = [
        'Hello,',
        '  World!',
        '',
        'Yours,',
        '  GraphQL.',
    ]
    _test_harness(_input, expectation)


def test_empty_leading_and_trailing_lines():
    _input = [
        '',
        '',
        '    Hello,',
        '      World!',
        '',
        '    Yours,',
        '      GraphQL.',
        '',
        '',
    ]
    expectation = [
        'Hello,',
        '  World!',
        '',
        'Yours,',
        '  GraphQL.',
    ]
    _test_harness(_input, expectation)


def remove_blank_and_leading_lines():
    _input = [
        '  ',
        '        ',
        '    Hello,',
        '      World!',
        '',
        '    Yours,',
        '      GraphQL.',
        '        ',
        '  ',
    ]
    expectation = [
        'Hello,',
        '  World!',
        '',
        'Yours,',
        '  GraphQL.',
    ]
    _test_harness(_input, expectation)


def test_retain_indentation_from_first_line():
    _input = [
        '    Hello,',
        '      World!',
        '',
        '    Yours,',
        '      GraphQL.',
    ]
    expectation = [
        '    Hello,',
        '  World!',
        '',
        'Yours,',
        '  GraphQL.',
    ]
    _test_harness(_input, expectation)


def test_does_not_alter_trailing_spaces():
    _input = [
        '               ',
        '    Hello,     ',
        '      World!   ',
        '               ',
        '    Yours,     ',
        '      GraphQL. ',
        '               ',
    ]
    expectation = [
        'Hello,     ',
        '  World!   ',
        '           ',
        'Yours,     ',
        '  GraphQL. ',
    ]
    _test_harness(_input, expectation)


def _test_harness(_input, expectation):
    _input = "\n".join(_input)
    expectation = "\n".join(expectation)
    assert block_string_value(_input) == expectation
