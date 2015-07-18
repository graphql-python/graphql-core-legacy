from graphql.type.definition import GraphQLNonNull, GraphQLArgument
from graphql.type.scalars import GraphQLBoolean


class GraphQLDirective(object):
    pass


def arg(name, *args, **kwargs):
    a = GraphQLArgument(*args, **kwargs)
    a.name = name
    return a


class GraphQLIncludeDirective(GraphQLDirective):
    name = 'include'
    args = [arg(
        'if',
        type=GraphQLNonNull(GraphQLBoolean),
        description='Directs the executor to include this field or fragment only when the `if` argument is true.',
    )]
    on_operation = False
    on_fragment = True
    on_field = True


class GraphQLSkipDirective(GraphQLDirective):
    name = 'skip'
    args = [arg(
        'if',
        type=GraphQLNonNull(GraphQLBoolean),
        description='Directs the executor to skip this field or fragment only when the `if` argument is true.',
    )]
    on_operation = False
    on_fragment = True
    on_field = True
