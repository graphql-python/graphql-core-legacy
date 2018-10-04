import json
from typing import cast, Callable, Dict, List, Sequence

from ..error import INVALID
from ..language import DirectiveLocation, parse_value
from ..type import (
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLType,
    GraphQLUnionType,
    TypeKind,
    assert_interface_type,
    assert_nullable_type,
    assert_object_type,
    introspection_types,
    is_input_type,
    is_output_type,
    specified_scalar_types,
)
from ..pyutils import OrderedDict
from .value_from_ast import value_from_ast

__all__ = ["build_client_schema"]


def build_client_schema(introspection, assume_valid=False):
    """Build a GraphQLSchema for use by client tools.

    Given the result of a client running the introspection query, creates and
    returns a GraphQLSchema instance which can be then used with all
    graphql-core tools, but cannot be used to execute a query, as
    introspection does not represent the "resolver", "parse" or "serialize"
    functions or any other server-internal mechanisms.

    This function expects a complete introspection result. Don't forget to
    check the "errors" field of a server response before calling this function.
    """
    # Get the schema from the introspection result.
    schema_introspection = introspection["__schema"]

    # Converts the list of types into a dict based on the type names.
    type_introspection_map = OrderedDict(
        ((type_["name"], type_) for type_ in schema_introspection["types"])
    )

    # A cache to use to store the actual GraphQLType definition objects by
    # name. Initialize to the GraphQL built in scalars. All functions below are
    # inline so that this type def cache is within the scope of the closure.
    type_def_cache = dict(specified_scalar_types, **introspection_types)

    # Given a type reference in introspection, return the GraphQLType instance.
    # preferring cached instances before building new instances.
    def get_type(type_ref):
        kind = type_ref.get("kind")
        if kind == TypeKind.LIST.name:
            item_ref = type_ref.get("ofType")
            if not item_ref:
                raise TypeError("Decorated type deeper than introspection query.")
            return GraphQLList(get_type(item_ref))
        elif kind == TypeKind.NON_NULL.name:
            nullable_ref = type_ref.get("ofType")
            if not nullable_ref:
                raise TypeError("Decorated type deeper than introspection query.")
            nullable_type = get_type(nullable_ref)
            return GraphQLNonNull(assert_nullable_type(nullable_type))
        name = type_ref.get("name")
        if not name:
            raise TypeError("Unknown type reference: {!r}".format(type_ref))
        return get_named_type(name)

    def get_named_type(type_name):
        cached_type = type_def_cache.get(type_name)
        if cached_type:
            return cached_type
        type_introspection = type_introspection_map.get(type_name)
        if not type_introspection:
            raise TypeError(
                (
                    "Invalid or incomplete schema, unknown type: {}."
                    " Ensure that a full introspection query is used in order"
                    " to build a client schema."
                ).format(type_name)
            )
        type_def = build_type(type_introspection)
        type_def_cache[type_name] = type_def
        return type_def

    def get_input_type(type_ref):
        input_type = get_type(type_ref)
        if not is_input_type(input_type):
            raise TypeError("Introspection must provide input type for arguments.")
        return input_type

    def get_output_type(type_ref):
        output_type = get_type(type_ref)
        if not is_output_type(output_type):
            raise TypeError("Introspection must provide output type for fields.")
        return output_type

    def get_object_type(type_ref):
        object_type = get_type(type_ref)
        return assert_object_type(object_type)

    def get_interface_type(type_ref):
        interface_type = get_type(type_ref)
        return assert_interface_type(interface_type)

    # Given a type's introspection result, construct the correct
    # GraphQLType instance.
    def build_type(type_):
        if type_ and "name" in type_ and "kind" in type_:
            builder = type_builders.get(type_["kind"])
            if builder:
                return builder(type_)
        raise TypeError(
            "Invalid or incomplete introspection result."
            " Ensure that a full introspection query is used in order"
            " to build a client schema: {!r}".format(type_)
        )

    def build_scalar_def(scalar_introspection):
        return GraphQLScalarType(
            name=scalar_introspection["name"],
            description=scalar_introspection.get("description"),
            serialize=lambda value: value,
        )

    def build_object_def(object_introspection):
        interfaces = object_introspection.get("interfaces")
        if interfaces is None:
            raise TypeError(
                "Introspection result missing interfaces:"
                " {}".format(json.dumps(object_introspection))
            )
        return GraphQLObjectType(
            name=object_introspection["name"],
            description=object_introspection.get("description"),
            interfaces=lambda: [
                get_interface_type(interface) for interface in interfaces
            ],
            fields=lambda: build_field_def_map(object_introspection),
        )

    def build_interface_def(interface_introspection):
        return GraphQLInterfaceType(
            name=interface_introspection["name"],
            description=interface_introspection.get("description"),
            fields=lambda: build_field_def_map(interface_introspection),
        )

    def build_union_def(union_introspection):
        possible_types = union_introspection.get("possibleTypes")
        if possible_types is None:
            raise TypeError(
                "Introspection result missing possibleTypes:"
                " {!r}".format(union_introspection)
            )
        return GraphQLUnionType(
            name=union_introspection["name"],
            description=union_introspection.get("description"),
            types=lambda: [get_object_type(type_) for type_ in possible_types],
        )

    def build_enum_def(enum_introspection):
        if enum_introspection.get("enumValues") is None:
            raise TypeError(
                "Introspection result missing enumValues:"
                " {!r}".format(enum_introspection)
            )
        return GraphQLEnumType(
            name=enum_introspection["name"],
            description=enum_introspection.get("description"),
            values=OrderedDict(
                (
                    (
                        value_introspect["name"],
                        GraphQLEnumValue(
                            description=value_introspect.get("description"),
                            deprecation_reason=value_introspect.get(
                                "deprecationReason"
                            ),
                        ),
                    )
                    for value_introspect in enum_introspection["enumValues"]
                )
            ),
        )

    def build_input_object_def(input_object_introspection):
        if input_object_introspection.get("inputFields") is None:
            raise TypeError(
                "Introspection result missing inputFields:"
                " {!r}".format(input_object_introspection)
            )
        return GraphQLInputObjectType(
            name=input_object_introspection["name"],
            description=input_object_introspection.get("description"),
            fields=lambda: build_input_value_def_map(
                input_object_introspection["inputFields"]
            ),
        )

    type_builders = {
        TypeKind.SCALAR.name: build_scalar_def,
        TypeKind.OBJECT.name: build_object_def,
        TypeKind.INTERFACE.name: build_interface_def,
        TypeKind.UNION.name: build_union_def,
        TypeKind.ENUM.name: build_enum_def,
        TypeKind.INPUT_OBJECT.name: build_input_object_def,
    }

    def build_field(field_introspection):
        if field_introspection.get("args") is None:
            raise TypeError(
                "Introspection result missing field args:"
                " {!r}".format(field_introspection)
            )
        return GraphQLField(
            get_output_type(field_introspection["type"]),
            args=build_arg_value_def_map(field_introspection["args"]),
            description=field_introspection.get("description"),
            deprecation_reason=field_introspection.get("deprecationReason"),
        )

    def build_field_def_map(type_introspection):
        if type_introspection.get("fields") is None:
            raise TypeError(
                "Introspection result missing fields:"
                " {!r}".format(type_introspection)
            )
        return OrderedDict(
            (
                (field_introspection["name"], build_field(field_introspection))
                for field_introspection in type_introspection["fields"]
            )
        )

    def build_arg_value(arg_introspection):
        type_ = get_input_type(arg_introspection["type"])
        default_value = arg_introspection.get("defaultValue")
        default_value = (
            INVALID
            if default_value is None
            else value_from_ast(parse_value(default_value), type_)
        )
        return GraphQLArgument(
            type_,
            default_value=default_value,
            description=arg_introspection.get("description"),
        )

    def build_arg_value_def_map(arg_introspections):
        return OrderedDict(
            (
                (
                    input_value_introspection["name"],
                    build_arg_value(input_value_introspection),
                )
                for input_value_introspection in arg_introspections
            )
        )

    def build_input_value(input_value_introspection):
        type_ = get_input_type(input_value_introspection["type"])
        default_value = input_value_introspection.get("defaultValue")
        default_value = (
            INVALID
            if default_value is None
            else value_from_ast(parse_value(default_value), type_)
        )
        return GraphQLInputField(
            type_,
            default_value=default_value,
            description=input_value_introspection.get("description"),
        )

    def build_input_value_def_map(input_value_introspections):
        return OrderedDict(
            (
                (
                    input_value_introspection["name"],
                    build_input_value(input_value_introspection),
                )
                for input_value_introspection in input_value_introspections
            )
        )

    def build_directive(directive_introspection):
        if directive_introspection.get("args") is None:
            raise TypeError(
                "Introspection result missing directive args:"
                " {!r}".format(directive_introspection)
            )
        if directive_introspection.get("locations") is None:
            raise TypeError(
                "Introspection result missing directive locations:"
                " {}".format(json.dumps(directive_introspection))
            )
        return GraphQLDirective(
            name=directive_introspection["name"],
            description=directive_introspection.get("description"),
            locations=list(directive_introspection.get("locations")),
            args=build_arg_value_def_map(directive_introspection["args"]),
        )

    # Iterate through all types, getting the type definition for each, ensuring
    # that any type not directly referenced by a field will get created.
    types = [get_named_type(name) for name in type_introspection_map]

    # Get the root Query, Mutation, and Subscription types.

    query_type_ref = schema_introspection.get("queryType")
    query_type = get_object_type(query_type_ref) if query_type_ref else None
    mutation_type_ref = schema_introspection.get("mutationType")
    mutation_type = get_object_type(mutation_type_ref) if mutation_type_ref else None
    subscription_type_ref = schema_introspection.get("subscriptionType")
    subscription_type = (
        get_object_type(subscription_type_ref) if subscription_type_ref else None
    )

    # Get the directives supported by Introspection, assuming empty-set if
    # directives were not queried for.
    directive_introspections = schema_introspection.get("directives")
    directives = (
        [
            build_directive(directive_introspection)
            for directive_introspection in directive_introspections
        ]
        if directive_introspections
        else []
    )

    return GraphQLSchema(
        query=query_type,
        mutation=mutation_type,
        subscription=subscription_type,
        types=types,
        directives=directives,
        assume_valid=assume_valid,
    )
