from ..language.ast import FragmentDefinition, FragmentSpread, VariableDefinition, Variable, OperationDefinition
from ..utils.type_info import TypeInfo
from ..language.visitor import Visitor, visit


class VariableUsage(object):
    __slots__ = 'node', 'type'

    def __init__(self, node, type):
        self.node = node
        self.type = type


class UsageVisitor(Visitor):
    __slots__ = 'context', 'usages', 'type_info'

    def __init__(self, usages, type_info):
        self.usages = usages
        self.type_info = type_info

    def enter(self, node, key, parent, path, ancestors):
        self.type_info.enter(node)
        if isinstance(node, VariableDefinition):
            return False
        elif isinstance(node, Variable):
            usage = VariableUsage(node, type=self.type_info.get_input_type())
            self.usages.append(usage)

    def leave(self, node, key, parent, path, ancestors):
        self.type_info.leave(node)


class ValidationContext(object):
    __slots__ = '_schema', '_ast', '_type_info', '_fragments', '_fragment_spreads', '_recursively_referenced_fragments', '_variable_usages', '_recursive_variable_usages'

    def __init__(self, schema, ast, type_info):
        self._schema = schema
        self._ast = ast
        self._type_info = type_info
        self._fragments = None
        self._fragment_spreads = {}
        self._recursively_referenced_fragments = {}
        self._variable_usages = {}
        self._recursive_variable_usages = {}

    def get_schema(self):
        return self._schema

    def get_variable_usages(self, node):
        usages = self._variable_usages.get(node)
        if usages is None:
            usages = []
            sub_visitor = UsageVisitor(usages, self._type_info)
            visit(node, sub_visitor)
            self._variable_usages[node] = usages

        return usages

    def get_recursive_variable_usages(self, operation):
        assert isinstance(operation, OperationDefinition)
        usages = self._recursive_variable_usages.get(operation)
        if usages is None:
            usages = self.get_variable_usages(operation)
            fragments = self.get_recursively_referenced_fragments(operation)
            for fragment in fragments:
                usages.extend(self.get_variable_usages(fragment))
            self._recursive_variable_usages[operation] = usages

        return usages

    def get_recursively_referenced_fragments(self, operation):
        assert isinstance(operation, OperationDefinition)
        fragments = self._recursively_referenced_fragments.get(operation)
        if not fragments:
            fragments = []
            collected_names = set()
            nodes_to_visit = [operation]
            while nodes_to_visit:
                node = nodes_to_visit.pop()
                spreads = self.get_fragment_spreads(node)
                for spread in spreads:
                    frag_name = spread.name.value
                    if frag_name not in collected_names:
                        collected_names.add(frag_name)
                        fragment = self.get_fragment(frag_name)
                        if fragment:
                            fragments.append(fragment)
                            nodes_to_visit.append(fragment)
            self._recursively_referenced_fragments[operation] = fragments
        return fragments

    def get_fragment_spreads(self, node):
        spreads = self._fragment_spreads.get(node)
        if not spreads:
            spreads = []
            self.gather_spreads(spreads, node.selection_set)
            self._fragment_spreads[node] = spreads
        return spreads

    def get_ast(self):
        return self._ast

    def get_fragment(self, name):
        fragments = self._fragments
        if fragments is None:
            self._fragments = fragments = {}
            for statement in self.get_ast().definitions:
                if isinstance(statement, FragmentDefinition):
                    fragments[statement.name.value] = statement
        return fragments.get(name)

    def get_type(self):
        return self._type_info.get_type()

    def get_parent_type(self):
        return self._type_info.get_parent_type()

    def get_input_type(self):
        return self._type_info.get_input_type()

    def get_field_def(self):
        return self._type_info.get_field_def()

    def get_directive(self):
        return self._type_info.get_directive()

    def get_argument(self):
        return self._type_info.get_argument()

    @classmethod
    def gather_spreads(cls, spreads, node):
        for selection in node.selections:
            if isinstance(selection, FragmentSpread):
                spreads.append(selection)
            elif selection.selection_set:
                cls.gather_spreads(spreads, selection.selection_set)
