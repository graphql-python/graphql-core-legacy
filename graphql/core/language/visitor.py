from copy import copy
import six
from . import ast

QUERY_DOCUMENT_KEYS = {
    ast.Name: (),

    ast.Document: ('definitions',),
    ast.OperationDefinition: ('name', 'variable_definitions', 'directives', 'selection_set'),
    ast.VariableDefinition: ('variable', 'type', 'default_value'),
    ast.Variable: ('name',),
    ast.SelectionSet: ('selections',),
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
    ast.ListValue: ('values',),
    ast.ObjectValue: ('fields',),
    ast.ObjectField: ('name', 'value'),

    ast.Directive: ('name', 'arguments'),

    ast.NamedType: ('name',),
    ast.ListType: ('type',),
    ast.NonNullType: ('type',),

    ast.ObjectTypeDefinition: ('name', 'interfaces', 'fields'),
    ast.FieldDefinition: ('name', 'arguments', 'type'),
    ast.InputValueDefinition: ('name', 'type', 'defaultValue'),
    ast.InterfaceTypeDefinition: ('name', 'fields'),
    ast.UnionTypeDefinition: ('name', 'types'),
    ast.ScalarTypeDefinition: ('name',),
    ast.EnumTypeDefinition: ('name', 'values'),
    ast.EnumValueDefinition: ('name',),
    ast.InputObjectTypeDefinition: ('name', 'fields'),
    ast.TypeExtensionDefinition: ('definition',),
}

AST_KIND_TO_TYPE = {c.__name__: c for c in QUERY_DOCUMENT_KEYS.keys()}

BREAK = object()
REMOVE = object()


class Stack(object):
    __slots__ = 'in_array', 'index', 'keys', 'edits', 'prev'

    def __init__(self, in_array, index, keys, edits, prev):
        self.in_array = in_array
        self.index = index
        self.keys = keys
        self.edits = edits
        self.prev = prev


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
    leave = visitor.leave
    enter = visitor.enter
    path_pop = path.pop
    ancestors_pop = ancestors.pop

    while True:
        index += 1
        is_leaving = index == len(keys)
        is_edited = is_leaving and edits
        if is_leaving:
            key = path_pop() if ancestors else None
            node = parent
            parent = ancestors_pop() if ancestors else None

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
                            setattr(node, edit_key, edit_value)

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
            assert isinstance(node, ast.Node), 'Invalid AST Node: ' + repr(node)

            if is_leaving:
                result = leave(node, key, parent, path, ancestors)

            else:
                result = enter(node, key, parent, path, ancestors)

            if result is BREAK:
                break

            if result is False:
                if not is_leaving:
                    path_pop()
                    continue

            elif result is not None:
                edits.append((key, result))
                if not is_leaving:
                    if result is not REMOVE:
                        # TODO: check result is valid node
                        node = result

                    else:
                        path_pop()
                        continue

        if result is None and is_edited:
            edits.append((key, node))

        if not is_leaving:
            stack = Stack(in_array, index, keys, edits, stack)
            in_array = isinstance(node, list)
            keys = node if in_array else visitor_keys.get(type(node), None) or []
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


class VisitorMeta(type):
    def __new__(cls, name, bases, attrs):
        enter_handlers = {}
        leave_handlers = {}

        for base in bases:
            if hasattr(base, '_enter_handlers'):
                enter_handlers.update(base._enter_handlers)
            if hasattr(base, '_leave_handlers'):
                leave_handlers.update(base._leave_handlers)

        for attr, val in attrs.items():
            if attr.startswith('enter_'):
                ast_kind = attr[6:]
                ast_type = AST_KIND_TO_TYPE.get(ast_kind)
                enter_handlers[ast_type] = val

            elif attr.startswith('leave_'):
                ast_kind = attr[6:]
                ast_type = AST_KIND_TO_TYPE.get(ast_kind)
                leave_handlers[ast_type] = val

        attrs['_get_enter_handler'] = enter_handlers.get
        attrs['_get_leave_handler'] = leave_handlers.get
        return super(VisitorMeta, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(VisitorMeta)
class Visitor(object):
    def enter(self, node, key, parent, path, ancestors):
        method = self._get_enter_handler(type(node))
        if method:
            return method(self, node, key, parent, path, ancestors)

    def leave(self, node, key, parent, path, ancestors):
        method = self._get_leave_handler(type(node))
        if method:
            return method(self, node, key, parent, path, ancestors)
