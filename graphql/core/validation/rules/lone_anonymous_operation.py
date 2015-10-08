from ...error import GraphQLError
from ...language import ast
from .base import ValidationRule


class LoneAnonymousOperation(ValidationRule):
    operation_count = 0

    def __init__(self, context):
        super(LoneAnonymousOperation, self).__init__(context)

    def enter_Document(self, node, key, parent, path, ancestors):
        self.operation_count = \
            sum(1 for definition in node.definitions if isinstance(definition, ast.OperationDefinition))

    def enter_OperationDefinition(self, node, key, parent, path, ancestors):
        if not node.name and self.operation_count > 1:
            return GraphQLError(self.anonymous_operation_not_alone_message(), [node])

    @staticmethod
    def anonymous_operation_not_alone_message():
        return 'This anonymous operation must be the only defined operation.'
