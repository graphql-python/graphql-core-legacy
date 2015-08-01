import graphql.type

__all__ = ['Schema']


class PublicType(object):
    pass


def build_typeref(refspec):
    if isinstance(refspec, TypeRef):
        # already a TypeRef
        return refspec

    if isinstance(refspec, basestring):
        # type name reference: Field('SomeType')
        return NameTypeRef(refspec)
    try:
        if issubclass(refspec, PublicType):
            # public type reference: Field(SomeType)
            return PublicTypeRef(refspec)
    except TypeError:
        # ignore if refspec is not a class
        pass

    # internal GraphQL type reference: Field(String)
    return InternalTypeRef(refspec)


class TypeRef(object):
    def resolve(self, schema):
        raise NotImplemented


class NameTypeRef(TypeRef):
    def __init__(self, name):
        self.name = name

    def resolve(self, schema):
        return schema._internal_types[self.name]


class WrappingTypeRef(TypeRef):
    def __init__(self, wrapper_type, inner_typeref):
        self.wrapper_type = wrapper_type
        self.inner_typeref = inner_typeref

    def resolve(self, schema):
        return self.wrapper_type(self.inner_typeref.resolve(schema))

    @classmethod
    def factory(cls, wrapper_type):
        def factory_func(inner_typerefspec):
            return cls(wrapper_type, build_typeref(inner_typerefspec))
        return factory_func


class PublicTypeRef(TypeRef):
    def __init__(self, public_type):
        self.public_type = public_type

    def resolve(self, schema):
        return schema._public_types[self.public_type]


class InternalTypeRef(TypeRef):
    def __init__(self, internal_type):
        self.internal_type = internal_type

    def resolve(self, schema):
        return self.internal_type


class LazyField(object):
    def __init__(self, typerefspec, args=None, resolver=None,
                 deprecation_reason=None, description=None):
        self.typeref = build_typeref(typerefspec)
        self.args = args
        self.resolver = resolver
        self.deprecation_reason = deprecation_reason
        self.description = description

    def resolve(self, schema):
        args = {}
        if self.args:
            for arg_name, arg in self.args.items():
                args[arg_name] = arg.resolve(schema)
        return graphql.type.GraphQLField(
            self.typeref.resolve(schema),
            args, self.resolver, self.deprecation_reason, self.description
        )

    def __call__(self, resolver):
        # Called when used as decorator
        self.resolver = resolver
        return self


class LazyArgument(object):
    def __init__(self, typerefspec, default_value=None, description=None):
        self.typeref = build_typeref(typerefspec)
        self.default_value = default_value
        self.description = description

    def resolve(self, schema):
        return graphql.type.GraphQLArgument(
            self.typeref.resolve(schema),
            self.default_value, self.description
        )


class Schema(object):
    String = InternalTypeRef(graphql.type.GraphQLString)
    Int = InternalTypeRef(graphql.type.GraphQLInt)
    Float = InternalTypeRef(graphql.type.GraphQLFloat)
    Boolean = InternalTypeRef(graphql.type.GraphQLBoolean)
    ID = InternalTypeRef(graphql.type.GraphQLID)

    Field = LazyField
    Argument = LazyArgument
    EnumValue = graphql.type.GraphQLEnumValue

    def __init__(self):
        self._internal_types = {}
        self._public_types = {}
        self._query_root = None
        self._mutation_root = None

        # Define in the constructor to make functions unbound
        self.NonNull = WrappingTypeRef.factory(graphql.type.GraphQLNonNull)
        self.List = WrappingTypeRef.factory(graphql.type.GraphQLList)

        self.EnumType = self._build_type_definer(self._define_enum)
        self.InterfaceType = self._build_type_definer(self._define_interface)
        self.UnionType = self._build_type_definer(self._define_union)
        self.ObjectType = self._build_type_definer(self._define_object)
        self.QueryRoot = self._build_type_definer(self._define_query_root)
        self.MutationRoot = self._build_type_definer(self._define_mutation_root)

    def _define_enum(self, dct):
        values = {}
        for k, v in dct.items():
            if isinstance(v, self.EnumValue):
                values[k] = v
        return graphql.type.GraphQLEnumType(
            name=dct['__typename__'],
            values=values,
            description=dct.get('__doc__'),
        )

    def _define_interface(self, dct):
        fields = {}
        for k, v in dct.items():
            if isinstance(v, self.Field):
                fields[k] = v
        return graphql.type.GraphQLInterfaceType(
            name=dct['__typename__'],
            fields=lambda: self._resolve_fields(fields),
            description=dct.get('__doc__'),
        )

    def _define_union(self, dct):
        types = [self._public_types[public_type] for public_type in dct['types']]
        return graphql.type.GraphQLUnionType(
            name=dct['__typename__'],
            types=types,
            resolve_type=dct.get('resolve_type'),
            description=dct.get('__doc__'),
        )

    def _define_object(self, dct):
        fields = {}
        for k, v in dct.items():
            if isinstance(v, self.Field):
                fields[k] = v
        interfaces = dct.get('__interfaces__')
        if interfaces:
            interfaces = [self._public_types[public_type] for public_type in interfaces]
        return graphql.type.GraphQLObjectType(
            name=dct['__typename__'],
            fields=lambda: self._resolve_fields(fields),
            interfaces=interfaces,
            description=dct.get('__doc__'),
        )

    def _define_query_root(self, dct):
        assert not self._query_root
        internal_type = self._define_object(dct)
        self._query_root = internal_type
        return internal_type

    def _define_mutation_root(self, dct):
        assert not self._mutation_root
        internal_type = self._define_object(dct)
        self._mutation_root = internal_type
        return internal_type

    def _resolve_fields(self, fields):
        resolved = {}
        for k, v in fields.items():
            resolved[k] = v.resolve(self)
        return resolved

    def _build_type_definer(self, internal_type_builder):
        class TypeDefinerMeta(type):
            def __init__(cls, name, bases, dct):
                self._define_type(cls, name, bases, dct, internal_type_builder)
                type.__init__(cls, name, bases, dct)

        class TypeDefiner(PublicType):
            __metaclass__ = TypeDefinerMeta

        return TypeDefiner

    def _define_type(self, cls, name, bases, dct, internal_type_builder):
        if not bases or bases[-1] is PublicType:
            return
        if '__typename__' not in dct:
            dct['__typename__'] = name
        assert dct['__typename__'] not in self._internal_types
        internal_type = internal_type_builder(dct)
        self._internal_types[dct['__typename__']] = internal_type
        self._public_types[cls] = internal_type

    def to_internal(self):
        return graphql.type.GraphQLSchema(self._query_root)
