from ..language.ast import FragmentDefinition, FragmentSpread


class ValidationContext(object):
    __slots__ = '_schema', '_ast', '_type_info', '_fragments', '_fragment_spreads'

    def __init__(self, schema, ast, type_info):
        self._schema = schema
        self._ast = ast
        self._type_info = type_info
        self._fragments = None
        self._fragment_spreads = {}

    def get_schema(self):
        return self._schema

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
