from ...error import GraphQLError
from ...language import ast
from .base import ValidationRule


class NoUndefinedVariables(ValidationRule):
    __slots__ = 'visited_fragment_names', 'defined_variable_names', 'operation',
    visit_spread_fragments = True

    def __init__(self, context):
        self.visited_fragment_names = set()
        self.defined_variable_names = set()
        self.operation = None

        super(NoUndefinedVariables, self).__init__(context)

    @staticmethod
    def undefined_var_message(var_name):
        return 'Variable "${}" is not defined.'.format(var_name)

    @staticmethod
    def undefined_var_by_op_message(var_name, op_name):
        return 'Variable "${}" is not defined by operation "{}".'.format(
            var_name, op_name
        )

    def enter_OperationDefinition(self, node, key, parent, path, ancestors):
        self.operation = node
        self.visited_fragment_names = set()
        self.defined_variable_names = set()

    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        self.defined_variable_names.add(node.variable.name.value)

    def enter_Variable(self, variable, key, parent, path, ancestors):
        var_name = variable.name.value
        if var_name not in self.defined_variable_names:
            within_fragment = any(isinstance(node, ast.FragmentDefinition) for node in ancestors)
            if within_fragment and self.operation and self.operation.name:
                return GraphQLError(
                    self.undefined_var_by_op_message(var_name, self.operation.name.value),
                    [variable, self.operation]
                )

            return GraphQLError(
                self.undefined_var_message(var_name),
                [variable]
            )

    def enter_FragmentSpread(self, spread_ast, *args):
        if spread_ast.name.value in self.visited_fragment_names:
            return False

        self.visited_fragment_names.add(spread_ast.name.value)
