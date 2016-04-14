from ...error import GraphQLError
from ...type.definition import (
    GraphQLNonNull
)
from ...utils.type_from_ast import type_from_ast
from ...utils.type_comparators import is_type_sub_type_of
from .base import ValidationRule


class VariablesInAllowedPosition(ValidationRule):
    __slots__ = 'var_def_map'

    def __init__(self, context):
        super(VariablesInAllowedPosition, self).__init__(context)
        self.var_def_map = {}

    def enter_OperationDefinition(self, node, key, parent, path, ancestors):
        self.var_def_map = {}

    def leave_OperationDefinition(self, operation, key, parent, path, ancestors):
        usages = self.context.get_recursive_variable_usages(operation)

        for usage in usages:
            node = usage.node
            type = usage.type
            var_name = node.name.value
            var_def = self.var_def_map.get(var_name)
            if var_def and type:
                var_type = type_from_ast(self.context.get_schema(), var_def.type)
                if var_type and not is_type_sub_type_of(self.effective_type(var_type, var_def), type):
                    self.context.report_error(GraphQLError(
                        self.bad_var_pos_message(var_name, var_type, type),
                        [var_def, node]
                    ))

    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        self.var_def_map[node.variable.name.value] = node

    @staticmethod
    def effective_type(var_type, var_def):
        if not var_def.default_value or isinstance(var_type, GraphQLNonNull):
            return var_type

        return GraphQLNonNull(var_type)

    @staticmethod
    def bad_var_pos_message(var_name, var_type, expected_type):
        return 'Variable "{}" of type "{}" used in position expecting type "{}".'.format(var_name, var_type,
                                                                                         expected_type)
