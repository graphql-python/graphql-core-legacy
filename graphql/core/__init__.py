from .executor import execute
from .language.source import Source
from .language.parser import parse


def graphql(schema, request='', root=None, vars=None, operation_name=None):
    source = Source(request, 'GraphQL request')
    ast = parse(source)
    # TODO: validate document
    return execute(
        schema,
        root or object(),
        ast,
        vars or {},
        operation_name
    )
