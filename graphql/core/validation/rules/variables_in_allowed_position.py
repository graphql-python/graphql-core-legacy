from ...error import GraphQLError
from ...type.definition import (
    GraphQLList,
    GraphQLNonNull
)
from ...utils.type_from_ast import type_from_ast
from .base import ValidationRule


class VariablesInAllowedPosition(ValidationRule):
    visit_spread_fragments = True

    def __init__(self, context):
        super(VariablesInAllowedPosition, self).__init__(context)
        self.var_def_map = {}
        self.visited_fragment_names = set()

    def enter_OperationDefinition(self, node, key, parent, path, ancestors):
        self.var_def_map = {}
        self.visited_fragment_names = set()

    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        self.var_def_map[node.variable.name.value] = node

    def enter_Variable(self, node, key, parent, path, ancestors):
        var_name = node.name.value
        var_def = self.var_def_map.get(var_name)
        var_type = var_def and type_from_ast(self.context.get_schema(), var_def.type)
        input_type = self.context.get_input_type()
        if var_type and input_type and not self.var_type_allowed_for_type(self.effective_type(var_type, var_def),
                                                                          input_type):
            return GraphQLError(self.bad_var_pos_message(var_name, var_type, input_type),
                                [node])

    def enter_FragmentSpread(self, node, key, parent, path, ancestors):
        if node.name.value in self.visited_fragment_names:
            return False
        self.visited_fragment_names.add(node.name.value)

    @staticmethod
    def effective_type(var_type, var_def):
        if not var_def.default_value or isinstance(var_def, GraphQLNonNull):
            return var_type

        return GraphQLNonNull(var_type)

    @classmethod
    def var_type_allowed_for_type(cls, var_type, expected_type):
        if isinstance(expected_type, GraphQLNonNull):
            if isinstance(var_type, GraphQLNonNull):
                return cls.var_type_allowed_for_type(var_type.of_type, expected_type.of_type)

            return False

        if isinstance(var_type, GraphQLNonNull):
            return cls.var_type_allowed_for_type(var_type.of_type, expected_type)

        if isinstance(var_type, GraphQLList) and isinstance(expected_type, GraphQLList):
            return cls.var_type_allowed_for_type(var_type.of_type, expected_type.of_type)

        return var_type == expected_type

    @staticmethod
    def bad_var_pos_message(var_name, var_type, expected_type):
        return 'Variable "{}" of type "{}" used in position expecting type "{}".'.format(var_name, var_type,
                                                                                         expected_type)
