from six import string_types
from .base import GraphQLDocument


class GraphQLCompiledDocument(GraphQLDocument):
    @classmethod
    def from_code(cls, schema, code, uptodate=None, extra_namespace=None):
        """Creates a GraphQLDocument object from compiled code and the globals.  This
        is used by the loaders and schema to create a document object.
        """
        if isinstance(code, string_types):
            filename = '<document>'
            code = compile(code, filename, 'exec')
        namespace = {"__file__": code.co_filename}
        exec(code, namespace)
        if extra_namespace:
            namespace.update(extra_namespace)
        rv = cls._from_namespace(schema, namespace)
        rv._uptodate = uptodate
        return rv

    @classmethod
    def from_module_dict(cls, schema, module_dict):
        """Creates a template object from a module.  This is used by the
        module loader to create a document object.
        """
        return cls._from_namespace(schema, module_dict)

    @classmethod
    def _from_namespace(cls, schema, namespace):
        document_string = namespace.get("document_string", "")
        document_ast = namespace.get("document_ast")
        execute = namespace["execute"]

        namespace["schema"] = schema
        return cls(
            schema=schema,
            document_string=document_string,
            document_ast=document_ast,
            execute=execute,
        )
