from graphql.core import Source, parse
from graphql.core.language import ast
from graphql.core.language.parser import Loc
from graphql.core.utils.ast_to_code import ast_to_code
from tests.core_language import fixtures


def test_ast_to_code_using_kitchen_sink():
    doc = parse(fixtures.KITCHEN_SINK)
    code_ast = ast_to_code(doc)
    source = Source(fixtures.KITCHEN_SINK)
    loc = lambda start, end: Loc(start, end, source)

    parsed_code_ast = eval(code_ast, {}, {'ast': ast, 'loc': loc})
    assert doc == parsed_code_ast
