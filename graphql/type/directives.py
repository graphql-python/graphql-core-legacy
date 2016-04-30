import collections

from ..utils.assert_valid_name import assert_valid_name
from .definition import GraphQLArgument, GraphQLNonNull, is_input_type
from .scalars import GraphQLBoolean


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
        self.locations = locations

        self.args = []
        if args:
            assert isinstance(args, dict), '{} args must be a dict with argument names as keys.'.format(name)
            for arg_name, _arg in args.items():
                assert_valid_name(arg_name)
                assert is_input_type(_arg.type), '{}({}) argument type must be Input Type but got {}.'.format(
                    name,
                    arg_name,
                    _arg.type)
                self.args.append(arg(
                    arg_name,
                    description=_arg.description,
                    type=_arg.type,
                    default_value=_arg.default_value
                ))


def arg(name, *args, **kwargs):
    a = GraphQLArgument(*args, **kwargs)
    a.name = name
    return a


GraphQLIncludeDirective = GraphQLDirective(
    name='include',
    args={
        'if': GraphQLArgument(
            type=GraphQLNonNull(GraphQLBoolean),
            description='Included when true.',
        ),
    },
    locations=[
        DirectiveLocation.FIELD,
        DirectiveLocation.FRAGMENT_SPREAD,
        DirectiveLocation.INLINE_FRAGMENT,
    ]
)

GraphQLSkipDirective = GraphQLDirective(
    name='skip',
    args={
        'if': GraphQLArgument(
            type=GraphQLNonNull(GraphQLBoolean),
            description='Skipped when true.',
        ),
    },
    locations=[
        DirectiveLocation.FIELD,
        DirectiveLocation.FRAGMENT_SPREAD,
        DirectiveLocation.INLINE_FRAGMENT,
    ]
)
