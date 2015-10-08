from ...error import GraphQLError
from .base import ValidationRule


class KnownTypeNames(ValidationRule):
    def enter_NamedType(self, node, *args):
        type_name = node.name.value
        type = self.context.get_schema().get_type(type_name)

        if not type:
            return GraphQLError(self.unknown_type_message(type_name), [node])

    @staticmethod
    def unknown_type_message(type):
        return 'Unknown type "{}".'.format(type)
