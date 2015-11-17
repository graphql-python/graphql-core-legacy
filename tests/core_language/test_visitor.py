from graphql.core.language.ast import Field, Name, SelectionSet
from graphql.core.language.parser import parse
from graphql.core.language.visitor import visit, Visitor, REMOVE, BREAK
from .fixtures import KITCHEN_SINK


def test_allows_for_editing_on_enter():
    ast = parse('{ a, b, c { a, b, c } }', no_location=True)

    class TestVisitor(Visitor):
        def enter(self, node, *args):
            if isinstance(node, Field) and node.name.value == 'b':
                return REMOVE

    edited_ast = visit(ast, TestVisitor())

    assert ast == parse('{ a, b, c { a, b, c } }', no_location=True)
    assert edited_ast == parse('{ a,   c { a,   c } }', no_location=True)


def test_allows_for_editing_on_leave():
    ast = parse('{ a, b, c { a, b, c } }', no_location=True)

    class TestVisitor(Visitor):
        def leave(self, node, *args):
            if isinstance(node, Field) and node.name.value == 'b':
                return REMOVE

    edited_ast = visit(ast, TestVisitor())

    assert ast == parse('{ a, b, c { a, b, c } }', no_location=True)
    assert edited_ast == parse('{ a,   c { a,   c } }', no_location=True)


def test_visits_edited_node():
    added_field = Field(name=Name(value='__typename'))
    ast = parse('{ a { x } }')

    class TestVisitor(Visitor):
        def __init__(self):
            self.did_visit_added_field = False

        def enter(self, node, *args):
            if isinstance(node, Field) and node.name.value == 'a':
                selection_set = node.selection_set
                selections = []
                if selection_set:
                    selections = selection_set.selections
                new_selection_set = SelectionSet(selections=[added_field] + selections)
                return Field(name=None, selection_set=new_selection_set)
            if node is added_field:
                self.did_visit_added_field = True

    visitor = TestVisitor()
    visit(ast, visitor)
    assert visitor.did_visit_added_field


def test_allows_skipping_a_subtree():
    visited = []
    ast = parse('{ a, b { x }, c }')

    class TestVisitor(Visitor):
        def enter(self, node, *args):
            visited.append(['enter', type(node).__name__, getattr(node, 'value', None)])
            if isinstance(node, Field) and node.name.value == 'b':
                return False

        def leave(self, node, *args):
            visited.append(['leave', type(node).__name__, getattr(node, 'value', None)])

    visit(ast, TestVisitor())

    assert visited == [
        ['enter', 'Document', None],
        ['enter', 'OperationDefinition', None],
        ['enter', 'SelectionSet', None],
        ['enter', 'Field', None],
        ['enter', 'Name', 'a'],
        ['leave', 'Name', 'a'],
        ['leave', 'Field', None],
        ['enter', 'Field', None],
        ['enter', 'Field', None],
        ['enter', 'Name', 'c'],
        ['leave', 'Name', 'c'],
        ['leave', 'Field', None],
        ['leave', 'SelectionSet', None],
        ['leave', 'OperationDefinition', None],
        ['leave', 'Document', None],
    ]


def test_allows_early_exit_while_visiting():
    visited = []
    ast = parse('{ a, b { x }, c }')

    class TestVisitor(Visitor):
        def enter(self, node, *args):
            visited.append(['enter', type(node).__name__, getattr(node, 'value', None)])
            if isinstance(node, Name) and node.value == 'x':
                return BREAK

        def leave(self, node, *args):
            visited.append(['leave', type(node).__name__, getattr(node, 'value', None)])

    visit(ast, TestVisitor())

    assert visited == [
        ['enter', 'Document', None],
        ['enter', 'OperationDefinition', None],
        ['enter', 'SelectionSet', None],
        ['enter', 'Field', None],
        ['enter', 'Name', 'a'],
        ['leave', 'Name', 'a'],
        ['leave', 'Field', None],
        ['enter', 'Field', None],
        ['enter', 'Name', 'b'],
        ['leave', 'Name', 'b'],
        ['enter', 'SelectionSet', None],
        ['enter', 'Field', None],
        ['enter', 'Name', 'x'],
    ]


def test_allows_a_named_functions_visitor_api():
    visited = []
    ast = parse('{ a, b { x }, c }')

    class TestVisitor(Visitor):
        def enter_Name(self, node, *args):
            visited.append(['enter', type(node).__name__, getattr(node, 'value', None)])

        def enter_SelectionSet(self, node, *args):
            visited.append(['enter', type(node).__name__, getattr(node, 'value', None)])

        def leave_SelectionSet(self, node, *args):
            visited.append(['leave', type(node).__name__, getattr(node, 'value', None)])

    visit(ast, TestVisitor())

    assert visited == [
        ['enter', 'SelectionSet', None],
        ['enter', 'Name', 'a'],
        ['enter', 'Name', 'b'],
        ['enter', 'SelectionSet', None],
        ['enter', 'Name', 'x'],
        ['leave', 'SelectionSet', None],
        ['enter', 'Name', 'c'],
        ['leave', 'SelectionSet', None],
    ]


def test_visits_kitchen_sink():
    visited = []
    ast = parse(KITCHEN_SINK)

    class TestVisitor(Visitor):
        def enter(self, node, key, parent, *args):
            kind = parent and type(parent).__name__
            if kind == 'list':
                kind = None
            visited.append(['enter', type(node).__name__, key, kind])

        def leave(self, node, key, parent, *args):
            kind = parent and type(parent).__name__
            if kind == 'list':
                kind = None
            visited.append(['leave', type(node).__name__, key, kind])

    visit(ast, TestVisitor())
    assert visited == [
        ['enter', 'Document', None, None],
        ['enter', 'OperationDefinition', 0, None],
        ['enter', 'Name', 'name', 'OperationDefinition'],
        ['leave', 'Name', 'name', 'OperationDefinition'],
        ['enter', 'VariableDefinition', 0, None],
        ['enter', 'Variable', 'variable', 'VariableDefinition'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'variable', 'VariableDefinition'],
        ['enter', 'NamedType', 'type', 'VariableDefinition'],
        ['enter', 'Name', 'name', 'NamedType'],
        ['leave', 'Name', 'name', 'NamedType'],
        ['leave', 'NamedType', 'type', 'VariableDefinition'],
        ['leave', 'VariableDefinition', 0, None],
        ['enter', 'VariableDefinition', 1, None],
        ['enter', 'Variable', 'variable', 'VariableDefinition'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'variable', 'VariableDefinition'],
        ['enter', 'NamedType', 'type', 'VariableDefinition'],
        ['enter', 'Name', 'name', 'NamedType'],
        ['leave', 'Name', 'name', 'NamedType'],
        ['leave', 'NamedType', 'type', 'VariableDefinition'],
        ['enter', 'EnumValue', 'default_value', 'VariableDefinition'],
        ['leave', 'EnumValue', 'default_value', 'VariableDefinition'],
        ['leave', 'VariableDefinition', 1, None],
        ['enter', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'alias', 'Field'],
        ['leave', 'Name', 'alias', 'Field'],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'ListValue', 'value', 'Argument'],
        ['enter', 'IntValue', 0, None],
        ['leave', 'IntValue', 0, None],
        ['enter', 'IntValue', 1, None],
        ['leave', 'IntValue', 1, None],
        ['leave', 'ListValue', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['enter', 'InlineFragment', 1, None],
        ['enter', 'NamedType', 'type_condition', 'InlineFragment'],
        ['enter', 'Name', 'name', 'NamedType'],
        ['leave', 'Name', 'name', 'NamedType'],
        ['leave', 'NamedType', 'type_condition', 'InlineFragment'],
        ['enter', 'Directive', 0, None],
        ['enter', 'Name', 'name', 'Directive'],
        ['leave', 'Name', 'name', 'Directive'],
        ['leave', 'Directive', 0, None],
        ['enter', 'SelectionSet', 'selection_set', 'InlineFragment'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['enter', 'Field', 1, None],
        ['enter', 'Name', 'alias', 'Field'],
        ['leave', 'Name', 'alias', 'Field'],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'IntValue', 'value', 'Argument'],
        ['leave', 'IntValue', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['enter', 'Argument', 1, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'Variable', 'value', 'Argument'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'value', 'Argument'],
        ['leave', 'Argument', 1, None],
        ['enter', 'Directive', 0, None],
        ['enter', 'Name', 'name', 'Directive'],
        ['leave', 'Name', 'name', 'Directive'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'Variable', 'value', 'Argument'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['leave', 'Directive', 0, None],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['enter', 'FragmentSpread', 1, None],
        ['enter', 'Name', 'name', 'FragmentSpread'],
        ['leave', 'Name', 'name', 'FragmentSpread'],
        ['leave', 'FragmentSpread', 1, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 1, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'InlineFragment'],
        ['leave', 'InlineFragment', 1, None],
        ['enter', 'InlineFragment', 2, None],
        ['enter', 'Directive', 0, None],
        ['enter', 'Name', 'name', 'Directive'],
        ['leave', 'Name', 'name', 'Directive'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'Variable', 'value', 'Argument'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['leave', 'Directive', 0, None],
        ['enter', 'SelectionSet', 'selection_set', 'InlineFragment'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'InlineFragment'],
        ['leave', 'InlineFragment', 2, None],
        ['enter', 'InlineFragment', 3, None],
        ['enter', 'SelectionSet', 'selection_set', 'InlineFragment'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'InlineFragment'],
        ['leave', 'InlineFragment', 3, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['leave', 'OperationDefinition', 0, None],
        ['enter', 'OperationDefinition', 1, None],
        ['enter', 'Name', 'name', 'OperationDefinition'],
        ['leave', 'Name', 'name', 'OperationDefinition'],
        ['enter', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'IntValue', 'value', 'Argument'],
        ['leave', 'IntValue', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['enter', 'Directive', 0, None],
        ['enter', 'Name', 'name', 'Directive'],
        ['leave', 'Name', 'name', 'Directive'],
        ['leave', 'Directive', 0, None],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['leave', 'OperationDefinition', 1, None],
        ['enter', 'OperationDefinition', 2, None],
        ['enter', 'Name', 'name', 'OperationDefinition'],
        ['leave', 'Name', 'name', 'OperationDefinition'],
        ['enter', 'VariableDefinition', 0, None],
        ['enter', 'Variable', 'variable', 'VariableDefinition'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'variable', 'VariableDefinition'],
        ['enter', 'NamedType', 'type', 'VariableDefinition'],
        ['enter', 'Name', 'name', 'NamedType'],
        ['leave', 'Name', 'name', 'NamedType'],
        ['leave', 'NamedType', 'type', 'VariableDefinition'],
        ['leave', 'VariableDefinition', 0, None],
        ['enter', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'Variable', 'value', 'Argument'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 0, None],
        ['enter', 'Field', 1, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'SelectionSet', 'selection_set', 'Field'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 1, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'Field'],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['leave', 'OperationDefinition', 2, None],
        ['enter', 'FragmentDefinition', 3, None],
        ['enter', 'Name', 'name', 'FragmentDefinition'],
        ['leave', 'Name', 'name', 'FragmentDefinition'],
        ['enter', 'NamedType', 'type_condition', 'FragmentDefinition'],
        ['enter', 'Name', 'name', 'NamedType'],
        ['leave', 'Name', 'name', 'NamedType'],
        ['leave', 'NamedType', 'type_condition', 'FragmentDefinition'],
        ['enter', 'SelectionSet', 'selection_set', 'FragmentDefinition'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'Variable', 'value', 'Argument'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['enter', 'Argument', 1, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'Variable', 'value', 'Argument'],
        ['enter', 'Name', 'name', 'Variable'],
        ['leave', 'Name', 'name', 'Variable'],
        ['leave', 'Variable', 'value', 'Argument'],
        ['leave', 'Argument', 1, None],
        ['enter', 'Argument', 2, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'ObjectValue', 'value', 'Argument'],
        ['enter', 'ObjectField', 0, None],
        ['enter', 'Name', 'name', 'ObjectField'],
        ['leave', 'Name', 'name', 'ObjectField'],
        ['enter', 'StringValue', 'value', 'ObjectField'],
        ['leave', 'StringValue', 'value', 'ObjectField'],
        ['leave', 'ObjectField', 0, None],
        ['leave', 'ObjectValue', 'value', 'Argument'],
        ['leave', 'Argument', 2, None],
        ['leave', 'Field', 0, None],
        ['leave', 'SelectionSet', 'selection_set', 'FragmentDefinition'],
        ['leave', 'FragmentDefinition', 3, None],
        ['enter', 'OperationDefinition', 4, None],
        ['enter', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['enter', 'Field', 0, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['enter', 'Argument', 0, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'BooleanValue', 'value', 'Argument'],
        ['leave', 'BooleanValue', 'value', 'Argument'],
        ['leave', 'Argument', 0, None],
        ['enter', 'Argument', 1, None],
        ['enter', 'Name', 'name', 'Argument'],
        ['leave', 'Name', 'name', 'Argument'],
        ['enter', 'BooleanValue', 'value', 'Argument'],
        ['leave', 'BooleanValue', 'value', 'Argument'],
        ['leave', 'Argument', 1, None],
        ['leave', 'Field', 0, None],
        ['enter', 'Field', 1, None],
        ['enter', 'Name', 'name', 'Field'],
        ['leave', 'Name', 'name', 'Field'],
        ['leave', 'Field', 1, None],
        ['leave', 'SelectionSet', 'selection_set', 'OperationDefinition'],
        ['leave', 'OperationDefinition', 4, None],
        ['leave', 'Document', None, None]
    ]
