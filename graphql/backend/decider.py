from .base import GraphQLBackend


class GraphQLDeciderBackend(GraphQLBackend):
    def __init__(self, backends=None):
        if not backends:
            raise Exception("Need to provide backends to decide into.")
        if not isinstance(backends, (list, tuple)):
            raise Exception("Provided backends need to be a list or tuple.")
        self.backends = backends
        super(GraphQLDeciderBackend, self).__init__()

    def document_from_string(self, schema, request_string):
        for backend in self.backends:
            try:
                return backend.document_from_string(schema, request_string)
            except Exception as e:
                continue

        raise Exception(
            "GraphQLDeciderBackend was not able to retrieve a document. Backends tried: {}".format(
                repr(self.backends)
            )
        )
