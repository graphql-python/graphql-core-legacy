from ..error import GraphQLError
from ..language.visitor import Visitor


class ValidationRule(Visitor):
    def __init__(self, context):
        self.context = context


class UniqueOperationNames(ValidationRule):
    def __init__(self, context):
        super(UniqueOperationNames, self).__init__(context)
        self.known_operation_names = {}

    def enter_OperationDefinition(self, node, *args):
        operation_name = node.name
        if operation_name:
            if operation_name.value in self.known_operation_names:
                return GraphQLError(
                    self.message(operation_name.value),
                    [self.known_operation_names[operation_name.value], operation_name]
                )
            self.known_operation_names[operation_name.value] = operation_name

    @staticmethod
    def message(operation_name):
        return 'There can only be one operation named "{}".'.format(operation_name)
