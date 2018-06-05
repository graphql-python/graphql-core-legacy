from ..pyutils.cached_property import cached_property
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

    @cached_property
    def operations_map(self):
        '''
        returns a Mapping of operation names and it's associated types.
        E.g. {'myQuery': 'query', 'myMutation': 'mutation'}
        '''
        document_ast = self.document_ast
        operations = {}
        for definition in document_ast.definitions:
            if isinstance(definition, ast.OperationDefinition):
                if definition.name:
                    operation_name = definition.name.value
                else:
                    operation_name = None
                operations[operation_name] = definition.operation
        return operations

    def get_operation_type(self, operation_name):
        '''
        Returns the operation type ('query', 'mutation', 'subscription' or None)
        for the given operation_name.
        If no operation_name is provided (and only one operation exists) it will return the
        operation type for that operation
        '''
        operations_map = self.operations_map
        if not operation_name and len(operations_map) == 1:
            return next(iter(operations_map.values()))
        return operations_map.get(operation_name)
