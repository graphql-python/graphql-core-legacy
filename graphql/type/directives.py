import collections

from .definition import GraphQLArgument, GraphQLNonNull
from .scalars import GraphQLBoolean
from ..utils.assert_valid_name import assert_valid_name


class DirectiveLocation(object):
    QUERY = 'QUERY'
    MUTATION = 'MUTATION'
    SUBSCRIPTION = 'SUBSCRIPTION'
    FIELD = 'FIELD'
    FRAGMENT_DEFINITION = 'FRAGMENT_DEFINITION'
    FRAGMENT_SPREAD = 'FRAGMENT_SPREAD'
    INLINE_FRAGMENT = 'INLINE_FRAGMENT'

    OPERATION_LOCATIONS = [
        QUERY,
        MUTATION,
        SUBSCRIPTION
    ]

    FRAGMENT_LOCATIONS = [
        FRAGMENT_DEFINITION,
        FRAGMENT_SPREAD,
        INLINE_FRAGMENT
    ]

    FIELD_LOCATIONS = [
        FIELD
    ]


class GraphQLDirective(object):
    __slots__ = 'name', 'args', 'description', 'locations'

    def __init__(self, name, description=None, args=None, locations=None):
        assert name, 'Directive must be named.'
        assert_valid_name(name)
        assert isinstance(locations, collections.Iterable), 'Must provide locations for directive.'

        self.name = name
        self.description = description
        self.args = args or []
        self.locations = locations


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
    locations=[
        DirectiveLocation.FIELD,
        DirectiveLocation.FRAGMENT_SPREAD,
        DirectiveLocation.INLINE_FRAGMENT,
    ]
)

GraphQLSkipDirective = GraphQLDirective(
    name='skip',
    args=[arg(
        'if',
        type=GraphQLNonNull(GraphQLBoolean),
        description='Directs the executor to skip this field or fragment only when the `if` argument is true.',
    )],
    locations=[
        DirectiveLocation.FIELD,
        DirectiveLocation.FRAGMENT_SPREAD,
        DirectiveLocation.INLINE_FRAGMENT,
    ]
)
