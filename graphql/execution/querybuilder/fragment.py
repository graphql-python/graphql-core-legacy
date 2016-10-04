from functools import partial
from ...pyutils.cached_property import cached_property
from ..values import get_argument_values, get_variable_values
from ..base import collect_fields
from ...pyutils.default_ordered_dict import DefaultOrderedDict


from ...type import GraphQLList, GraphQLNonNull, GraphQLObjectType, GraphQLInterfaceType, GraphQLUnionType


def get_base_type(type):
    if isinstance(type, (GraphQLList, GraphQLNonNull)):
        return get_base_type(type.of_type)
    return type


def get_resolvers(context, type, selection_set):
    from .resolver import field_resolver
    subfield_asts = DefaultOrderedDict(list)
    visited_fragment_names = set()
    if selection_set:
        subfield_asts = collect_fields(
            context, type, selection_set,
            subfield_asts, visited_fragment_names
        )

    resolvers = []
    for response_name, field_asts in subfield_asts.items():
        field_ast = field_asts[0]
        field_name = field_ast.name.value
        field_def = type.fields[field_name]
        field_base_type = get_base_type(field_def.type)
        field_fragment = None
        if isinstance(field_base_type, GraphQLObjectType):
            field_fragment = Fragment(
                type=field_base_type,
                selection_set=field_ast.selection_set,
                context=context
            )
        elif isinstance(field_base_type, (GraphQLInterfaceType, GraphQLUnionType)):
            field_fragment = AbstractFragment(
                abstract_type=field_base_type,
                selection_set=field_ast.selection_set,
                context=context
            )
        resolver = field_resolver(field_def, fragment=field_fragment)
        args = get_argument_values(
            field_def.args,
            field_ast.arguments,
            context and context.variable_values
        )
        resolver = partial(resolver, args=args)
        resolvers.append((response_name, resolver))
    return resolvers


class Fragment(object):
    def __init__(self, type, selection_set, context=None, execute_serially=False):
        self.type = type
        self.selection_set = selection_set
        self.execute_serially = execute_serially
        self.context = context

    @cached_property
    def partial_resolvers(self):
        return get_resolvers(
            self.context,
            self.type,
            self.selection_set
        )

    def resolver(self, resolver, *args, **kwargs):
        root = resolver(*args, **kwargs)
        return {
            field_name: field_resolver(root)
            for field_name, field_resolver in self.partial_resolvers
        }

    def __eq__(self, other):
        return isinstance(other, Fragment) and (
            other.type == self.type and
            other.selection_set == self.selection_set and
            other.context == self.context and
            other.execute_serially == self.execute_serially
        )


class AbstractFragment(object):
    def __init__(self, abstract_type, selection_set, context=None, execute_serially=False):
        self.abstract_type = abstract_type
        self.selection_set = selection_set
        self.context = context
        # self.execute_serially = execute_serially # Technically impossible
        self._type_resolvers = {}

    @cached_property
    def possible_types(self):
        return self.context.schema.get_possible_types(self.abstract_type)

    def get_type_resolvers(self, type):
        if type not in self._type_resolvers:
            assert type in self.possible_types
            self._type_resolvers[type] = get_resolvers(
                self.context,
                type,
                self.selection_set
            )
        return self._type_resolvers[type]

    def resolve_type(self, result):
        return_type = self.abstract_type
        context = self.context.context_value
        info = None

        if return_type.resolve_type:
            runtime_type = return_type.resolve_type(result, context, info)
        else:
            for type in self.possible_types:
                if callable(type.is_type_of) and type.is_type_of(result, context, info):
                    return type

    def resolver(self, resolver, *args, **kwargs):
        root = resolver(*args, **kwargs)
        _type = self.resolve_type(root)

        return {
            field_name: field_resolver(root)
            for field_name, field_resolver in self.get_type_resolvers(_type)
        }
