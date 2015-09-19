import collections
from ..error import Error
from ..language import ast


def is_input_type(type):
    named_type = get_named_type(type)
    return isinstance(named_type, (
        GraphQLScalarType,
        GraphQLEnumType,
        GraphQLInputObjectType,
    ))


def is_composite_type(type):
    named_type = get_named_type(type)
    return isinstance(named_type, (
        GraphQLObjectType,
        GraphQLInterfaceType,
        GraphQLUnionType,
    ))


def is_leaf_type(type):
    named_type = get_named_type(type)
    return isinstance(named_type, (
        GraphQLScalarType,
        GraphQLEnumType,
    ))


def get_named_type(type):
    unmodified_type = type
    while isinstance(unmodified_type, (GraphQLList, GraphQLNonNull)):
        unmodified_type = unmodified_type.of_type
    return unmodified_type


def get_nullable_type(type):
    if isinstance(type, GraphQLNonNull):
        return type.of_type
    return type


class GraphQLType(object):
    def __str__(self):
        return self.name


class GraphQLScalarType(GraphQLType):
    """Scalar Type Definition

    The leaf values of any request and input values to arguments are
    Scalars (or Enums) and are defined with a name and a series of coercion
    functions used to ensure validity.

    Example:

        def coerce_odd(value):
            if value % 2 == 1:
                return value
            return None

        OddType = GraphQLScalarType(name='Odd', serialize=coerce_odd)
    """
    def __init__(self, name, description=None, serialize=None, parse_value=None, parse_literal=None):
        assert name, 'Type must be named.'
        self.name = name
        self.description = description
        assert callable(serialize)
        if parse_value or parse_literal:
            assert callable(parse_value) and callable(parse_literal)
        self._serialize = serialize
        self._parse_value = parse_value
        self._parse_literal = parse_literal

    def serialize(self, value):
        return self._serialize(value)

    def parse_value(self, value):
        if self._parse_value:
            return self._parse_value(value)
        return None

    def parse_literal(self, value_ast):
        if self._parse_literal:
            return self._parse_literal(value_ast)
        return None

    def __str__(self):
        return self.name


class GraphQLObjectType(GraphQLType):
    """Object Type Definition

    Almost all of the GraphQL types you define will be object types.
    Object types have a name, but most importantly describe their fields.

    Example:

        AddressType = GraphQLObjectType('Address', {
            'street': GraphQLField(GraphQLString),
            'number': GraphQLField(GraphQLInt),
            'formatted': GraphQLField(GraphQLString,
                resolver=lambda obj, *_: obj.number + ' ' + obj.street),
        })

    When two types need to refer to each other, or a type needs to refer to
    itself in a field, you can use a static method to supply the fields
    lazily.

    Example:

        PersonType = GraphQLObjectType('Person', lambda: {
            'name': GraphQLField(GraphQLString),
            'bestFriend': GraphQLField(PersonType)
        })
    """
    def __init__(self, name, fields, interfaces=None, is_type_of=None, description=None):
        assert name, 'Type must be named.'
        self.name = name
        self.description = description
        self._fields = fields
        self._field_map = None
        self._interfaces = interfaces or []
        self._is_type_of = is_type_of
        add_impl_to_interfaces(self)

    def get_fields(self):
        if self._field_map is None:
            self._field_map = define_field_map(self._fields)
        return self._field_map

    def get_interfaces(self):
        return self._interfaces

    def is_type_of(self, value):
        if self._is_type_of:
            return self._is_type_of(value)


def define_field_map(fields):
    if callable(fields):
        fields = fields()
    for field_name, field in fields.items():
        field.name = field_name
    return fields


def add_impl_to_interfaces(impl):
    for type in impl.get_interfaces():
        type._impls.append(impl)


class GraphQLField(object):
    def __init__(self, type, args=None, resolver=None,
                 deprecation_reason=None, description=None):
        self.type = type
        self.args = []
        if args:
            for arg_name, arg in args.items():
                arg.name = arg_name
                self.args.append(arg)
        self.resolver = resolver
        self.deprecation_reason = deprecation_reason
        self.description = description


class GraphQLArgument(object):
    def __init__(self, type, default_value=None, description=None):
        self.type = type
        self.default_value = default_value
        self.description = description


class GraphQLInterfaceType(GraphQLType):
    """Interface Type Definition

    When a field can return one of a heterogeneous set of types, a Interface type is used to describe what types are possible,
    what fields are in common across all types, as well as a function to determine which type is actually used when the field is resolved.

    Example:

        EntityType = GraphQLInterfaceType(
            name='Entity',
            fields={
                'name': GraphQLField(GraphQLString),
            })
    """

    def __init__(self, name, fields=None, resolve_type=None, description=None):
        assert name, 'Type must be named.'
        self.name = name
        self.description = description
        self._fields = fields or {}
        self._resolver = resolve_type

        self._impls = []
        self._field_map = None
        self._possible_type_names = None

    def get_fields(self):
        if self._field_map is None:
            self._field_map = define_field_map(self._fields)
        return self._field_map

    def get_possible_types(self):
        return self._impls

    def is_possible_type(self, type):
        if self._possible_type_names is None:
            self._possible_type_names = set(
                t.name for t in self.get_possible_types()
            )
        return type.name in self._possible_type_names

    def resolve_type(self, value):
        if self._resolver:
            return self._resolver(value)
        return get_type_of(value, self)


def get_type_of(value, abstract_type):
    possible_types = abstract_type.get_possible_types()
    for type in possible_types:
        is_type_of = type.is_type_of(value)
        if is_type_of is None:
            raise Error(
                'Non-Object Type {} does not implement resolve_type and '
                'Object Type {} does not implement is_type_of. '
                'There is no way to determine if a value is of this type.'
                .format(abstract_type.name, type.name)
            )
        if is_type_of:
            return type


class GraphQLUnionType(GraphQLType):
    """Union Type Definition

    When a field can return one of a heterogeneous set of types, a Union type is used to describe what types are possible
    as well as providing a function to determine which type is actually used when the field is resolved.

    Example:

        class PetType(GraphQLUnionType):
            name = 'Pet'
            types = [DogType, CatType]

            def resolve_type(self, value):
                if isinstance(value, Dog):
                    return DogType()
                if isinstance(value, Cat):
                    return CatType()
    """
    def __init__(self, name, types=None, resolve_type=None, description=None):
        assert name, 'Type must be named.'
        self.name = name
        self.description = description
        assert types, \
            'Must provide types for Union {}.'.format(name)
        self._possible_type_names = None
        non_obj_types = [t for t in types
                         if not isinstance(t, GraphQLObjectType)]
        if non_obj_types:
            raise Error(
                'Union {} may only contain object types, it cannot '
                'contain: {}.'.format(
                    self.name,
                    ', '.join(str(t) for t in non_obj_types)
                )
            )
        self._types = types
        self._resolve_type = resolve_type

    def get_possible_types(self):
        return self._types

    def is_possible_type(self, type):
        if self._possible_type_names is None:
            self._possible_type_names = set(
                t.name for t in self.get_possible_types()
            )
        return type.name in self._possible_type_names

    def resolve_type(self, value):
        if self._resolve_type:
            return self._resolve_type(value)
        return get_type_of(value, self)


class GraphQLEnumType(GraphQLType):
    """Enum Type Definition

    Some leaf values of requests and input values are Enums. GraphQL serializes Enum values as strings,
    however internally Enums can be represented by any kind of type, often integers.

    Example:

        RGBType = GraphQLEnumType('RGB', {
            'RED': 0,
            'GREEN': 1,
            'BLUE': 2,
        })

    Note: If a value is not provided in a definition, the name of the enum value will be used as it's internal value.
    """
    def __init__(self, name, values, description=None):
        self.name = name
        self.description = description
        self._values = values
        self._value_map = None
        self._value_lookup = None
        self._name_lookup = None

    def get_values(self):
        if self._value_map is None:
            self._value_map = self._define_value_map()
        return self._value_map

    def serialize(self, value):
        if isinstance(value, collections.Hashable):
            enum_value = self._get_value_lookup().get(value)
            if enum_value:
                return enum_value.name
        return None

    def parse_value(self, value):
        if isinstance(value, collections.Hashable):
            enum_value = self._get_value_lookup().get(value)
            if enum_value:
                return enum_value.name
        return None

    def parse_literal(self, value_ast):
        if isinstance(value_ast, ast.EnumValue):
            enum_value = self._get_name_lookup().get(value_ast.value)
            if enum_value:
                return enum_value.value

    def _define_value_map(self):
        value_map = {}
        for value_name, value in self._values.items():
            if not isinstance(value, GraphQLEnumValue):
                value = GraphQLEnumValue(value)
            value.name = value_name
            if value.value is None:
                value.value = value_name
            value_map[value_name] = value
        return value_map

    def _get_value_lookup(self):
        if self._value_lookup is None:
            lookup = {}
            for value_name, value in self.get_values().items():
                lookup[value.value] = value
            self._value_lookup = lookup
        return self._value_lookup

    def _get_name_lookup(self):
        if self._name_lookup is None:
            lookup = {}
            for value_name, value in self.get_values().items():
                lookup[value.name] = value
            self._name_lookup = lookup
        return self._name_lookup


class GraphQLEnumValue(object):
    def __init__(self, value=None, deprecation_reason=None,
                 description=None):
        self.value = value
        self.deprecation_reason = deprecation_reason
        self.description = description


class GraphQLInputObjectType(GraphQLType):
    """Input Object Type Definition

    An input object defines a structured collection of fields which may be
    supplied to a field argument.

    Using `NonNull` will ensure that a value must be provided by the query

    Example:

        NonNullFloat = GraphQLNonNull(GraphQLFloat())

        class GeoPoint(GraphQLInputObjectType):
            name = 'GeoPoint'
            fields = {
                'lat': GraphQLInputObjectField(NonNullFloat),
                'lon': GraphQLInputObjectField(NonNullFloat),
                'alt': GraphQLInputObjectField(GraphQLFloat(),
                    default_value=0)
            }
    """
    def __init__(self, name, fields, description=None):
        assert name, 'Type must be named.'
        self.name = name
        self.description = description
        self._fields = fields
        self._field_map = None

    def get_fields(self):
        if self._field_map is None:
            self._field_map = define_field_map(self._fields)
        return self._field_map


class GraphQLInputObjectField(object):
    def __init__(self, type, default_value=None, description=None):
        self.type = type
        self.default_value = default_value
        self.description = description


class GraphQLList(GraphQLType):
    """List Modifier

    A list is a kind of type marker, a wrapping type which points to another
    type. Lists are often created within the context of defining the fields
    of an object type.

    Example:

        class PersonType(GraphQLObjectType):
            name = 'Person'

            def get_fields(self):
                return {
                    'parents': GraphQLField(GraphQLList(PersonType())),
                    'children': GraphQLField(GraphQLList(PersonType())),
                }
    """
    def __init__(self, type):
        self.of_type = type

    def __str__(self):
        return '[' + str(self.of_type) + ']'


class GraphQLNonNull(GraphQLType):
    """Non-Null Modifier

    A non-null is a kind of type marker, a wrapping type which points to another type. Non-null types enforce that their values are never null
    and can ensure an error is raised if this ever occurs during a request. It is useful for fields which you can make a strong guarantee on
    non-nullability, for example usually the id field of a database row will never be null.

    Example:

        class RowType(GraphQLObjectType):
            name = 'Row'
            fields = {
                'id': GraphQLField(type=GraphQLNonNull(GraphQLString()))
            }

    Note: the enforcement of non-nullability occurs within the executor.
    """
    def __init__(self, type):
        assert not isinstance(type, GraphQLNonNull), \
            'Cannot nest NonNull inside NonNull.'
        self.of_type = type

    def __str__(self):
        return str(self.of_type) + '!'
