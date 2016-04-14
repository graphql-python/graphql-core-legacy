from ...error import GraphQLError
from ...language import ast
from .base import ValidationRule


class KnownArgumentNames(ValidationRule):

    def enter_Argument(self, node, key, parent, path, ancestors):
        argument_of = ancestors[-1]

        if isinstance(argument_of, ast.Field):
            field_def = self.context.get_field_def()
            if not field_def:
                return

            field_arg_def = next((arg for arg in field_def.args if arg.name == node.name.value), None)

            if not field_arg_def:
                parent_type = self.context.get_parent_type()
                assert parent_type
                self.context.report_error(GraphQLError(
                    self.unknown_arg_message(node.name.value, field_def.name, parent_type.name),
                    [node]
                ))

        elif isinstance(argument_of, ast.Directive):
            directive = self.context.get_directive()
            if not directive:
                return

            directive_arg_def = next((arg for arg in directive.args if arg.name == node.name.value), None)

            if not directive_arg_def:
                self.context.report_error(GraphQLError(
                    self.unknown_directive_arg_message(node.name.value, directive.name),
                    [node]
                ))

    @staticmethod
    def unknown_arg_message(arg_name, field_name, type):
        return 'Unknown argument "{}" on field "{}" of type "{}".'.format(arg_name, field_name, type)

    @staticmethod
    def unknown_directive_arg_message(arg_name, directive_name):
        return 'Unknown argument "{}" on directive "@{}".'.format(arg_name, directive_name)
