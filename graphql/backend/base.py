from ..language import ast
from abc import ABCMeta, abstractmethod
import six



class GraphQLBackend(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def document_from_string(self, schema, request_string):
        raise NotImplementedError(
            "document_from_string method not implemented in {}.".format(self.__class__)
        )


class GraphQLDocument(object):
    def __init__(self, schema, document_string, document_ast, execute):
        self.schema = schema
        self.document_string = document_string
        self.document_ast = document_ast
        self.execute = execute

    def get_operations(self):
        document_ast = self.document_ast
        operations = {}
        for definition in document_ast.definitions:
            if isinstance(definition, ast.OperationDefinition):
                if definition.name:
                    operation_name = definition.name.value
                else:
                    operation_name =  None
                operations[operation_name] = definition.operation
        return operations
