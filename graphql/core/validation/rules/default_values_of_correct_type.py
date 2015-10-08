from ...error import GraphQLError
from ...language.printer import print_ast
from ...type.definition import GraphQLNonNull
from ...utils.is_valid_literal_value import is_valid_literal_value
from .base import ValidationRule


class DefaultValuesOfCorrectType(ValidationRule):
    def enter_VariableDefinition(self, node, key, parent, path, ancestors):
        name = node.variable.name.value
        default_value = node.default_value
        type = self.context.get_input_type()

        if isinstance(type, GraphQLNonNull) and default_value:
            return GraphQLError(
                self.default_for_non_null_arg_message(name, type, type.of_type),
                [default_value]
            )

        if type and default_value and not is_valid_literal_value(type, default_value):
            return GraphQLError(
                self.bad_value_for_default_arg_message(name, type, print_ast(default_value)),
                [default_value]
            )

    @staticmethod
    def default_for_non_null_arg_message(var_name, type, guess_type):
        return 'Variable "${}" of type "{}" is required and will not use the default value. ' \
               'Perhaps you meant to use type "{}".'.format(var_name, type, guess_type)

    @staticmethod
    def bad_value_for_default_arg_message(var_name, type, value):
        return 'Variable "${}" of type "{}" has invalid default value: {}.'.format(var_name, type, value)
