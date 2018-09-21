from typing import Any, Callable, Dict, List, NoReturn, Optional, Union, cast

from ..language import (
    DirectiveDefinitionNode,
    DirectiveLocation,
    DocumentNode,
    EnumTypeDefinitionNode,
    EnumValueDefinitionNode,
    FieldDefinitionNode,
    InputObjectTypeDefinitionNode,
    InputValueDefinitionNode,
    InterfaceTypeDefinitionNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    ObjectTypeDefinitionNode,
    OperationType,
    ScalarTypeDefinitionNode,
    SchemaDefinitionNode,
    Source,
    TypeDefinitionNode,
    TypeNode,
    UnionTypeDefinitionNode,
    parse,
    Node,
)
from ..type import (
    GraphQLArgument,
    GraphQLDeprecatedDirective,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLIncludeDirective,
    GraphQLInputType,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLNullableType,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLSkipDirective,
    GraphQLType,
    GraphQLUnionType,
    introspection_types,
    specified_scalar_types,
)
from .value_from_ast import value_from_ast

TypeDefinitionsMap = Dict[str, TypeDefinitionNode]
TypeResolver = Callable[[NamedTypeNode], GraphQLNamedType]

__all__ = [
    "build_ast_schema",
    "build_schema",
    "get_description",
    "ASTDefinitionBuilder",
]


def build_ast_schema(document_ast, assume_valid=False, assume_valid_sdl=False):
    """Build a GraphQL Schema from a given AST.

    This takes the ast of a schema document produced by the parse function in
    src/language/parser.py.

    If no schema definition is provided, then it will look for types named
    Query and Mutation.

    Given that AST it constructs a GraphQLSchema. The resulting schema
    has no resolve methods, so execution will use default resolvers.

    When building a schema from a GraphQL service's introspection result, it
    might be safe to assume the schema is valid. Set `assume_valid` to True
    to assume the produced schema is valid. Set `assume_valid_sdl` to True to
    assume it is already a valid SDL document.
    """
    if not isinstance(document_ast, DocumentNode):
        raise TypeError("Must provide a Document AST.")

    if not (assume_valid or assume_valid_sdl):
        from ..validation.validate import assert_valid_sdl

        assert_valid_sdl(document_ast)

    schema_def = None
    type_defs = []
    append_type_def = type_defs.append
    node_map = {}
    directive_defs = []
    append_directive_def = directive_defs.append
    for def_ in document_ast.definitions:
        if isinstance(def_, SchemaDefinitionNode):
            schema_def = def_
        elif isinstance(def_, TypeDefinitionNode):
            def_ = def_
            type_name = def_.name.value
            if type_name in node_map:
                raise TypeError(
                    "Type '{}' was defined more than once.".format(type_name)
                )
            append_type_def(def_)
            node_map[type_name] = def_
        elif isinstance(def_, DirectiveDefinitionNode):
            append_directive_def(def_)

    if schema_def:
        operation_types = get_operation_types(schema_def, node_map)
    else:
        operation_types = {
            OperationType.QUERY: node_map.get("Query"),
            OperationType.MUTATION: node_map.get("Mutation"),
            OperationType.SUBSCRIPTION: node_map.get("Subscription"),
        }

    def resolve_type(type_ref):
        raise TypeError("Type {!r} not found in document.".format(type_ref.name.value))

    definition_builder = ASTDefinitionBuilder(
        node_map, assume_valid=assume_valid, resolve_type=resolve_type
    )

    directives = [
        definition_builder.build_directive(directive_def)
        for directive_def in directive_defs
    ]

    # If specified directives were not explicitly declared, add them.
    if not any(directive.name == "skip" for directive in directives):
        directives.append(GraphQLSkipDirective)
    if not any(directive.name == "include" for directive in directives):
        directives.append(GraphQLIncludeDirective)
    if not any(directive.name == "deprecated" for directive in directives):
        directives.append(GraphQLDeprecatedDirective)

    # Note: While this could make early assertions to get the correctly
    # typed values below, that would throw immediately while type system
    # validation with validate_schema will produce more actionable results.
    query_type = operation_types.get(OperationType.QUERY)
    mutation_type = operation_types.get(OperationType.MUTATION)
    subscription_type = operation_types.get(OperationType.SUBSCRIPTION)
    return GraphQLSchema(
        query=definition_builder.build_type(query_type) if query_type else None,
        mutation=definition_builder.build_type(mutation_type)
        if mutation_type
        else None,
        subscription=definition_builder.build_type(subscription_type)
        if subscription_type
        else None,
        types=[definition_builder.build_type(node) for node in type_defs],
        directives=directives,
        ast_node=schema_def,
        assume_valid=assume_valid,
    )


def get_operation_types(schema, node_map):
    op_types = {}
    for operation_type in schema.operation_types:
        type_name = operation_type.type.name.value
        operation = operation_type.operation
        if operation in op_types:
            raise TypeError(
                "Must provide only one {} type in schema.".format(operation.value)
            )
        if type_name not in node_map:
            raise TypeError(
                ("Specified {} type '{}'" " not found in document.").format(
                    operation.value, type_name
                )
            )
        op_types[operation] = operation_type.type
    return op_types


def default_type_resolver(type_ref):
    """Type resolver that always throws an error."""
    raise TypeError("Type '{}' not found in document.".format(type_ref.name.value))


class ASTDefinitionBuilder(object):
    def __init__(
        self,
        type_definitions_map,
        assume_valid=False,
        resolve_type=default_type_resolver,
    ):
        self._type_definitions_map = type_definitions_map
        self._assume_valid = assume_valid
        self._resolve_type = resolve_type
        # Initialize to the GraphQL built in scalars and introspection types.
        self._cache = dict(specified_scalar_types, **introspection_types)

    def build_type(self, node):
        type_name = node.name.value
        cache = self._cache
        if type_name not in cache:
            if isinstance(node, NamedTypeNode):
                def_node = self._type_definitions_map.get(type_name)
                cache[type_name] = (
                    self._make_schema_def(def_node)
                    if def_node
                    else self._resolve_type(node)
                )
            else:
                cache[type_name] = self._make_schema_def(node)
        return cache[type_name]

    def _build_wrapped_type(self, type_node):
        if isinstance(type_node, ListTypeNode):
            return GraphQLList(self._build_wrapped_type(type_node.type))
        if isinstance(type_node, NonNullTypeNode):
            return GraphQLNonNull(
                # Note: GraphQLNonNull constructor validates this type
                self._build_wrapped_type(type_node.type)
            )
        return self.build_type(type_node)

    def build_directive(self, directive_node):
        return GraphQLDirective(
            name=directive_node.name.value,
            description=directive_node.description.value
            if directive_node.description
            else None,
            locations=[
                DirectiveLocation[node.value] for node in directive_node.locations
            ],
            args=self._make_args(directive_node.arguments)
            if directive_node.arguments
            else None,
            ast_node=directive_node,
        )

    def build_field(self, field):
        # Note: While this could make assertions to get the correctly typed
        # value, that would throw immediately while type system validation
        # with validate_schema() will produce more actionable results.
        type_ = self._build_wrapped_type(field.type)
        type_ = type_
        return GraphQLField(
            type_=type_,
            description=field.description.value if field.description else None,
            args=self._make_args(field.arguments) if field.arguments else None,
            deprecation_reason=get_deprecation_reason(field),
            ast_node=field,
        )

    def build_input_field(self, value):
        # Note: While this could make assertions to get the correctly typed
        # value, that would throw immediately while type system validation
        # with validate_schema() will produce more actionable results.
        type_ = self._build_wrapped_type(value.type)
        type_ = type_
        return GraphQLInputField(
            type_=type_,
            description=value.description.value if value.description else None,
            default_value=value_from_ast(value.default_value, type_),
            ast_node=value,
        )

    @staticmethod
    def build_enum_value(value):
        return GraphQLEnumValue(
            description=value.description.value if value.description else None,
            deprecation_reason=get_deprecation_reason(value),
            ast_node=value,
        )

    def _make_schema_def(self, type_def):
        method = {
            "object_type_definition": self._make_type_def,
            "interface_type_definition": self._make_interface_def,
            "enum_type_definition": self._make_enum_def,
            "union_type_definition": self._make_union_def,
            "scalar_type_definition": self._make_scalar_def,
            "input_object_type_definition": self._make_input_object_def,
        }.get(type_def.kind)
        if not method:
            raise TypeError("Type kind '{}' not supported.".format(type_def.kind))
        return method(type_def)  # type: ignore

    def _make_type_def(self, type_def):
        interfaces = type_def.interfaces
        return GraphQLObjectType(
            name=type_def.name.value,
            description=type_def.description.value if type_def.description else None,
            fields=lambda: self._make_field_def_map(type_def),
            # While this could make early assertions to get the correctly typed
            # values, that would throw immediately while type system validation
            # with validate_schema will produce more actionable results.
            interfaces=(
                lambda: [self.build_type(ref) for ref in interfaces]
            )  # type: ignore
            if interfaces
            else [],
            ast_node=type_def,
        )

    def _make_field_def_map(self, type_def):
        fields = type_def.fields
        return (
            {field.name.value: self.build_field(field) for field in fields}
            if fields
            else {}
        )

    def _make_arg(self, value_node):
        # Note: While this could make assertions to get the correctly typed
        # value, that would throw immediately while type system validation
        # with validate_schema will produce more actionable results.
        type_ = self._build_wrapped_type(value_node.type)
        type_ = type_
        return GraphQLArgument(
            type_=type_,
            description=value_node.description.value
            if value_node.description
            else None,
            default_value=value_from_ast(value_node.default_value, type_),
            ast_node=value_node,
        )

    def _make_args(self, values):
        return {value.name.value: self._make_arg(value) for value in values}

    def _make_input_fields(self, values):
        return {value.name.value: self.build_input_field(value) for value in values}

    def _make_interface_def(self, type_def):
        return GraphQLInterfaceType(
            name=type_def.name.value,
            description=type_def.description.value if type_def.description else None,
            fields=lambda: self._make_field_def_map(type_def),
            ast_node=type_def,
        )

    def _make_enum_def(self, type_def):
        return GraphQLEnumType(
            name=type_def.name.value,
            description=type_def.description.value if type_def.description else None,
            values=self._make_value_def_map(type_def),
            ast_node=type_def,
        )

    def _make_value_def_map(self, type_def):
        return (
            {
                value.name.value: self.build_enum_value(value)
                for value in type_def.values
            }
            if type_def.values
            else {}
        )

    def _make_union_def(self, type_def):
        types = type_def.types
        return GraphQLUnionType(
            name=type_def.name.value,
            description=type_def.description.value if type_def.description else None,
            # Note: While this could make assertions to get the correctly typed
            # values below, that would throw immediately while type system
            # validation with validate_schema will get more actionable results.
            types=(lambda: [self.build_type(ref) for ref in types])  # type: ignore
            if types
            else [],
            ast_node=type_def,
        )

    @staticmethod
    def _make_scalar_def(type_def):
        return GraphQLScalarType(
            name=type_def.name.value,
            description=type_def.description.value if type_def.description else None,
            ast_node=type_def,
            serialize=lambda value: value,
        )

    def _make_input_object_def(self, type_def):
        return GraphQLInputObjectType(
            name=type_def.name.value,
            description=type_def.description.value if type_def.description else None,
            fields=(lambda: self._make_input_fields(type_def.fields))
            if type_def.fields
            else {},
            ast_node=type_def,
        )


def get_deprecation_reason(node):
    """Given a field or enum value node, get deprecation reason as string."""
    from ..execution import get_directive_values

    deprecated = get_directive_values(GraphQLDeprecatedDirective, node)
    return deprecated["reason"] if deprecated else None


def get_description(node):
    """@deprecated: Given an ast node, returns its string description."""
    try:
        # noinspection PyUnresolvedReferences
        return node.description.value  # type: ignore
    except AttributeError:
        return None


def build_schema(
    source,
    assume_valid=False,
    assume_valid_sdl=False,
    no_location=False,
    experimental_fragment_variables=False,
):
    """Build a GraphQLSchema directly from a source document."""
    return build_ast_schema(
        parse(
            source,
            no_location=no_location,
            experimental_fragment_variables=experimental_fragment_variables,
        ),
        assume_valid=assume_valid,
        assume_valid_sdl=assume_valid_sdl,
    )
