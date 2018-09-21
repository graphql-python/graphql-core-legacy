from typing import Set

from ...error import GraphQLError
from ...language import OperationDefinitionNode, VariableDefinitionNode
from . import ValidationContext, ValidationRule

__all__ = ["NoUndefinedVariablesRule", "undefined_var_message"]


def undefined_var_message(var_name, op_name=None):
    return (
        "Variable '${}' is not defined by operation '{}'.".format(var_name, op_name)
        if op_name
        else "Variable '${}' is not defined.".format(var_name)
    )


class NoUndefinedVariablesRule(ValidationRule):
    """No undefined variables

    A GraphQL operation is only valid if all variables encountered, both
    directly and via fragment spreads, are defined by that operation.
    """

    def __init__(self, context):
        super(NoUndefinedVariablesRule, self).__init__(context)
        self.defined_variable_names = set()

    def enter_operation_definition(self, *_args):
        self.defined_variable_names.clear()

    def leave_operation_definition(self, operation, *_args):
        usages = self.context.get_recursive_variable_usages(operation)
        defined_variables = self.defined_variable_names
        for usage in usages:
            node = usage.node
            var_name = node.name.value
            if var_name not in defined_variables:
                op_name = operation.name.value if operation.name else None
                self.report_error(
                    GraphQLError(
                        undefined_var_message(var_name, op_name), [node, operation]
                    )
                )

    def enter_variable_definition(self, node, *_args):
        self.defined_variable_names.add(node.variable.name.value)
