from ...error import GraphQLError
from ...language.printer import print_ast
from ...utils.is_valid_literal_value import is_valid_literal_value
from .base import ValidationRule


class ArgumentsOfCorrectType(ValidationRule):
    def enter_Argument(self, node, key, parent, path, ancestors):
        arg_def = self.context.get_argument()
        if arg_def and not is_valid_literal_value(arg_def.type, node.value):
            return GraphQLError(
                self.bad_value_message(node.name.value, arg_def.type,
                                       print_ast(node.value)),
                [node.value]
            )

    @staticmethod
    def bad_value_message(arg_name, type, value):
        return 'Argument "{}" expected type "{}" but got: {}.'.format(arg_name, type, value)
