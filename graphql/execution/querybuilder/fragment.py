from ...pyutils.cached_property import cached_property


class Fragment(object):
    def __init__(self, type, field_asts):
        self.type = type
        self.field_asts = field_asts

    @cached_property
    def field_resolvers(self):
        from .resolver import field_resolver
        return {
            field_name: field_resolver(self.type.fields[field_name])
            for field_name in self.field_names
        }

    @cached_property
    def field_names(self):
        return map(lambda field_ast: field_ast.name.value, self.field_asts)

    def resolver(self, resolver, *args, **kwargs):
        root = resolver(*args, **kwargs)
        return {
            field_name: self.field_resolvers[field_name](root)
            for field_name in self.field_names
        }