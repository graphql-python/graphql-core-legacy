from ...pyutils.cached_property import cached_property


class Fragment(object):
    def __init__(self, type, field_asts):
        self.type = type
        self.field_asts = field_asts

    @cached_property
    def partial_resolvers(self):
        from .resolver import field_resolver
        resolvers = []
        for field_ast in self.field_asts:
            field_name = field_ast.name.value
            field_def = self.type.fields[field_name]
            resolver = field_resolver(field_def)
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
