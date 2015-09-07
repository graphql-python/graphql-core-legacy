from copy import copy
from collections import namedtuple
from . import ast

QUERY_DOCUMENT_KEYS = {
    ast.Name: (),

    ast.Document: ('definitions', ),
    ast.OperationDefinition: ('name', 'variable_definitions', 'directives', 'selection_set'),
    ast.VariableDefinition: ('variable', 'type', 'default_value'),
    ast.Variable: ('name', ),
    ast.SelectionSet: ('selections', ),
    ast.Field: ('alias', 'name', 'arguments', 'directives', 'selection_set'),
    ast.Argument: ('name', 'value'),

    ast.FragmentSpread: ('name', 'directives'),
    ast.InlineFragment: ('type_condition', 'directives', 'selection_set'),
    ast.FragmentDefinition: ('name', 'type_condition', 'directives', 'selection_set'),

    ast.IntValue: (),
    ast.FloatValue: (),
    ast.StringValue: (),
    ast.BooleanValue: (),
    ast.EnumValue: (),
    ast.ListValue: ('values', ),
    ast.ObjectValue: ('fields', ),
    ast.ObjectField: ('name', 'value'),

    ast.Directive: ('name', 'arguments'),

    ast.NamedType: ('name', ),
    ast.ListType: ('type', ),
    ast.NonNullType: ('type', ),
}

BREAK = object()
REMOVE = object()

Stack = namedtuple('Stack', 'in_array index keys edits prev')


def visit(root, visitor, key_map=None):
    visitor_keys = key_map or QUERY_DOCUMENT_KEYS

    stack = None
    in_array = isinstance(root, list)
    keys = [root]
    index = -1
    edits = []
    parent = None
    path = []
    ancestors = []
    new_root = root

    while True:
        index += 1
        is_leaving = index == len(keys)
        key = None
        node = None
        is_edited = is_leaving and len(edits) != 0
        if is_leaving:
            key = path.pop() if len(ancestors) != 0 else None
            node = parent
            parent = ancestors.pop() if len(ancestors) != 0 else None
            if is_edited:
                if in_array:
                    node = list(node)
                else:
                    node = copy(node)
                edit_offset = 0
                for edit_key, edit_value in edits:
                    if in_array:
                        edit_key -= edit_offset
                    if in_array and edit_value is REMOVE:
                        node.pop(edit_key)
                        edit_offset += 1
                    else:
                        if isinstance(node, list):
                            node[edit_key] = edit_value
                        else:
                            node = node._replace(**{edit_key: edit_value})
            index = stack.index
            keys = stack.keys
            edits = stack.edits
            in_array = stack.in_array
            stack = stack.prev
        else:
            if parent:
                key = index if in_array else keys[index]
                if isinstance(parent, list):
                    node = parent[key]
                else:
                    node = getattr(parent, key, None)
            else:
                key = None
                node = new_root
            if node is None:
                continue
            if parent:
                path.append(key)

        result = None
        if not isinstance(node, list):
            assert is_node(node), 'Invalid AST Node: ' + node
            if is_leaving:
                result = visitor.leave(node, key, parent, path, ancestors)
            else:
                result = visitor.enter(node, key, parent, path, ancestors)
            if result is BREAK:
                break

            if result is False:
                if not is_leaving:
                    path.pop()
                    continue
            elif result is not None:
                edits.append((key, result))
                if not is_leaving:
                    if result is not REMOVE:
                        # TODO: check result is valid node
                        node = result
                    else:
                        path.pop()
                        continue

        if result is None and is_edited:
            edits.append((key, node))

        if not is_leaving:
            stack = Stack(in_array, index, keys, edits, prev=stack)
            in_array = isinstance(node, list)
            keys = node if in_array else visitor_keys.get(type(node), [])
            index = -1
            edits = []
            if parent:
                ancestors.append(parent)
            parent = node

        if not stack:
            break

    if edits:
        new_root = edits[0][1]

    return new_root


def is_node(maybe_node):
    return isinstance(maybe_node, object)  # FIXME


class Visitor(object):
    def enter(self, node, key, parent, path, ancestors):
        return self._call_kind_specific_visitor('enter_', node, key, parent, path, ancestors)

    def leave(self, node, key, parent, path, ancestors):
        return self._call_kind_specific_visitor('leave_', node, key, parent, path, ancestors)

    def _call_kind_specific_visitor(self, prefix, node, key, parent, path, ancestors):
        node_kind = type(node).__name__
        method_name = prefix + node_kind
        method = getattr(self, method_name, None)
        if method:
            return method(node, key, parent, path, ancestors)
