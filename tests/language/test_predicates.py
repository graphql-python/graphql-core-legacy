from graphql.language import (
    DefinitionNode,
    DocumentNode,
    ExecutableDefinitionNode,
    FieldDefinitionNode,
    FieldNode,
    InlineFragmentNode,
    IntValueNode,
    Node,
    NonNullTypeNode,
    ObjectValueNode,
    ScalarTypeDefinitionNode,
    ScalarTypeExtensionNode,
    SchemaDefinitionNode,
    SchemaExtensionNode,
    SelectionNode,
    SelectionSetNode,
    TypeDefinitionNode,
    TypeExtensionNode,
    TypeNode,
    TypeSystemDefinitionNode,
    ValueNode,
    is_definition_node,
    is_executable_definition_node,
    is_selection_node,
    is_value_node,
    is_type_node,
    is_type_system_definition_node,
    is_type_definition_node,
    is_type_system_extension_node,
    is_type_extension_node,
)


def describe_predicates():
    def check_definition_node():
        assert not is_definition_node(Node())
        assert not is_definition_node(DocumentNode(None))
        assert is_definition_node(DefinitionNode())
        assert is_definition_node(ExecutableDefinitionNode(None, None, None))
        assert is_definition_node(TypeSystemDefinitionNode())

    def check_exectuable_definition_node():
        assert not is_executable_definition_node(Node())
        assert not is_executable_definition_node(DocumentNode(None))
        assert not is_executable_definition_node(DefinitionNode())
        assert is_executable_definition_node(ExecutableDefinitionNode(None, None, None))
        assert not is_executable_definition_node(TypeSystemDefinitionNode())

    def check_selection_node():
        assert not is_selection_node(Node())
        assert not is_selection_node(DocumentNode(None))
        assert is_selection_node(SelectionNode())
        assert is_selection_node(FieldNode(None))
        assert is_selection_node(InlineFragmentNode(None, None))
        assert not is_selection_node(SelectionSetNode(None))

    def check_value_node():
        assert not is_value_node(Node())
        assert not is_value_node(DocumentNode(None))
        assert is_value_node(ValueNode())
        assert is_value_node(IntValueNode(None))
        assert is_value_node(ObjectValueNode(None))
        assert not is_value_node(TypeNode())

    def check_type_node():
        assert not is_type_node(Node())
        assert not is_type_node(DocumentNode(None))
        assert not is_type_node(ValueNode())
        assert is_type_node(TypeNode())
        assert is_type_node(NonNullTypeNode(None))

    def check_type_system_definition_node():
        assert not is_type_system_definition_node(Node())
        assert not is_type_system_definition_node(DocumentNode(None))
        assert is_type_system_definition_node(TypeSystemDefinitionNode())
        assert not is_type_system_definition_node(TypeNode())
        assert not is_type_system_definition_node(DefinitionNode())
        assert is_type_system_definition_node(TypeDefinitionNode(None))
        assert is_type_system_definition_node(SchemaDefinitionNode(None))
        assert is_type_system_definition_node(ScalarTypeDefinitionNode(None))
        assert is_type_system_definition_node(FieldDefinitionNode(None, None))

    def check_type_definition_node():
        assert not is_type_definition_node(Node())
        assert not is_type_definition_node(DocumentNode(None))
        assert is_type_definition_node(TypeDefinitionNode(None))
        assert is_type_definition_node(ScalarTypeDefinitionNode(None))
        assert not is_type_definition_node(TypeSystemDefinitionNode())
        assert not is_type_definition_node(DefinitionNode())
        assert not is_type_definition_node(TypeNode())

    def check_type_system_extension_node():
        assert not is_type_system_extension_node(Node())
        assert not is_type_system_extension_node(DocumentNode(None))
        assert is_type_system_extension_node(SchemaExtensionNode())
        assert is_type_system_extension_node(TypeExtensionNode(None))
        assert not is_type_system_extension_node(TypeSystemDefinitionNode())
        assert not is_type_system_extension_node(DefinitionNode())
        assert not is_type_system_extension_node(TypeNode())

    def check_type_extension_node():
        assert not is_type_extension_node(Node())
        assert not is_type_extension_node(DocumentNode(None))
        assert is_type_extension_node(TypeExtensionNode(None))
        assert not is_type_extension_node(ScalarTypeDefinitionNode(None))
        assert is_type_extension_node(ScalarTypeExtensionNode(None))
        assert not is_type_extension_node(DefinitionNode())
        assert not is_type_extension_node(TypeNode())
