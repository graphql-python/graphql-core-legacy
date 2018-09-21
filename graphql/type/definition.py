from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    NamedTuple,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)
from collections import namedtuple

from ..error import GraphQLError, INVALID, InvalidType
from ..language import (
    EnumTypeDefinitionNode,
    EnumValueDefinitionNode,
    EnumTypeExtensionNode,
    EnumValueNode,
    FieldDefinitionNode,
    FieldNode,
    FragmentDefinitionNode,
    InputObjectTypeDefinitionNode,
    InputObjectTypeExtensionNode,
    InputValueDefinitionNode,
    InterfaceTypeDefinitionNode,
    InterfaceTypeExtensionNode,
    ObjectTypeDefinitionNode,
    ObjectTypeExtensionNode,
    OperationDefinitionNode,
    ScalarTypeDefinitionNode,
    ScalarTypeExtensionNode,
    TypeDefinitionNode,
    TypeExtensionNode,
    UnionTypeDefinitionNode,
    UnionTypeExtensionNode,
    ValueNode,
)
from ..pyutils import MaybeAwaitable, cached_property
from ..utilities.value_from_ast_untyped import value_from_ast_untyped

if TYPE_CHECKING:  # pragma: no cover
    from .schema import GraphQLSchema  # noqa: F401

__all__ = [
    "is_type",
    "is_scalar_type",
    "is_object_type",
    "is_interface_type",
    "is_union_type",
    "is_enum_type",
    "is_input_object_type",
    "is_list_type",
    "is_non_null_type",
    "is_input_type",
    "is_output_type",
    "is_leaf_type",
    "is_composite_type",
    "is_abstract_type",
    "is_wrapping_type",
    "is_nullable_type",
    "is_named_type",
    "is_required_argument",
    "is_required_input_field",
    "assert_type",
    "assert_scalar_type",
    "assert_object_type",
    "assert_interface_type",
    "assert_union_type",
    "assert_enum_type",
    "assert_input_object_type",
    "assert_list_type",
    "assert_non_null_type",
    "assert_input_type",
    "assert_output_type",
    "assert_leaf_type",
    "assert_composite_type",
    "assert_abstract_type",
    "assert_wrapping_type",
    "assert_nullable_type",
    "assert_named_type",
    "get_nullable_type",
    "get_named_type",
    "GraphQLAbstractType",
    "GraphQLArgument",
    "GraphQLArgumentMap",
    "GraphQLCompositeType",
    "GraphQLEnumType",
    "GraphQLEnumValue",
    "GraphQLEnumValueMap",
    "GraphQLField",
    "GraphQLFieldMap",
    "GraphQLFieldResolver",
    "GraphQLInputField",
    "GraphQLInputFieldMap",
    "GraphQLInputObjectType",
    "GraphQLInputType",
    "GraphQLIsTypeOfFn",
    "GraphQLLeafType",
    "GraphQLList",
    "GraphQLNamedType",
    "GraphQLNullableType",
    "GraphQLNonNull",
    "GraphQLResolveInfo",
    "GraphQLScalarType",
    "GraphQLScalarSerializer",
    "GraphQLScalarValueParser",
    "GraphQLScalarLiteralParser",
    "GraphQLObjectType",
    "GraphQLOutputType",
    "GraphQLInterfaceType",
    "GraphQLType",
    "GraphQLTypeResolver",
    "GraphQLUnionType",
    "GraphQLWrappingType",
    "ResponsePath",
    "Thunk",
]


class GraphQLType(object):
    """Base class for all GraphQL types"""

    # Note: We don't use slots for GraphQLType objects because memory
    # considerations are not really important for the schema definition
    # and it would make caching properties slower or more complicated.


# There are predicates for each kind of GraphQL type.


def is_type(type_):
    # type: (Any) -> bool
    return isinstance(type_, GraphQLType)


def assert_type(type_):
    # type: (Any) -> GraphQLType
    if not is_type(type_):
        raise TypeError("Expected {} to be a GraphQL type.".format(type_))
    return type_


# These types wrap and modify other types

GT = TypeVar("GT", bound=GraphQLType)


class GraphQLWrappingType(GraphQLType, Generic[GT]):
    """Base class for all GraphQL wrapping types"""

    # of_type: GT

    def __init__(self, type_):
        # type: (GT) -> None
        if not is_type(type_):
            raise TypeError(
                "Can only create a wrapper for a GraphQLType, but got:"
                " {}.".format(type_)
            )
        self.of_type = type_


def is_wrapping_type(type_):
    # type: (Any) -> bool
    return isinstance(type_, GraphQLWrappingType)


def assert_wrapping_type(type_):
    # type: (Any) -> GraphQLWrappingType
    if not is_wrapping_type(type_):
        raise TypeError("Expected {} to be a GraphQL wrapping type.".format(type_))
    return type_


# These named types do not include modifiers like List or NonNull.


class GraphQLNamedType(GraphQLType):
    """Base class for all GraphQL named types"""

    def __init__(
        self,
        name,  # type: str
        description=None,  # type: Optional[str]
        ast_node=None,  # type: Optional[TypeDefinitionNode]
        extension_ast_nodes=None,  # type: Optional[Sequence[TypeExtensionNode]]
    ):
        if not name:
            raise TypeError("Must provide name.")
        if not isinstance(name, str):
            raise TypeError("The name must be a string.")
        if description is not None and not isinstance(description, str):
            raise TypeError("The description must be a string.")
        if ast_node and not isinstance(ast_node, TypeDefinitionNode):
            raise TypeError("{} AST node must be a TypeDefinitionNode.".format(name))
        if extension_ast_nodes:
            if isinstance(extension_ast_nodes, list):
                extension_ast_nodes = tuple(extension_ast_nodes)
            if not isinstance(extension_ast_nodes, tuple):
                raise TypeError(
                    "{} extension AST nodes must be a list/tuple.".format(name)
                )
            if not all(
                isinstance(node, TypeExtensionNode) for node in extension_ast_nodes
            ):
                raise TypeError(
                    "{} extension AST nodes must be TypeExtensionNode.".format(name)
                )
        self.name = name
        self.description = description
        self.ast_node = ast_node
        self.extension_ast_nodes = extension_ast_nodes  # type: ignore

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<{}({})>".format(self.__class__.__name__, self)


def is_named_type(type_):
    # type: (Any) -> bool
    return isinstance(type_, GraphQLNamedType)


def assert_named_type(type_):
    # type: (Any) -> GraphQLNamedType
    if not is_named_type(type_):
        raise TypeError("Expected {} to be a GraphQL named type.".format(type_))
    return type_


def get_named_type(type_):  # noqa: F811
    # type: (Optional[GraphQLType]) -> Optional[GraphQLNamedType]
    """Unwrap possible wrapping type"""
    if type_:
        unwrapped_type = type_
        while is_wrapping_type(unwrapped_type):
            unwrapped_type = unwrapped_type
            unwrapped_type = unwrapped_type.of_type
        return unwrapped_type
    return None


def resolve_thunk(thunk):
    # type: (Any) -> Any
    """Resolve the given thunk.

    Used while defining GraphQL types to allow for circular references in
    otherwise immutable type definitions.
    """
    return thunk() if callable(thunk) else thunk


def default_value_parser(value):
    # type: (Any) -> Any
    return value


# Unfortunately these types cannot be specified any better in Python:
GraphQLScalarSerializer = Callable
GraphQLScalarValueParser = Callable
GraphQLScalarLiteralParser = Callable


class GraphQLScalarType(GraphQLNamedType):
    """Scalar Type Definition

    The leaf values of any request and input values to arguments are
    Scalars (or Enums) and are defined with a name and a series of functions
    used to parse input from ast or variables and to ensure validity.

    If a type's serialize function does not return a value (i.e. it returns
    `None`), then no error will be included in the response.

    Example:

        def serialize_odd(value):
            if value % 2 == 1:
                return value

        odd_type = GraphQLScalarType('Odd', serialize=serialize_odd)

    """

    # Serializes an internal value to include in a response.
    # serialize: GraphQLScalarSerializer

    #  Parses an externally provided value to use as an input.
    # parseValue: GraphQLScalarValueParser
    # Parses an externally provided literal value to use as an input.

    # Takes a dictionary of variables as an optional second argument.
    # parseLiteral: GraphQLScalarLiteralParser

    # ast_node: Optional[ScalarTypeDefinitionNode]
    # extension_ast_nodes: Optional[Tuple[ScalarTypeExtensionNode]]

    def __init__(
        self,
        name,  # type: str
        serialize,  # type: GraphQLScalarSerializer,
        description=None,  # type: Optional[str]
        parse_value=None,  # type: GraphQLScalarValueParser
        parse_literal=None,  # type: GraphQLScalarLiteralParser
        ast_node=None,  # type: Optional[ScalarTypeDefinitionNode]
        extension_ast_nodes=None,  # type: Optional[Sequence[ScalarTypeExtensionNode]]
    ):
        # type: (...) -> None
        super(GraphQLScalarType, self).__init__(
            name=name,
            description=description,
            ast_node=ast_node,
            extension_ast_nodes=extension_ast_nodes,
        )
        if not callable(serialize):
            raise TypeError(
                (
                    "{} must provide 'serialize' function."
                    " If this custom Scalar is also used as an input type,"
                    " ensure 'parse_value' and 'parse_literal' functions"
                    " are also provided."
                ).format(name)
            )
        if parse_value is not None or parse_literal is not None:
            if not callable(parse_value) or not callable(parse_literal):
                raise TypeError(
                    (
                        "{} must provide"
                        " both 'parse_value' and 'parse_literal' functions."
                    ).format(name)
                )
        if ast_node and not isinstance(ast_node, ScalarTypeDefinitionNode):
            raise TypeError(
                "{} AST node must be a ScalarTypeDefinitionNode.".format(name)
            )
        if extension_ast_nodes and not all(
            isinstance(node, ScalarTypeExtensionNode) for node in extension_ast_nodes
        ):
            raise TypeError(
                ("{} extension AST nodes" " must be ScalarTypeExtensionNode.").format(
                    name
                )
            )
        self.serialize = serialize  # type: ignore
        self.parse_value = parse_value or default_value_parser
        self.parse_literal = parse_literal or value_from_ast_untyped


def is_scalar_type(type_):
    # type: (Any) -> bool
    return isinstance(type_, GraphQLScalarType)


def assert_scalar_type(type_):
    # type: (Any) -> GraphQLScalarType
    if not is_scalar_type(type_):
        raise TypeError("Expected {} to be a GraphQL Scalar type.".format(type_))
    return type_


# if False:
GraphQLArgumentMap = Dict[str, "GraphQLArgument"]


class GraphQLField:
    """Definition of a GraphQL field"""

    # type: "GraphQLOutputType"
    # args: Dict[str, "GraphQLArgument"]
    # resolve: Optional["GraphQLFieldResolver"]
    # subscribe: Optional["GraphQLFieldResolver"]
    # description: Optional[str]
    # deprecation_reason: Optional[str]
    # ast_node: Optional[FieldDefinitionNode]

    def __init__(
        self,
        type_,  # type: GraphQLOutputType,
        args=None,  # type: GraphQLArgumentMap
        resolve=None,  # type: GraphQLFieldResolver,
        subscribe=None,  # type: GraphQLFieldResolver
        description=None,  # type: Optional[str]
        deprecation_reason=None,  # type: Optional[str]
        ast_node=None,  # type: FieldDefinitionNode
    ):
        if not is_output_type(type_):
            raise TypeError("Field type must be an output type.")
        if args is None:
            args = {}
        elif not isinstance(args, dict):
            raise TypeError("Field args must be a dict with argument names as keys.")
        elif not all(
            isinstance(value, GraphQLArgument) or is_input_type(value)
            for value in args.values()
        ):
            raise TypeError("Field args must be GraphQLArgument or input type objects.")
        else:
            args = {
                name: value
                if isinstance(value, GraphQLArgument)
                else GraphQLArgument(value)
                for name, value in args.items()
            }
        if resolve is not None and not callable(resolve):
            raise TypeError(
                "Field resolver must be a function if provided, "
                " but got: {!r}.".format(resolve)
            )
        if description is not None and not isinstance(description, str):
            raise TypeError("The description must be a string.")
        if deprecation_reason is not None and not isinstance(deprecation_reason, str):
            raise TypeError("The deprecation reason must be a string.")
        if ast_node and not isinstance(ast_node, FieldDefinitionNode):
            raise TypeError("Field AST node must be a FieldDefinitionNode.")
        self.type = type_
        self.args = args or {}
        self.resolve = resolve
        self.subscribe = subscribe
        self.deprecation_reason = deprecation_reason
        self.description = description
        self.ast_node = ast_node

    def __eq__(self, other):
        return self is other or (
            isinstance(other, GraphQLField)
            and self.type == other.type
            and self.args == other.args
            and self.resolve == other.resolve
            and self.description == other.description
            and self.deprecation_reason == other.deprecation_reason
        )

    @property
    def is_deprecated(self):
        return bool(self.deprecation_reason)


ResponsePath = namedtuple("ResponsePath", "prev,key")

# class ResponsePath(object):

#     def __init__(self, prev, key):
#         # type: (Union[str, int], Optional[ResponsePath]) -> None
#         self.prev = prev
#         self.key = key


# class GraphQLResolveInfo(NamedTuple):
#     """Collection of information passed to the resolvers.

#     This is always passed as the first argument to the resolvers.

#     Note that contrary to the JavaScript implementation, the context
#     (commonly used to represent an authenticated user, or request-specific
#     caches) is included here and not passed as an additional argument.
#     """

#     field_name: str
#     field_nodes: List[FieldNode]
#     return_type: "GraphQLOutputType"
#     parent_type: "GraphQLObjectType"
#     path: ResponsePath
#     schema: "GraphQLSchema"
#     fragments: Dict[str, FragmentDefinitionNode]
#     root_value: Any
#     operation: OperationDefinitionNode
#     variable_values: Dict[str, Any]
#     context: Any

GraphQLResolveInfo = namedtuple(
    "GraphQLResolveInfo",
    (
        "field_name",
        "field_nodes",
        "return_type",
        "parent_type",
        "path",
        "schema",
        "fragments",
        "root_value",
        "operation",
        "variable_values",
        "context",
    ),
)

# Note: Contrary to the Javascript implementation of GraphQLFieldResolver,
# the context is passed as part of the GraphQLResolveInfo and any arguments
# are passed individually as keyword arguments.
GraphQLFieldResolverWithoutArgs = Callable[[Any, GraphQLResolveInfo], Any]
# Unfortunately there is currently no syntax to indicate optional or keyword
# arguments in Python, so we also allow any other Callable as a workaround:
GraphQLFieldResolver = Callable[..., Any]

# Note: Contrary to the Javascript implementation of GraphQLTypeResolver,
# the context is passed as part of the GraphQLResolveInfo:
GraphQLTypeResolver = Callable[
    [Any, GraphQLResolveInfo], MaybeAwaitable[Union["GraphQLObjectType", str]]
]

# Note: Contrary to the Javascript implementation of GraphQLIsTypeOfFn,
# the context is passed as part of the GraphQLResolveInfo:
GraphQLIsTypeOfFn = Callable[[Any, GraphQLResolveInfo], MaybeAwaitable[bool]]


class GraphQLArgument:
    """Definition of a GraphQL argument"""

    # type: "GraphQLInputType"
    # default_value: Any
    # description: Optional[str]
    # ast_node: Optional[InputValueDefinitionNode]

    def __init__(
        self,
        type_,  # type: GraphQLInputType
        default_value=INVALID,  # type: Any
        description=None,  # type: str
        ast_node=None,  # type: InputValueDefinitionNode
    ):
        # type: (...) -> None
        if not is_input_type(type_):
            raise TypeError("Argument type must be a GraphQL input type.")
        if description is not None and not isinstance(description, str):
            raise TypeError("The description must be a string.")
        if ast_node and not isinstance(ast_node, InputValueDefinitionNode):
            raise TypeError("Argument AST node must be an InputValueDefinitionNode.")
        self.type = type_
        self.default_value = default_value
        self.description = description
        self.ast_node = ast_node

    def __eq__(self, other):
        return self is other or (
            isinstance(other, GraphQLArgument)
            and self.type == other.type
            and self.default_value == other.default_value
            and self.description == other.description
        )


def is_required_argument(arg):
    return is_non_null_type(arg.type) and arg.default_value is INVALID


T = TypeVar("T")
Thunk = Union[Callable[[], T], T]

GraphQLFieldMap = Dict[str, GraphQLField]
GraphQLInterfaceList = Sequence["GraphQLInterfaceType"]


class GraphQLObjectType(GraphQLNamedType):
    """Object Type Definition

    Almost all of the GraphQL types you define will be object types.
    Object types have a name, but most importantly describe their fields.

    Example::

        AddressType = GraphQLObjectType('Address', {
            'street': GraphQLField(GraphQLString),
            'number': GraphQLField(GraphQLInt),
            'formatted': GraphQLField(GraphQLString,
                lambda obj, info, **args: f'{obj.number} {obj.street}')
        })

    When two types need to refer to each other, or a type needs to refer to
    itself in a field, you can use a lambda function with no arguments (a
    so-called "thunk") to supply the fields lazily.

    Example::

        PersonType = GraphQLObjectType('Person', lambda: {
            'name': GraphQLField(GraphQLString),
            'bestFriend': GraphQLField(PersonType)
        })

    """

    def __init__(
        self,
        name,
        fields,
        interfaces=None,
        is_type_of=None,
        description=None,
        ast_node=None,
        extension_ast_nodes=None,
    ):
        super(GraphQLObjectType, self).__init__(
            name=name,
            description=description,
            ast_node=ast_node,
            extension_ast_nodes=extension_ast_nodes,
        )
        if is_type_of is not None and not callable(is_type_of):
            raise TypeError(
                (
                    "{} must provide 'is_type_of' as a function," " but got: {!r}."
                ).format(name, is_type_of)
            )
        if ast_node and not isinstance(ast_node, ObjectTypeDefinitionNode):
            raise TypeError(
                "{} AST node must be an ObjectTypeDefinitionNode.".format(name)
            )
        if extension_ast_nodes and not all(
            isinstance(node, ObjectTypeExtensionNode) for node in extension_ast_nodes
        ):
            raise TypeError(
                ("{} extension AST nodes" " must be ObjectTypeExtensionNodes.").format(
                    name
                )
            )
        self._fields = fields
        self._interfaces = interfaces
        self.is_type_of = is_type_of

    @cached_property
    def fields(self):
        """Get provided fields, wrapping them as GraphQLFields if needed."""
        try:
            fields = resolve_thunk(self._fields)
        except GraphQLError:
            raise
        except Exception as error:
            raise TypeError("{} fields cannot be resolved: {}".format(self.name, error))
        if not isinstance(fields, dict) or not all(
            isinstance(key, str) for key in fields
        ):
            raise TypeError(
                (
                    "{} fields must be a dict with field names as keys"
                    " or a function which returns such an object."
                ).format(self.name)
            )
        if not all(
            isinstance(value, GraphQLField) or is_output_type(value)
            for value in fields.values()
        ):
            raise TypeError(
                ("{} fields must be" " GraphQLField or output type objects.").format(
                    self.name
                )
            )
        return {
            name: value if isinstance(value, GraphQLField) else GraphQLField(value)
            for name, value in fields.items()
        }

    @cached_property
    def interfaces(self):
        """Get provided interfaces."""
        try:
            interfaces = resolve_thunk(self._interfaces)
        except GraphQLError:
            raise
        except Exception as error:
            raise TypeError(
                "{} interfaces cannot be resolved: {}".format(self.name, error)
            )
        if interfaces is None:
            interfaces = []
        if not isinstance(interfaces, (list, tuple)):
            raise TypeError(
                (
                    "{} interfaces must be a list/tuple"
                    " or a function which returns a list/tuple."
                ).format(self.name)
            )
        if not all(isinstance(value, GraphQLInterfaceType) for value in interfaces):
            raise TypeError(
                "{} interfaces must be GraphQLInterface objects.".format(self.name)
            )
        return interfaces[:]


def is_object_type(type_):
    return isinstance(type_, GraphQLObjectType)


def assert_object_type(type_):
    if not is_object_type(type_):
        raise TypeError("Expected {} to be a GraphQL Object type.".format(type_))
    return type_


class GraphQLInterfaceType(GraphQLNamedType):
    """Interface Type Definition

    When a field can return one of a heterogeneous set of types, a Interface
    type is used to describe what types are possible, what fields are in common
    across all types, as well as a function to determine which type is actually
    used when the field is resolved.

    Example::

        EntityType = GraphQLInterfaceType('Entity', {
                'name': GraphQLField(GraphQLString),
            })
    """

    def __init__(
        self,
        name,
        fields=None,
        resolve_type=None,
        description=None,
        ast_node=None,
        extension_ast_nodes=None,
    ):
        super(GraphQLInterfaceType, self).__init__(
            name=name,
            description=description,
            ast_node=ast_node,
            extension_ast_nodes=extension_ast_nodes,
        )
        if resolve_type is not None and not callable(resolve_type):
            raise TypeError(
                (
                    "{} must provide 'resolve_type' as a function," " but got: {!r}."
                ).format(name, resolve_type)
            )
        if ast_node and not isinstance(ast_node, InterfaceTypeDefinitionNode):
            raise TypeError(
                "{} AST node must be an InterfaceTypeDefinitionNode.".format(name)
            )
        if extension_ast_nodes and not all(
            isinstance(node, InterfaceTypeExtensionNode) for node in extension_ast_nodes
        ):
            raise TypeError(
                (
                    "{} extension AST nodes" " must be InterfaceTypeExtensionNodes."
                ).format(name)
            )
        self._fields = fields
        self.resolve_type = resolve_type
        self.description = description

    @cached_property
    def fields(self):
        """Get provided fields, wrapping them as GraphQLFields if needed."""
        try:
            fields = resolve_thunk(self._fields)
        except GraphQLError:
            raise
        except Exception as error:
            raise TypeError("{} fields cannot be resolved: {}".format(self.name, error))
        if not isinstance(fields, dict) or not all(
            isinstance(key, str) for key in fields
        ):
            raise TypeError(
                (
                    "{} fields must be a dict with field names as keys"
                    " or a function which returns such an object."
                ).format(self.name)
            )
        if not all(
            isinstance(value, GraphQLField) or is_output_type(value)
            for value in fields.values()
        ):
            raise TypeError(
                ("{} fields must be" " GraphQLField or output type objects.").format(
                    self.name
                )
            )
        return {
            name: value if isinstance(value, GraphQLField) else GraphQLField(value)
            for name, value in fields.items()
        }


def is_interface_type(type_):
    return isinstance(type_, GraphQLInterfaceType)


def assert_interface_type(type_):
    if not is_interface_type(type_):
        raise TypeError("Expected {} to be a GraphQL Interface type.".format(type_))
    return type_


GraphQLTypeList = Sequence[GraphQLObjectType]


class GraphQLUnionType(GraphQLNamedType):
    """Union Type Definition

    When a field can return one of a heterogeneous set of types, a Union type
    is used to describe what types are possible as well as providing a function
    to determine which type is actually used when the field is resolved.

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

    def __init__(
        self,
        name,
        types,
        resolve_type=None,
        description=None,
        ast_node=None,
        extension_ast_nodes=None,
    ):
        super(GraphQLUnionType, self).__init__(
            name=name,
            description=description,
            ast_node=ast_node,
            extension_ast_nodes=extension_ast_nodes,
        )
        if resolve_type is not None and not callable(resolve_type):
            raise TypeError(
                (
                    "{} must provide 'resolve_type' as a function," " but got: {!r}."
                ).format(name, resolve_type)
            )
        if ast_node and not isinstance(ast_node, UnionTypeDefinitionNode):
            raise TypeError(
                "{} AST node must be a UnionTypeDefinitionNode.".format(name)
            )
        if extension_ast_nodes and not all(
            isinstance(node, UnionTypeExtensionNode) for node in extension_ast_nodes
        ):
            raise TypeError(
                "{} extension AST nodes must be UnionTypeExtensionNode.".format(name)
            )
        self._types = types
        self.resolve_type = resolve_type

    @cached_property
    def types(self):
        """Get provided types."""
        try:
            types = resolve_thunk(self._types)
        except GraphQLError:
            raise
        except Exception as error:
            raise TypeError("{} types cannot be resolved: {}".format(self.name, error))
        if types is None:
            types = []
        if not isinstance(types, (list, tuple)):
            raise TypeError(
                (
                    "{} types must be a list/tuple"
                    " or a function which returns a list/tuple."
                ).format(self.name)
            )
        if not all(isinstance(value, GraphQLObjectType) for value in types):
            raise TypeError(
                "{} types must be GraphQLObjectType objects.".format(self.name)
            )
        return types[:]


def is_union_type(type_):
    return isinstance(type_, GraphQLUnionType)


def assert_union_type(type_):
    if not is_union_type(type_):
        raise TypeError("Expected {} to be a GraphQL Union type.".format(type_))
    return type_


GraphQLEnumValueMap = Dict[str, "GraphQLEnumValue"]


class GraphQLEnumType(GraphQLNamedType):
    """Enum Type Definition

    Some leaf values of requests and input values are Enums. GraphQL serializes
    Enum values as strings, however internally Enums can be represented by any
    kind of type, often integers. They can also be provided as a Python Enum.

    Example::

        RGBType = GraphQLEnumType('RGB', {
            'RED': 0,
            'GREEN': 1,
            'BLUE': 2
        })

    Example using a Python Enum::

        class RGBEnum(enum.Enum):
            RED = 0
            GREEN = 1
            BLUE = 2

        RGBType = GraphQLEnumType('RGB', enum.Enum)

    Instead of raw values, you can also specify GraphQLEnumValue objects
    with more detail like description or deprecation information.

    Note: If a value is not provided in a definition, the name of the enum
    value will be used as its internal value when the value is serialized.
    """

    def __init__(
        self, name, values, description=None, ast_node=None, extension_ast_nodes=None
    ):
        super(GraphQLEnumType, self).__init__(
            name=name,
            description=description,
            ast_node=ast_node,
            extension_ast_nodes=extension_ast_nodes,
        )
        try:  # check for enum
            values = cast(Enum, values).__members__  # type: ignore
        except AttributeError:
            if not isinstance(values, dict) or not all(
                isinstance(name, str) for name in values
            ):
                try:
                    # noinspection PyTypeChecker
                    values = dict(values)  # type: ignore
                except (TypeError, ValueError):
                    raise TypeError(
                        (
                            "{} values must be an Enum or a dict"
                            " with value names as keys."
                        ).format(name)
                    )
            values = values
        else:
            values = values
            values = {key: value.value for key, value in values.items()}
        values = {
            key: value
            if isinstance(value, GraphQLEnumValue)
            else GraphQLEnumValue(value)
            for key, value in values.items()
        }
        if ast_node and not isinstance(ast_node, EnumTypeDefinitionNode):
            raise TypeError(
                "{} AST node must be an EnumTypeDefinitionNode.".format(name)
            )
        if extension_ast_nodes and not all(
            isinstance(node, EnumTypeExtensionNode) for node in extension_ast_nodes
        ):
            raise TypeError(
                "{} extension AST nodes must be EnumTypeExtensionNode.".format(name)
            )
        self.values = values

    @cached_property
    def _value_lookup(self):
        # use first value or name as lookup
        lookup = {}
        for name, enum_value in self.values.items():
            value = enum_value.value
            if value is None:
                value = name
            try:
                if value not in lookup:
                    lookup[value] = name
            except TypeError:
                pass  # ignore unhashable values
        return lookup

    def serialize(self, value):
        try:
            return self._value_lookup.get(value, INVALID)
        except TypeError:  # unhashable value
            for enum_name, enum_value in self.values.items():
                if enum_value.value == value:
                    return enum_name
        return INVALID

    def parse_value(self, value):
        if isinstance(value, str):
            try:
                enum_value = self.values[value]
            except KeyError:
                return INVALID
            if enum_value.value is None:
                return value
            return enum_value.value
        return INVALID

    def parse_literal(self, value_node, _variables=None):
        # Note: variables will be resolved before calling this method.
        if isinstance(value_node, EnumValueNode):
            value = value_node.value
            try:
                enum_value = self.values[value]
            except KeyError:
                return INVALID
            if enum_value.value is None:
                return value
            return enum_value.value
        return INVALID


def is_enum_type(type_):
    return isinstance(type_, GraphQLEnumType)


def assert_enum_type(type_):
    if not is_enum_type(type_):
        raise TypeError("Expected {} to be a GraphQL Enum type.".format(type_))
    return type_


class GraphQLEnumValue:

    def __init__(
        self, value=None, description=None, deprecation_reason=None, ast_node=None
    ):
        if description is not None and not isinstance(description, str):
            raise TypeError("The description must be a string.")
        if deprecation_reason is not None and not isinstance(deprecation_reason, str):
            raise TypeError("The deprecation reason must be a string.")
        if ast_node and not isinstance(ast_node, EnumValueDefinitionNode):
            raise TypeError("AST node must be an EnumValueDefinitionNode.")
        self.value = value
        self.description = description
        self.deprecation_reason = deprecation_reason
        self.ast_node = ast_node

    def __eq__(self, other):
        return self is other or (
            isinstance(other, GraphQLEnumValue)
            and self.value == other.value
            and self.description == other.description
            and self.deprecation_reason == other.deprecation_reason
        )

    @property
    def is_deprecated(self):
        return bool(self.deprecation_reason)


GraphQLInputFieldMap = Dict[str, "GraphQLInputField"]


class GraphQLInputObjectType(GraphQLNamedType):
    """Input Object Type Definition

    An input object defines a structured collection of fields which may be
    supplied to a field argument.

    Using `NonNull` will ensure that a value must be provided by the query

    Example::

        NonNullFloat = GraphQLNonNull(GraphQLFloat())

        class GeoPoint(GraphQLInputObjectType):
            name = 'GeoPoint'
            fields = {
                'lat': GraphQLInputField(NonNullFloat),
                'lon': GraphQLInputField(NonNullFloat),
                'alt': GraphQLInputField(
                          GraphQLFloat(), default_value=0)
            }
    """

    def __init__(
        self, name, fields, description=None, ast_node=None, extension_ast_nodes=None
    ):
        super(GraphQLInputObjectType, self).__init__(
            name=name,
            description=description,
            ast_node=ast_node,
            extension_ast_nodes=extension_ast_nodes,
        )
        if ast_node and not isinstance(ast_node, InputObjectTypeDefinitionNode):
            raise TypeError(
                "{} AST node must be an InputObjectTypeDefinitionNode.".format(name)
            )
        if extension_ast_nodes and not all(
            isinstance(node, InputObjectTypeExtensionNode)
            for node in extension_ast_nodes
        ):
            raise TypeError(
                (
                    "{} extension AST nodes" " must be InputObjectTypeExtensionNode."
                ).format(name)
            )
        self._fields = fields

    @cached_property
    def fields(self):
        """Get provided fields, wrap them as GraphQLInputField if needed."""
        try:
            fields = resolve_thunk(self._fields)
        except GraphQLError:
            raise
        except Exception as error:
            raise TypeError("{} fields cannot be resolved: {}".format(self.name, error))
        if not isinstance(fields, dict) or not all(
            isinstance(key, str) for key in fields
        ):
            raise TypeError(
                (
                    "{} fields must be a dict with field names as keys"
                    " or a function which returns such an object."
                ).format(self.name)
            )
        if not all(
            isinstance(value, GraphQLInputField) or is_input_type(value)
            for value in fields.values()
        ):
            raise TypeError(
                (
                    "{} fields must be" " GraphQLInputField or input type objects."
                ).format(self.name)
            )
        return {
            name: value
            if isinstance(value, GraphQLInputField)
            else GraphQLInputField(value)
            for name, value in fields.items()
        }


def is_input_object_type(type_):
    return isinstance(type_, GraphQLInputObjectType)


def assert_input_object_type(type_):
    if not is_input_object_type(type_):
        raise TypeError("Expected {} to be a GraphQL Input Object type.".format(type_))
    return type_


class GraphQLInputField:
    """Definition of a GraphQL input field"""

    def __init__(self, type_, description=None, default_value=INVALID, ast_node=None):
        if not is_input_type(type_):
            raise TypeError("Input field type must be a GraphQL input type.")
        if ast_node and not isinstance(ast_node, InputValueDefinitionNode):
            raise TypeError("Input field AST node must be an InputValueDefinitionNode.")
        self.type = type_
        self.default_value = default_value
        self.description = description
        self.ast_node = ast_node

    def __eq__(self, other):
        return self is other or (
            isinstance(other, GraphQLInputField)
            and self.type == other.type
            and self.description == other.description
        )


def is_required_input_field(field):
    return is_non_null_type(field.type) and field.default_value is INVALID


# Wrapper types


class GraphQLList(Generic[GT], GraphQLWrappingType[GT]):
    # class GraphQLList(GraphQLWrappingType):
    """List Type Wrapper

    A list is a wrapping type which points to another type.
    Lists are often created within the context of defining the fields of
    an object type.

    Example::

        class PersonType(GraphQLObjectType):
            name = 'Person'

            @property
            def fields(self):
                return {
                    'parents': GraphQLField(GraphQLList(PersonType())),
                    'children': GraphQLField(GraphQLList(PersonType())),
                }
    """

    def __init__(self, type_):
        super(GraphQLList, self).__init__(type_=type_)

    def __str__(self):
        return "[{}]".format(self.of_type)


def is_list_type(type_):
    return isinstance(type_, GraphQLList)


def assert_list_type(type_):
    if not is_list_type(type_):
        raise TypeError("Expected {} to be a GraphQL List type.".format(type_))
    return type_


GNT = TypeVar("GNT", bound="GraphQLNullableType")


class GraphQLNonNull(GraphQLWrappingType[GNT], Generic[GNT]):
    # class GraphQLNonNull(GraphQLWrappingType):
    """Non-Null Type Wrapper

    A non-null is a wrapping type which points to another type.
    Non-null types enforce that their values are never null and can ensure
    an error is raised if this ever occurs during a request. It is useful for
    fields which you can make a strong guarantee on non-nullability,
    for example usually the id field of a database row will never be null.

    Example::

        class RowType(GraphQLObjectType):
            name = 'Row'
            fields = {
                'id': GraphQLField(GraphQLNonNull(GraphQLString()))
            }

    Note: the enforcement of non-nullability occurs within the executor.
    """

    def __init__(self, type_):
        super(GraphQLNonNull, self).__init__(type_=type_)
        if isinstance(type_, GraphQLNonNull):
            raise TypeError(
                "Can only create NonNull of a Nullable GraphQLType but got:"
                " {}.".format(type_)
            )

    def __str__(self):
        return "{}!".format(self.of_type)


def is_non_null_type(type_):
    return isinstance(type_, GraphQLNonNull)


def assert_non_null_type(type_):
    if not is_non_null_type(type_):
        raise TypeError("Expected {} to be a GraphQL Non-Null type.".format(type_))
    return type_


# These types can all accept null as a value.

graphql_nullable_types = (
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
)

GraphQLNullableType = Union[
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
]


def is_nullable_type(type_):
    return isinstance(type_, graphql_nullable_types)


def assert_nullable_type(type_):
    if not is_nullable_type(type_):
        raise TypeError("Expected {} to be a GraphQL nullable type.".format(type_))
    return type_


@overload
def get_nullable_type(type_):
    ...


@overload  # noqa: F811 (pycqa/flake8#423)
def get_nullable_type(type_):
    ...


@overload  # noqa: F811
def get_nullable_type(type_):
    ...


def get_nullable_type(type_):  # noqa: F811
    """Unwrap possible non-null type"""
    if is_non_null_type(type_):
        type_ = type_
        type_ = type_.of_type
    return type_


# These types may be used as input types for arguments and directives.

graphql_input_types = (GraphQLScalarType, GraphQLEnumType, GraphQLInputObjectType)

GraphQLInputType = Union[
    GraphQLScalarType, GraphQLEnumType, GraphQLInputObjectType, GraphQLWrappingType
]


def is_input_type(type_):
    return isinstance(type_, graphql_input_types) or (
        isinstance(type_, GraphQLWrappingType) and is_input_type(type_.of_type)
    )


def assert_input_type(type_):
    if not is_input_type(type_):
        raise TypeError("Expected {} to be a GraphQL input type.".format(type_))
    return type_


# These types may be used as output types as the result of fields.

graphql_output_types = (
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
)

GraphQLOutputType = Union[
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLWrappingType,
]


def is_output_type(type_):
    return isinstance(type_, graphql_output_types) or (
        isinstance(type_, GraphQLWrappingType) and is_output_type(type_.of_type)
    )


def assert_output_type(type_):
    if not is_output_type(type_):
        raise TypeError("Expected {} to be a GraphQL output type.".format(type_))
    return type_


# These types may describe types which may be leaf values.

graphql_leaf_types = (GraphQLScalarType, GraphQLEnumType)

GraphQLLeafType = Union[GraphQLScalarType, GraphQLEnumType]


def is_leaf_type(type_):
    return isinstance(type_, graphql_leaf_types)


def assert_leaf_type(type_):
    if not is_leaf_type(type_):
        raise TypeError("Expected {} to be a GraphQL leaf type.".format(type_))
    return type_


# These types may describe the parent context of a selection set.

graphql_composite_types = (GraphQLObjectType, GraphQLInterfaceType, GraphQLUnionType)

GraphQLCompositeType = Union[GraphQLObjectType, GraphQLInterfaceType, GraphQLUnionType]


def is_composite_type(type_):
    return isinstance(type_, graphql_composite_types)


def assert_composite_type(type_):
    if not is_composite_type(type_):
        raise TypeError("Expected {} to be a GraphQL composite type.".format(type_))
    return type_


# These types may describe abstract types.

graphql_abstract_types = (GraphQLInterfaceType, GraphQLUnionType)

GraphQLAbstractType = Union[GraphQLInterfaceType, GraphQLUnionType]


def is_abstract_type(type_):
    return isinstance(type_, graphql_abstract_types)


def assert_abstract_type(type_):
    if not is_abstract_type(type_):
        raise TypeError("Expected {} to be a GraphQL composite type.".format(type_))
    return type_
