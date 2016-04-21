from ..language.visitor import ParallelVisitor, TypeInfoVisitor, visit
from ..type import GraphQLSchema
from ..utils.type_info import TypeInfo
from .context import ValidationContext
from .rules import specified_rules


def validate(schema, ast, rules=specified_rules):
    assert schema, 'Must provide schema'
    assert ast, 'Must provide document'
    assert isinstance(schema, GraphQLSchema)
    type_info = TypeInfo(schema)
    return visit_using_rules(schema, type_info, ast, rules)


def visit_using_rules(schema, type_info, ast, rules):
    context = ValidationContext(schema, ast, type_info)
    visitors = [rule(context) for rule in rules]
    visit(ast, TypeInfoVisitor(type_info, ParallelVisitor(visitors)))
    return context.get_errors()
