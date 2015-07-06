from graphql.error import Error
from graphql.language.kinds import ENUM

'''
/**
 * These are all of the possible kinds of types.
 */
export type GraphQLType =
  GraphQLScalarType |
  GraphQLObjectType |
  GraphQLInterfaceType |
  GraphQLUnionType |
  GraphQLEnumType |
  GraphQLInputObjectType |
  GraphQLList |
  GraphQLNonNull;

// Predicates

/**
 * These types may be used as input types for arguments and directives.
 */
export type GraphQLInputType =
  GraphQLScalarType |
  GraphQLEnumType |
  GraphQLInputObjectType |
  GraphQLList |
  GraphQLNonNull;

export function isInputType(type: ?GraphQLType): boolean {
  var nakedType = getUnmodifiedType(type);
  return (
    nakedType instanceof GraphQLScalarType ||
    nakedType instanceof GraphQLEnumType ||
    nakedType instanceof GraphQLInputObjectType
  );
}

/**
 * These types may be used as output types as the result of fields.
 */
export type GraphQLOutputType =
  GraphQLScalarType |
  GraphQLObjectType |
  GraphQLInterfaceType |
  GraphQLUnionType |
  GraphQLEnumType |
  GraphQLList |
  GraphQLNonNull;

export function isOutputType(type: ?GraphQLType): boolean {
  var nakedType = getUnmodifiedType(type);
  return (
    nakedType instanceof GraphQLScalarType ||
    nakedType instanceof GraphQLObjectType ||
    nakedType instanceof GraphQLInterfaceType ||
    nakedType instanceof GraphQLUnionType ||
    nakedType instanceof GraphQLEnumType
  );
}

/**
 * These types may describe types which may be leaf values.
 */
export type GraphQLLeafType =
  GraphQLScalarType |
  GraphQLEnumType;

export function isLeafType(type: ?GraphQLType): boolean {
  var nakedType = getUnmodifiedType(type);
  return (
    nakedType instanceof GraphQLScalarType ||
    nakedType instanceof GraphQLEnumType
  );
}

/**
 * These types may describe the parent context of a selection set.
 */
export type GraphQLCompositeType =
  GraphQLObjectType |
  GraphQLInterfaceType |
  GraphQLUnionType;

export function isCompositeType(type: ?GraphQLType): boolean {
  return (
    type instanceof GraphQLObjectType ||
    type instanceof GraphQLInterfaceType ||
    type instanceof GraphQLUnionType
  );
}

/**
 * These types may describe the parent context of a selection set.
 */
export type GraphQLAbstractType =
  GraphQLInterfaceType |
  GraphQLUnionType;

export function isAbstractType(type: ?GraphQLType): boolean {
  return (
    type instanceof GraphQLInterfaceType ||
    type instanceof GraphQLUnionType
  );
}

/**
 * These types can all accept null as a value.
 */
export type GraphQLNullableType =
  GraphQLScalarType |
  GraphQLObjectType |
  GraphQLInterfaceType |
  GraphQLUnionType |
  GraphQLEnumType |
  GraphQLInputObjectType |
  GraphQLList;

export function getNullableType(type: ?GraphQLType): ?GraphQLNullableType {
  return type instanceof GraphQLNonNull ? type.ofType : type;
}

/**
 * These types have no modifiers like List or NonNull.
 */
export type GraphQLUnmodifiedType =
  GraphQLScalarType |
  GraphQLObjectType |
  GraphQLInterfaceType |
  GraphQLUnionType |
  GraphQLEnumType |
  GraphQLInputObjectType;

export function getUnmodifiedType(type: ?GraphQLType): ?GraphQLUnmodifiedType {
  var unmodifiedType = type;
  while (
    unmodifiedType instanceof GraphQLList ||
    unmodifiedType instanceof GraphQLNonNull
  ) {
    unmodifiedType = unmodifiedType.ofType;
  }
  return unmodifiedType;
}
'''

class GraphQLType(object):
    pass


class GraphQLScalarType(GraphQLType):
    """Scalar Type Definition

    The leaf values of any request and input values to arguments are
    Scalars (or Enums) and are defined with a name and a series of coercion
    functions used to ensure validity.

    Example:

        class OddType(GraphQLScalarType):
            name = 'Odd'

            def coerce(self, value):
                if value % 2 == 1:
                    return value
                return None
    """
    def coerce(self, value):
        raise NotImplemented

    def coerce_literal(self, value):
        return None

    def __str__(self):
        return self.name


class GraphQLObjectType(GraphQLType):
    """Object Type Definition

    Almost all of the GraphQL types you define will be object types.
    Object types have a name, but most importantly describe their fields.

    Example:

        class AddressType(GraphQLObjectType):
            name = 'Address'

        var AddressType = new GraphQLObjectType({
          name: 'Address',
          fields: {
            street: { type: GraphQLString },
            number: { type: GraphQLInt },
            formatted: {
              type: GraphQLString,
              resolve(obj) {
                return obj.number + ' ' + obj.street
              }
            }
          }
        });

    When two types need to refer to each other, or a type needs to refer to
    itself in a field, you can use a function expression (aka a closure or a
    thunk) to supply the fields lazily.

    Example:

        var PersonType = new GraphQLObjectType({
          name: 'Person',
          fields: () => ({
            name: { type: GraphQLString },
            bestFriend: { type: PersonType },
          })
        });
    """
    def __init__(self):
        self._add_impls_to_ifaces()

    def get_fields(self):
        return self.fields

    def get_interfaces(self):
        return []

    def is_type_of(self, value):
        return False

    def _add_impls_to_ifaces(self):
        for type in self.get_interfaces():
            type._impls.append(self)


class GraphQLField(object):
    def __init__(self, type, args=None, resolver=None,
        deprecation_reason=None, description=None):
        self.type = type
        self.args = []
        if args:
            for arg_name, arg in args.items():
                self.args.append({
                    'name': arg_name,
                    'type': arg.type,
                    'default_value': arg.default_value,
                })
        self.resolver = resolver
        self.deprecation_reason = deprecation_reason
        self.description = description


class GraphQLArgument(object):
    def __init__(self, type, default_value=None):
        self.type = type
        self.default_value = default_value


class _InterfaceTypeMeta(type):
    def __init__(cls, name, bases, dct):
        super(_InterfaceTypeMeta, cls).__init__(name, bases, dct)
        cls._impls = []


class GraphQLInterfaceType(GraphQLType):
    """Interface Type Definition

    When a field can return one of a heterogeneous set of types, a Interface type is used to describe what types are possible, what fields are in common across all types, as well as a function to determine which type is actually used when the field is resolved.

    Example:

        class EntityType(GraphQLInterfaceType):
            name = 'Entity'
            fields = {
                'name': GraphQLField(GraphQLString()),
            }
    """
    __metaclass__ = _InterfaceTypeMeta

    def __init__(self):
        self._possible_type_names = None

    def get_fields(self):
        return self.fields

    def get_possible_types(self):
        return self._impls

    def is_possible_type(self, type):
        if self._possible_type_names is None:
            self._possible_type_names = set(
                t.name for t in self.get_possible_types()
            )
        return type.name in self._possible_type_names

    def resolve_type(value):
        return get_type_of(value, self)


def get_type_of(value, abstract_type):
    possible_types = abstract_type.get_possible_types()
    for type in possible_types:
        if not type.is_type_of(value):
            raise Error(
                'Non-Object Type {} does not implement resolve_type and ' \
                'Object Type {} does not implement is_type_of. ' \
                'There is no way to determine if a value is of this type.'
                .format(abstract_type.name, type.name)
            )
        return type


class GraphQLUnionType(GraphQLType):
    """Union Type Definition

    When a field can return one of a heterogeneous set of types, a Union type is used to describe what types are possible as well as providing a function to determine which type is actually used when the field is resolved.

    Example:

        class PetType(GraphQLUnionType):
            name = 'Pet'
            types = [DogType(), CatType()]

            def resolve_type(self, value):
                if isinstance(value, Dog):
                    return DogType()
                if isinstance(value, Cat):
                    return CatType()
    """
    def __init__(self):
        assert self.name, 'Type must be named.'
        assert self.types, \
            'Must provide types for Union {}.'.format(self.name)
        non_obj_types = [t for t in self.types
            if not instanceof(t, GraphQLObjectType)]
        if non_obj_types:
            raise Error(
                'Union {} may only contain object types, it cannot ' \
                'contain: {}.'.format(
                    self.name,
                    ', '.join(t.name for t in non_obj_types)
                )
            )

    def get_possible_types(self):
        return self.types

    def is_possible_type(self, type):
        if self._possible_type_names is None:
            self._possible_type_names = set(
                t.name for t in self.get_possible_types()
            )
        return type.name in self._possible_type_names

    def resolve_type(value):
        return get_type_of(value, self)
        


class GraphQLEnumType(GraphQLType):
    """Enum Type Definition

    Some leaf values of requests and input values are Enums. GraphQL serializes Enum values as strings, however internally Enums can be represented by any kind of type, often integers.

    Example:

        class RGBType(GraphQLEnumType):
            name = 'RGB'
            values = {
                'RED': GraphQLEnumValue(0),
                'GREEN': GraphQLEnumValue(1),
                'BLUE': GraphQLEnumValue(2),
            }

    Note: If a value is not provided in a definition, the name of the enum value will be used as it's internal value.
    """
    def __init__(self):
        self._values = None
        self._value_lookup = None
        self._namee_lookup = None

    def get_values(self):
        if self._values is None:
            self._values = self._define_value_map()
        return self._values

    def coerce(self, value):
        enum_value = self._get_value_lookup().get(value)
        if enum_value:
            return enum_value.name
        return None

    def coerce_literal(self, value):
        if value.kind == ENUM:
            enum_value = self._get_name_lookup().get(value.value)
            if enum_value:
                return enum_value.value

    def _define_value_map(self):
        for value_name, value in self.values.items():
            value.name = value_name
            if value.value is None:
                value.value = value_name
        return self.values

    def _get_value_lookup(self):
        if self._value_lookup is None:
            lookup = {}
            for value_name, value in self.get_values():
                lookup[value.value] = value
            self._value_lookup = lookup
        return self._value_lookup

    def _get_name_lookup(self):
        if self._name_lookup is None:
            lookup = {}
            for value_name, value in self.get_values():
                lookup[value.name] = value
            self._name_lookup = lookup
        return self._name_lookup


class GraphQLEnumValue(object):
    def __init__(self, value=None, deprecation_reason=None,
        description=None):
        self.value = value
        self.deprecation_reason = depreaction_reason
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
    def __init__(self):
        assert self.name, 'Type must be named.'

    def get_fields(self):
        return self.fields


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


class GraphQLNonNull(GraphQLType):
    """Non-Null Modifier

    A non-null is a kind of type marker, a wrapping type which points to another type. Non-null types enforce that their values are never null and can ensure an error is raised if this ever occurs during a request. It is useful for fields which you can make a strong guarantee on non-nullability, for example usually the id field of a database row will never be null.

    Example:

        class RowType(GraphQLObjectType):
            name = 'Row'
            fields = {
                'id': GraphQLField(type=GraphQLNonNull(GraphQLString()))
            }

    Note: the enforcement of non-nullability occurs within the executor.
    """
    def __init__(self, type):
        self.of_type = type
