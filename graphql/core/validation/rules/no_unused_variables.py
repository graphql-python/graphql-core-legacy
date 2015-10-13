from ...error import GraphQLError
from .base import ValidationRule


class NoUnusedVariables(ValidationRule):
    __slots__ = 'visited_fragment_names', 'variable_definitions', 'variable_name_used', 'visit_spread_fragments'

    def __init__(self, context):
        self.visited_fragment_names = None
        self.variable_definitions = None
        self.variable_name_used = None
        self.visit_spread_fragments = True
        super(NoUnusedVariables, self).__init__(context)

    def enter_OperationDefinition(self, node, key, parent, path, ancestors):
        self.visited_fragment_names = set()
        self.variable_definitions = []
        self.variable_name_used = set()

    def leave_OperationDefinition(self, node, key, parent, path, ancestors):
        errors = [
            GraphQLError(
                self.unused_variable_message(variable_definition.variable.name.value),
                [variable_definition]
            )
            for variable_definition in self.variable_definitions
            if variable_definition.variable.name.value not in self.variable_name_used
            ]

        if errors:
            return errors

    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        if self.variable_definitions is not None:
            self.variable_definitions.append(node)

        return False

    def enter_Variable(self, node, key, parent, path, ancestors):
        if self.variable_name_used is not None:
            self.variable_name_used.add(node.name.value)

    def enter_FragmentSpread(self, node, key, parent, path, ancestors):
        if self.visited_fragment_names is not None:
            spread_name = node.name.value
            if spread_name in self.visited_fragment_names:
                return False

            self.visited_fragment_names.add(spread_name)

    @staticmethod
    def unused_variable_message(variable_name):
        return 'Variable "${}" is never used.'.format(variable_name)
