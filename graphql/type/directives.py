from graphql.type.definition import GraphQLNonNull
from graphql.type.scalars import GraphQLBoolean


class GraphQLDirective(object):
    pass


class GraphQLIncludeDirective(GraphQLDirective):
    name = 'include'
    args = [{
        'name': 'if',
        'type': GraphQLNonNull(GraphQLBoolean),
        'description': 'Directs the executor to include this field or fragment only when the `if` argument is true.',
    }]


class GraphQLSkipDirective(GraphQLDirective):
    name = 'skip'
    args = [{
        'name': 'if',
        'type': GraphQLNonNull(GraphQLBoolean),
        'description': 'Directs the executor to skip this field or fragment only when the `if` argument is true.',
    }]
