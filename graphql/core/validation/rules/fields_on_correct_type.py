from ...error import GraphQLError
from .base import ValidationRule


class FieldsOnCorrectType(ValidationRule):

    def enter_Field(self, node, key, parent, path, ancestors):
        type = self.context.get_parent_type()
        if not type:
            return

        field_def = self.context.get_field_def()
        if not field_def:
            self.context.report_error(GraphQLError(
                self.undefined_field_message(node.name.value, type.name),
                [node]
            ))

    @staticmethod
    def undefined_field_message(field_name, type):
        return 'Cannot query field "{}" on "{}".'.format(field_name, type)
