from graphql import Source, parse
from graphql.language import ast
from graphql.language.parser import Loc
from graphql.utils.ast_to_code import ast_to_code

from ...language.tests import fixtures
from ...utils.undefined import Undefined


def test_ast_to_code_using_kitchen_sink():
    doc = parse(fixtures.KITCHEN_SINK)
    code_ast = ast_to_code(doc)
    source = Source(fixtures.KITCHEN_SINK)

    def loc(start, end):
        return Loc(start, end, source)

    parsed_code_ast = eval(code_ast, {}, {"ast": ast, "loc": loc, "Undefined": Undefined})
    assert doc == parsed_code_ast
