from ...error import GraphQLError
from .base import ValidationRule


class KnownTypeNames(ValidationRule):

    def enter_ObjectTypeDefinition(self, node, *args):
        return False

    def enter_InterfaceTypeDefinition(self, node, *args):
        return False

    def enter_UnionTypeDefinition(self, node, *args):
        return False

    def enter_InputObjectTypeDefinition(self, node, *args):
        return False

    def enter_NamedType(self, node, *args):
        type_name = node.name.value
        type = self.context.get_schema().get_type(type_name)

        if not type:
            self.context.report_error(GraphQLError(self.unknown_type_message(type_name), [node]))

    @staticmethod
    def unknown_type_message(type):
        return 'Unknown type "{}".'.format(type)
