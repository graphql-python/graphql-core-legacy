from copy import deepcopy
from ..pyutils.enum import Enum

from .lexer import Token
from .source import Source
from ..pyutils import camel_to_snake

if False:  # pragma: no cover
    from typing import List, Optional, Union

__all__ = [
    "Location",
    "Node",
    "NameNode",
    "DocumentNode",
    "DefinitionNode",
    "ExecutableDefinitionNode",
    "OperationDefinitionNode",
    "VariableDefinitionNode",
    "SelectionSetNode",
    "SelectionNode",
    "FieldNode",
    "ArgumentNode",
    "FragmentSpreadNode",
    "InlineFragmentNode",
    "FragmentDefinitionNode",
    "ValueNode",
    "VariableNode",
    "IntValueNode",
    "FloatValueNode",
    "StringValueNode",
    "BooleanValueNode",
    "NullValueNode",
    "EnumValueNode",
    "ListValueNode",
    "ObjectValueNode",
    "ObjectFieldNode",
    "DirectiveNode",
    "TypeNode",
    "NamedTypeNode",
    "ListTypeNode",
    "NonNullTypeNode",
    "TypeSystemDefinitionNode",
    "SchemaDefinitionNode",
    "OperationType",
    "OperationTypeDefinitionNode",
    "TypeDefinitionNode",
    "ScalarTypeDefinitionNode",
    "ObjectTypeDefinitionNode",
    "FieldDefinitionNode",
    "InputValueDefinitionNode",
    "InterfaceTypeDefinitionNode",
    "UnionTypeDefinitionNode",
    "EnumTypeDefinitionNode",
    "EnumValueDefinitionNode",
    "InputObjectTypeDefinitionNode",
    "DirectiveDefinitionNode",
    "SchemaExtensionNode",
    "TypeExtensionNode",
    "TypeSystemExtensionNode",
    "ScalarTypeExtensionNode",
    "ObjectTypeExtensionNode",
    "InterfaceTypeExtensionNode",
    "UnionTypeExtensionNode",
    "EnumTypeExtensionNode",
    "InputObjectTypeExtensionNode",
]


class Location(object):
    """AST Location
    Contains a range of UTF-8 character offsets and token references that
    identify the region of the source from which the AST derived.
    """

    def __init__(self, start, end, start_token, end_token, source):
        # type: (int, int, Token, Token, Source) -> None
        self.start = start  # character offset at which this Node begins
        self.end = end  # character offset at which this Node ends
        self.start_token = start_token  # Token at which this Node begins
        self.end_token = end_token  # Token at which this Node ends.
        self.source = source  # Source document the AST represents

    def __str__(self):
        return "{}:{}".format(self.start, self.end)

    def __repr__(self):
        return "Location({}, {})".format(self.start, self.end)

    def __eq__(self, other):
        if isinstance(other, Location):
            return self.start == other.start and self.end == other.end
        elif isinstance(other, (list, tuple)) and len(other) == 2:
            return self.start == other[0] and self.end == other[1]
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class OperationType(Enum):

    QUERY = "query"
    MUTATION = "mutation"
    SUBSCRIPTION = "subscription"

    def __repr__(self):
        return "OperationType.{}".format(self.name)


# Base AST Node


class Node(object):
    """AST nodes"""

    __slots__ = ("loc",)

    # the kind of the node as a snake_case string
    kind = "ast"  # type: str

    def __init__(self, loc=None):
        # type: (Optional[Location]) -> None
        self.loc = loc

    def __repr__(self):
        """Get a simple representation of the node."""
        name = self.__class__.__name__
        args = ['{}={!r}'.format(key, getattr(self, key)) for key in self.__slots__]
        return "{}({})".format(name, ', '.join(args))

    def __str__(self):
        """Get a simple representation of the node."""
        name, loc = self.__class__.__name__, getattr(self, "loc", None)
        return "{} at {}".format(name, loc) if loc else name

    def __eq__(self, other):
        """Test whether two nodes are equal (recursively)."""
        return (
            isinstance(other, Node)
            and self.__class__ == other.__class__
            and all(getattr(self, key) == getattr(other, key) for key in self.__slots__)
        )

    def __hash__(self):
        return id(self)

    def __copy__(self):
        """Create a shallow copy of the node."""
        return self.__class__(**{key: getattr(self, key) for key in self.__slots__})

    def __deepcopy__(self, memo):
        """Create a deep copy of the node"""
        # noinspection PyArgumentList
        return self.__class__(
            **{key: deepcopy(getattr(self, key), memo) for key in self.__slots__}
        )

    # def __init_subclass__(cls, **kwargs):
    #     super(Node, cls).__init_subclass__(**kwargs)
    #     name = cls.__name__
    #     if name.endswith("Node"):
    #         name = name[:-4]
    #     cls.kind = camel_to_snake(name)


# Name


class NameNode(Node):
    __slots__ = ("value", "loc")
    kind = 'name'

    def __init__(self, value, loc=None):
        # type: (str, Optional[Location]) -> None
        self.value = value
        self.loc = loc


# Document


class DocumentNode(Node):
    __slots__ = ("definitions", "loc")
    kind = 'document'

    def __init__(self, definitions, loc=None):
        # type: (List[DefinitionNode], Optional[Location]) -> None
        self.definitions = definitions
        self.loc = loc


class DefinitionNode(Node):
    pass


class ExecutableDefinitionNode(DefinitionNode):
    __slots__ = ("directives", "variable_definitions", "selection_set", "loc")
    kind = 'executable_definition'

    def __init__(
        self,
        # name,  # type: NameNode
        directives,  # type: Optional[List[DirectiveNode]]
        selection_set,  # type: SelectionSetNode
        variable_definitions=None,  # type: Optional[List[VariableDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        # self.name = name
        self.directives = directives
        self.selection_set = selection_set
        self.variable_definitions = variable_definitions
        self.loc = loc


class OperationDefinitionNode(ExecutableDefinitionNode):
    __slots__ = (
        "operation",
        "selection_set",
        "name",
        "variable_definitions",
        "directives",
        "loc",
    )
    kind = 'operation_definition'

    def __init__(
        self,
        variable_definitions,  # type: List[VariableDefinitionNode]
        selection_set,  # type: SelectionSetNode
        operation,  # type: OperationType
        name=None,  # type: Optional[NameNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.directives = directives
        self.variable_definitions = variable_definitions
        self.selection_set = selection_set
        self.operation = operation
        self.loc = loc


class VariableDefinitionNode(Node):
    __slots__ = ("variable", "type", "default_value", "directives", "loc")
    kind = 'variable_definition'

    def __init__(
        self,
        variable,  # type: VariableNode
        type,  # type: TypeNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        default_value=None,  # type: Optional[ValueNode]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.variable = variable
        self.type = type
        self.directives = directives
        self.default_value = default_value
        self.loc = loc


class SelectionSetNode(Node):
    __slots__ = ("selections", "loc")
    kind = 'selection_set'

    def __init__(
        self,
        selections,  # type: List[SelectionNode]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.selections = selections
        self.loc = loc


class SelectionNode(Node):
    __slots__ = ("directives", "loc")
    kind = 'selection'

    def __init__(
        self,
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.directives = directives
        self.loc = loc


class FieldNode(SelectionNode):
    __slots__ = ("alias", "name", "arguments", "selection_set", "directives", "loc")
    kind = 'field'

    def __init__(
        self,
        name,  # type: NameNode
        alias=None,  # type: Optional[NameNode]
        arguments=None,  # type: Optional[List[ArgumentNode]]
        selection_set=None,  # type: Optional[SelectionSetNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.directives = directives
        self.loc = loc
        self.name = name
        self.alias = alias
        self.arguments = arguments
        self.selection_set = selection_set


class ArgumentNode(Node):
    __slots__ = ("name", "value", "loc")
    kind = 'argument'

    def __init__(
        self,
        name,  # type: NameNode
        value,  # type: ValueNode
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.value = value
        self.loc = loc


# Fragments


class FragmentSpreadNode(SelectionNode):
    __slots__ = ("name", "loc")
    kind = 'fragment_spread'

    def __init__(
        self,
        name,  # type: NameNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.directives = directives
        self.loc = loc
        self.name = name


class InlineFragmentNode(SelectionNode):
    __slots__ = ("type_condition", "selection_set", "loc")
    kind = 'inline_fragment'

    def __init__(
        self,
        type_condition,  # type: NamedTypeNode
        selection_set,  # type: SelectionSetNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.directives = directives
        self.loc = loc
        self.type_condition = type_condition
        self.selection_set = selection_set


class FragmentDefinitionNode(ExecutableDefinitionNode):
    __slots__ = (
        "name",
        "type_condition",
        "directives",
        "variable_definitions",
        "selection_set",
        "loc",
    )
    kind = 'fragment_definition'

    def __init__(
        self,
        name,  # type: NameNode
        type_condition,  # type: NamedTypeNode
        selection_set,  # type: SelectionSetNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        variable_definitions=None,  # type: Optional[List[VariableDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.directives = directives
        self.selection_set = selection_set
        self.variable_definitions = variable_definitions
        self.loc = loc
        self.name = name
        self.type_condition = type_condition


# Values


class ValueNode(Node):
    pass


class VariableNode(ValueNode):
    __slots__ = ("name", "loc")
    kind = 'variable'

    def __init__(self, name, loc=None):
        # type: (NameNode, Optional[Location]) -> None
        self.name = name
        self.loc = loc


class IntValueNode(ValueNode):
    __slots__ = ("value", "loc")
    kind = 'int_value'

    def __init__(self, value, loc=None):
        # type: (str, Optional[Location]) -> None
        self.value = value
        self.loc = loc


class FloatValueNode(ValueNode):
    __slots__ = ("value", "loc")
    kind = 'float_value'

    def __init__(self, value, loc=None):
        # type: (str, Optional[Location]) -> None
        self.value = value
        self.loc = loc


class StringValueNode(ValueNode):
    __slots__ = ("value", "block", "loc")
    kind = 'string_value'

    def __init__(
        self,
        value,  # type: str
        block=None,  # type: Optional[bool]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.value = value
        self.block = block
        self.loc = loc


class BooleanValueNode(ValueNode):
    __slots__ = ("value",)
    kind = 'boolean_value'

    def __init__(self, value, loc=None):
        # type: (bool, Optional[Location]) -> None
        self.value = value
        self.loc = loc


class NullValueNode(ValueNode):
    kind = 'null_value'


class EnumValueNode(ValueNode):
    __slots__ = ("value", "loc")
    kind = 'enum_value'

    def __init__(self, value, loc=None):
        # type: (str, Optional[Location]) -> None
        self.value = value
        self.loc = loc


class ListValueNode(ValueNode):
    __slots__ = ("values", "loc")
    kind = 'list_value'

    def __init__(self, values, loc=None):
        # type: (List[ValueNode], Optional[Location]) -> None
        self.values = values
        self.loc = loc


class ObjectValueNode(ValueNode):
    __slots__ = ("fields", "loc")
    kind = 'object_value'

    def __init__(
        self,
        fields,  # type: List[ObjectFieldNode]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.fields = fields
        self.loc = loc


class ObjectFieldNode(Node):
    __slots__ = ("name", "value", "loc")
    kind = 'object_field'

    def __init__(
        self,
        name,  # type: NameNode
        value,  # type: ValueNode
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.value = value
        self.loc = loc


# Directives


class DirectiveNode(Node):
    __slots__ = ("name", "arguments", "loc")
    kind = 'directive'

    def __init__(
        self,
        name,  # type: NameNode
        arguments,  # type: List[ArgumentNode]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.arguments = arguments
        self.loc = loc


# Type Reference


class TypeNode(Node):
    __slots__ = ()


class NamedTypeNode(TypeNode):
    __slots__ = ("name", "loc")
    kind = 'named_type'

    def __init__(self, name, loc=None):
        # type: (NameNode, Optional[Location]) -> None
        self.name = name
        self.loc = loc


class ListTypeNode(TypeNode):
    __slots__ = ("type", "loc")
    kind = 'list_type'

    def __init__(self, type, loc=None):
        # type: (TypeNode, Optional[Location]) -> None
        self.type = type
        self.loc = loc


class NonNullTypeNode(TypeNode):
    __slots__ = ("type",)
    kind = 'non_null_type'

    def __init__(
        self,
        type,  # type: Union[NamedTypeNode, ListTypeNode]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.type = type
        self.loc = loc


# Type System Definition


class TypeSystemDefinitionNode(DefinitionNode):
    __slots__ = ()


class SchemaDefinitionNode(TypeSystemDefinitionNode):
    __slots__ = ("directives", "operation_types", "loc")
    kind = 'schema_definition'

    def __init__(
        self,
        operation_types,  # type: List[OperationTypeDefinitionNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.directives = directives
        self.operation_types = operation_types
        self.loc = loc


class OperationTypeDefinitionNode(Node):
    __slots__ = ("operation", "type", "loc")
    kind = 'operation_type_definition'

    def __init__(
        self,
        operation,  # type: OperationType
        type,  # type: NamedTypeNode
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.operation = operation
        self.type = type
        self.loc = loc


# Type Definition


class TypeDefinitionNode(TypeSystemDefinitionNode):
    __slots__ = ("description", "name", "directives", "loc")
    kind = 'type_definition'

    def __init__(
        self,
        name,  # type: NameNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc


class ScalarTypeDefinitionNode(TypeDefinitionNode):
    kind = 'scalar_type_definition'


class ObjectTypeDefinitionNode(TypeDefinitionNode):
    __slots__ = ("interfaces", "fields", "name", "description", "directives", "loc")
    kind = 'object_type_definition'

    def __init__(
        self,
        name,  # type: NameNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        interfaces=None,  # type: Optional[List[NamedTypeNode]]
        fields=None,  # type: Optional[List[FieldDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc
        self.interfaces = interfaces
        self.fields = fields


class FieldDefinitionNode(TypeDefinitionNode):
    __slots__ = ("arguments", "type", "name", "description", "directives", "loc")
    kind = 'field_definition'

    def __init__(
        self,
        name,  # type: NameNode
        type,  # type: TypeNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        arguments=None,  # type: Optional[List[InputValueDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc
        self.type = type
        self.arguments = arguments


class InputValueDefinitionNode(TypeDefinitionNode):
    __slots__ = ("type", "default_value", "name", "description", "directives", "loc")
    kind = 'input_value_definition'

    def __init__(
        self,
        name,  # type: NameNode
        type,  # type: TypeNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        default_value=None,  # type: Optional[ValueNode]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc
        self.type = type
        self.default_value = default_value


class InterfaceTypeDefinitionNode(TypeDefinitionNode):
    __slots__ = ("fields", "name", "description", "directives", "loc")
    kind = 'interface_type_definition'

    def __init__(
        self,
        name,  # type: NameNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        fields=None,  # type: Optional[List[FieldDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc
        self.fields = fields


class UnionTypeDefinitionNode(TypeDefinitionNode):
    __slots__ = ("name", "description", "directives", "types", "loc")
    kind = 'union_type_definition'

    def __init__(
        self,
        name,  # type: NameNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        types=None,  # type: Optional[List[NamedTypeNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc
        self.types = types
        self.loc = loc


class EnumTypeDefinitionNode(TypeDefinitionNode):
    __slots__ = ("name", "description", "directives", "values", "loc")
    kind = 'enum_type_definition'

    def __init__(
        self,
        name,  # type: NameNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        values=None,  # type: Optional[List[EnumValueDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc
        self.values = values


class EnumValueDefinitionNode(TypeDefinitionNode):
    kind = 'enum_value_definition'


class InputObjectTypeDefinitionNode(TypeDefinitionNode):
    __slots__ = ("name", "description", "directives", "fields", "loc")
    kind = 'input_object_type_definition'

    def __init__(
        self,
        name,  # type: NameNode
        description=None,  # type: Optional[StringValueNode]
        directives=None,  # type: Optional[List[DirectiveNode]]
        fields=None,  # type: Optional[List[InputValueDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.directives = directives
        self.loc = loc
        self.fields = fields


# Directive Definitions


class DirectiveDefinitionNode(TypeSystemDefinitionNode):
    __slots__ = ("name", "locations", "description", "arguments", "loc")
    kind = 'directive_definition'

    def __init__(
        self,
        name,  # type: NameNode
        locations,  # type: List[NameNode]
        description=None,  # type: Optional[StringValueNode]
        arguments=None,  # type: Optional[List[InputValueDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.description = description
        self.arguments = arguments
        self.locations = locations
        self.loc = loc


# Type System Extensions


class SchemaExtensionNode(Node):
    __slots__ = ("directives", "operation_types", "loc")
    kind = 'schema_extension'

    def __init__(
        self,
        directives=None,  # type: Optional[List[DirectiveNode]]
        operation_types=None,  # type: Optional[List[OperationTypeDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.directives = directives
        self.operation_types = operation_types
        self.loc = loc


# Type Extensions


class TypeExtensionNode(TypeSystemDefinitionNode):
    __slots__ = ("name", "directives", "loc")
    kind = 'type_extension'

    def __init__(
        self,
        name,  # type: NameNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.directives = directives
        self.loc = loc


if False:
    TypeSystemExtensionNode = Union[SchemaExtensionNode, TypeExtensionNode]
else:
    TypeSystemExtensionNode = None


class ScalarTypeExtensionNode(TypeExtensionNode):
    kind = 'scalar_type_extension'


class ObjectTypeExtensionNode(TypeExtensionNode):
    __slots__ = ("name", "directives", "interfaces", "fields", "loc")
    kind = 'object_type_extension'

    def __init__(
        self,
        name,  # type: NameNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        interfaces=None,  # type: Optional[List[NamedTypeNode]]
        fields=None,  # type: Optional[List[FieldDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.directives = directives
        self.interfaces = interfaces
        self.fields = fields
        self.loc = loc


class InterfaceTypeExtensionNode(TypeExtensionNode):
    __slots__ = ("name", "directives", "fields", "loc")
    kind = 'interface_type_extension'

    def __init__(
        self,
        name,  # type: NameNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        fields=None,  # type: Optional[List[FieldDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.directives = directives
        self.fields = fields
        self.loc = loc


class UnionTypeExtensionNode(TypeExtensionNode):
    __slots__ = ("name", "directives", "types", "loc")
    kind = 'union_type_extension'

    def __init__(
        self,
        name,  # type: NameNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        types=None,  # type: Optional[List[NamedTypeNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.directives = directives
        self.types = types
        self.loc = loc


class EnumTypeExtensionNode(TypeExtensionNode):
    __slots__ = ("name", "directives", "values", "loc")
    kind = 'enum_type_extension'

    def __init__(
        self,
        name,  # type: NameNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        values=None,  # type: Optional[List[EnumValueDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.directives = directives
        self.values = values
        self.loc = loc


class InputObjectTypeExtensionNode(TypeExtensionNode):
    __slots__ = ("name", "directives", "fields", "loc")
    kind = 'input_object_type_extension'

    def __init__(
        self,
        name,  # type: NameNode
        directives=None,  # type: Optional[List[DirectiveNode]]
        fields=None,  # type: Optional[List[InputValueDefinitionNode]]
        loc=None,  # type: Optional[Location]
    ):
        # type: (...) -> None
        self.name = name
        self.directives = directives
        self.fields = fields
        self.loc = loc
