from functools import partial
from ...pyutils.cached_property import cached_property
from ..values import get_argument_values, get_variable_values



class Fragment(object):
    def __init__(self, type, field_asts, field_fragments=None, execute_serially=False):
        self.type = type
        self.field_asts = field_asts
        self.field_fragments = field_fragments or {}
        self.variable_values = {}

    @cached_property
    def partial_resolvers(self):
        from .resolver import field_resolver
        resolvers = []
        for field_ast in self.field_asts:
            field_name = field_ast.name.value
            field_def = self.type.fields[field_name]
            field_fragment = self.field_fragments.get(field_name)
            resolver = field_resolver(field_def, fragment=field_fragment)
            args = get_argument_values(
                field_def.args,
                field_ast.arguments,
                self.variable_values
            )
            resolver = partial(resolver, args=args)
            resolvers.append((field_name, resolver))
        return resolvers

    def resolver(self, resolver, *args, **kwargs):
        root = resolver(*args, **kwargs)
        return {
            field_name: field_resolver(root)
            for field_name, field_resolver in self.partial_resolvers
        }

    def __eq__(self, other):
        return isinstance(other, Fragment) and (
            other.type == self.type and
            other.field_asts == self.field_asts
        )
