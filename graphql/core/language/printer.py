import json
from .visitor import Visitor, visit

__all__ = ['print_ast']


def print_ast(ast):
    return visit(ast, PrintingVisitor())


class PrintingVisitor(Visitor):
    def leave_Name(self, node, *args):
        return node.value

    def leave_Variable(self, node, *args):
        return '$' + node.name

    def leave_Document(self, node, *args):
        return join(node.definitions, '\n\n') + '\n'

    def leave_OperationDefinition(self, node, *args):
        name = node.name
        selection_set = node.selection_set
        if not name:
            return selection_set
        op = node.operation
        defs = wrap('(', join(node.variable_definitions, ', '), ')')
        directives = join(node.directives, ' ')
        return join([op, join([name, defs]), directives, selection_set], ' ')

    def leave_VariableDefinition(self, node, *args):
        return node.variable + ': ' + node.type + wrap(' = ', node.default_value)

    def leave_SelectionSet(self, node, *args):
        return block(node.selections)

    def leave_Field(self, node, *args):
        return join([
            wrap('', node.alias, ': ') + node.name + wrap('(', join(node.arguments, ', '), ')'),
            join(node.directives, ' '),
            node.selection_set
        ], ' ')

    def leave_Argument(self, node, *args):
        return node.name + ': ' + node.value

    # Fragments

    def leave_FragmentSpread(self, node, *args):
        return '...' + node.name + wrap(' ', join(node.directives, ' '))

    def leave_InlineFragment(self, node, *args):
        return ('... on ' + node.type_condition + ' ' +
                wrap('', join(node.directives, ' '), ' ') +
                node.selection_set)

    def leave_FragmentDefinition(self, node, *args):
        return ('fragment {} on {} '.format(node.name, node.type_condition) +
                wrap('', join(node.directives, ' '), ' ') +
                node.selection_set)

    # Value

    def leave_IntValue(self, node, *args):
        return node.value

    def leave_FloatValue(self, node, *args):
        return node.value

    def leave_StringValue(self, node, *args):
        return json.dumps(node.value)

    def leave_BooleanValue(self, node, *args):
        return json.dumps(node.value)

    def leave_EnumValue(self, node, *args):
        return node.value

    def leave_ListValue(self, node, *args):
        return '[' + join(node.values, ', ') + ']'

    def leave_ObjectValue(self, node, *args):
        return '{' + join(node.fields, ', ') + '}'

    def leave_ObjectField(self, node, *args):
        return node.name + ': ' + node.value

    # Directive

    def leave_Directive(self, node, *args):
        return '@' + node.name + wrap('(', join(node.arguments, ', '), ')')

    # Type

    def leave_NamedType(self, node, *args):
        return node.name

    def leave_ListType(self, node, *args):
        return '[' + node.type + ']'

    def leave_NonNullType(self, node, *args):
        return node.type + '!'


def join(maybe_list, separator=''):
    if maybe_list:
        return separator.join(filter(None, maybe_list))
    return ''


def block(maybe_list):
    if maybe_list:
        return indent('{\n' + join(maybe_list, '\n')) + '\n}'
    return ''


def wrap(start, maybe_str, end=''):
    if maybe_str:
        return start + maybe_str + end
    return ''


def indent(maybe_str):
    if maybe_str:
        return maybe_str.replace('\n', '\n  ')
    return maybe_str
