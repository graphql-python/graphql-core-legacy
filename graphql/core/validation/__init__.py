from ..language.visitor import visit
from ..type import GraphQLSchema
from ..utils.type_info import TypeInfo
from .context import ValidationContext
from .rules import specified_rules
from .visitor import ValidationVisitor


def validate(schema, ast, rules=specified_rules):
    assert schema, 'Must provide schema'
    assert ast, 'Must provide document'
    assert isinstance(schema, GraphQLSchema)
    type_info = TypeInfo(schema)
    return visit_using_rules(schema, type_info, ast, rules)


def visit_using_rules(schema, type_info, ast, rules):
    context = ValidationContext(schema, ast, type_info)
    errors = []
    rules = [rule(context) for rule in rules]
    visit(ast, ValidationVisitor(rules, context, type_info, errors))
    return errors
