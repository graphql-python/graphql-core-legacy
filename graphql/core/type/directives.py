from .definition import GraphQLArgument, GraphQLNonNull
from .scalars import GraphQLBoolean


class GraphQLDirective(object):
    __slots__ = 'name', 'args', 'description', 'on_operation', 'on_fragment', 'on_field'

    def __init__(self, name, description=None, args=None, on_operation=False, on_fragment=False, on_field=False):
        self.name = name
        self.description = description
        self.args = args or []
        self.on_operation = on_operation
        self.on_fragment = on_fragment
        self.on_field = on_field


def arg(name, *args, **kwargs):
    a = GraphQLArgument(*args, **kwargs)
    a.name = name
    return a


GraphQLIncludeDirective = GraphQLDirective(
    name='include',
    args=[arg(
        'if',
        type=GraphQLNonNull(GraphQLBoolean),
        description='Directs the executor to include this field or fragment only when the `if` argument is true.',
    )],
    on_operation=False,
    on_fragment=True,
    on_field=True
)

GraphQLSkipDirective = GraphQLDirective(
    name='skip',
    args=[arg(
        'if',
        type=GraphQLNonNull(GraphQLBoolean),
        description='Directs the executor to skip this field or fragment only when the `if` argument is true.',
    )],
    on_operation=False,
    on_fragment=True,
    on_field=True
)
