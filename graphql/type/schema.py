from functools import partial, reduce
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, cast

from ..error import GraphQLError
from ..language import ast
from .definition import (
    GraphQLInterfaceType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLUnionType,
    GraphQLInputObjectType,
    GraphQLWrappingType,
    is_abstract_type,
    is_input_object_type,
    is_interface_type,
    is_object_type,
    is_union_type,
    is_wrapping_type,
)
from .directives import GraphQLDirective, specified_directives, is_directive
from .introspection import introspection_types

__all__ = ["GraphQLSchema", "is_schema"]


TypeMap = Dict[str, GraphQLNamedType]


def is_schema(schema):
    """Test if the given value is a GraphQL schema."""
    return isinstance(schema, GraphQLSchema)


class GraphQLSchema:
    """Schema Definition

    A Schema is created by supplying the root types of each type of operation,
    query and mutation (optional). A schema definition is then supplied to the
    validator and executor.

    Example::

        const MyAppSchema = GraphQLSchema(
          query=MyAppQueryRootType,
          mutation=MyAppMutationRootType)

    Note: If a list of `directives` are provided to GraphQLSchema, that will be
    the exact list of directives represented and allowed. If `directives` is
    not provided, then a default set of the specified directives (e.g. @include
    and @skip) will be used. If you wish to provide *additional* directives to
    these specified directives, you must explicitly declare them. Example::

        const MyAppSchema = GraphQLSchema(
          ...
          directives=specifiedDirectives + [myCustomDirective])
    """

    def __init__(
        self,
        query=None,
        mutation=None,
        subscription=None,
        types=None,
        directives=None,
        ast_node=None,
        extension_ast_nodes=None,
        assume_valid=False,
    ):
        """Initialize GraphQL schema.

        If this schema was built from a source known to be valid, then it may
        be marked with assume_valid to avoid an additional type system
        validation. Otherwise check for common mistakes during construction
        to produce clear and early error messages.
        """
        if assume_valid:
            # If this schema was built from a source known to be valid,
            # then it may be marked with assume_valid to avoid an additional
            # type system validation.
            self._validation_errors = []
        else:
            # Otherwise check for common mistakes during construction to
            # produce clear and early error messages.
            if types is None:
                types = []
            elif isinstance(types, tuple):
                types = list(types)
            if not isinstance(types, list):
                raise TypeError("Schema types must be a list/tuple.")
            if isinstance(directives, tuple):
                directives = list(directives)
            if directives is not None and not isinstance(directives, list):
                raise TypeError("Schema directives must be a list/tuple.")
            self._validation_errors = None

        self.query_type = query
        self.mutation_type = mutation
        self.subscription_type = subscription
        # Provide specified directives (e.g. @include and @skip) by default
        self.directives = list(directives or specified_directives)
        self.ast_node = ast_node
        self.extension_ast_nodes = (
            tuple(extension_ast_nodes)
            if extension_ast_nodes
            else None
        )

        # Build type map now to detect any errors within this schema.
        initial_types = [query, mutation, subscription, introspection_types["__Schema"]]
        if types:
            initial_types.extend(types)

        # Keep track of all types referenced within the schema.
        type_map = {}
        # First by deeply visiting all initial types.
        type_map = type_map_reduce(initial_types, type_map)
        # Then by deeply visiting all directive types.
        type_map = type_map_directive_reduce(self.directives, type_map)
        # Storing the resulting map for reference by the schema
        self.type_map = type_map

        self._possible_type_map = {}

        # Keep track of all implementations by interface name.
        self._implementations = {}
        setdefault = self._implementations.setdefault
        for type_ in self.type_map.values():
            if is_object_type(type_):
                type_ = type_
                for interface in type_.interfaces:
                    if is_interface_type(interface):
                        setdefault(interface.name, []).append(type_)
            elif is_abstract_type(type_):
                setdefault(type_.name, [])

    def get_type(self, name):
        return self.type_map.get(name)

    def get_possible_types(self, abstract_type):
        """Get list of all possible concrete types for given abstract type."""
        if is_union_type(abstract_type):
            abstract_type = abstract_type
            return abstract_type.types
        return self._implementations[abstract_type.name]

    def is_possible_type(self, abstract_type, possible_type):
        """Check whether a concrete type is possible for an abstract type."""
        possible_type_map = self._possible_type_map
        try:
            possible_type_names = possible_type_map[abstract_type.name]
        except KeyError:
            possible_types = self.get_possible_types(abstract_type)
            possible_type_names = {type_.name for type_ in possible_types}
            possible_type_map[abstract_type.name] = possible_type_names
        return possible_type.name in possible_type_names

    def get_directive(self, name):
        for directive in self.directives:
            if directive.name == name:
                return directive
        return None

    @property
    def validation_errors(self):
        return self._validation_errors


def type_map_reducer(map_, type_=None):
    """Reducer function for creating the type map from given types."""
    if not type_:
        return map_
    if is_wrapping_type(type_):
        return type_map_reducer(
            map_, cast(GraphQLWrappingType[GraphQLNamedType], type_).of_type
        )
    name = type_.name
    if name in map_:
        if map_[name] is not type_:
            raise TypeError(
                "Schema must contain unique named types but contains multiple"
                " types named {!r}.".format(name)
            )
        return map_
    map_[name] = type_

    if is_union_type(type_):
        type_ = type_
        map_ = type_map_reduce(type_.types, map_)

    if is_object_type(type_):
        type_ = type_
        map_ = type_map_reduce(type_.interfaces, map_)

    if is_object_type(type_) or is_interface_type(type_):
        for field in cast(GraphQLInterfaceType, type_).fields.values():
            args = field.args
            if args:
                types = [arg.type for arg in args.values()]
                map_ = type_map_reduce(types, map_)
            map_ = type_map_reducer(map_, field.type)

    if is_input_object_type(type_):
        for field in cast(GraphQLInputObjectType, type_).fields.values():
            map_ = type_map_reducer(map_, field.type)

    return map_


def type_map_directive_reducer(map_, directive=None):
    """Reducer function for creating the type map from given directives."""
    # Directives are not validated until validate_schema() is called.
    if not is_directive(directive):
        return map_
    return reduce(
        lambda prev_map, arg: type_map_reducer(prev_map, arg.type),  # type: ignore
        directive.args.values(),
        map_,
    )  # type: ignore


# Reduce functions for type maps:
type_map_reduce = partial(reduce, type_map_reducer)
type_map_directive_reduce = partial(reduce, type_map_directive_reducer)
