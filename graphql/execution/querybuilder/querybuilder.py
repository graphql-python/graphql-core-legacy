# -*- coding: utf-8 -*-
from ...error import GraphQLError
from ...language import ast
from ...pyutils.default_ordered_dict import DefaultOrderedDict
from ...type.definition import GraphQLInterfaceType, GraphQLUnionType
from ...type.directives import GraphQLIncludeDirective, GraphQLSkipDirective
from ...type.introspection import (SchemaMetaFieldDef, TypeMetaFieldDef,
                                  TypeNameMetaFieldDef)
from ...utils.type_from_ast import type_from_ast
from ..values import get_argument_values, get_variable_values

from ...type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
                     GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
                     GraphQLSchema, GraphQLUnionType)
from ..base import (ExecutionContext, ExecutionResult, ResolveInfo, Undefined,
                    collect_fields, default_resolve_fn, get_field_def,
                    get_operation_root_type)

from .fragment import Fragment


def get_base_type(type):
    if isinstance(type, (GraphQLList, GraphQLNonNull)):
        return get_base_type(type.of_type)
    return type


class QueryBuilder(object):

    __slots__ = 'schema', 'operations', 'fragments'

    def __init__(self, schema, document_ast):
        operations = {}
        fragments = {}

        for definition in document_ast.definitions:
            if isinstance(definition, ast.OperationDefinition):
                operation_name  = definition.name.value
                operations[operation_name] = definition

            elif isinstance(definition, ast.FragmentDefinition):
                fragment_name = definition.name.value
                fragments[fragment_name] = definition

            else:
                raise GraphQLError(
                    u'GraphQL cannot execute a request containing a {}.'.format(definition.__class__.__name__),
                    definition
                )

        if not operations:
            raise GraphQLError('Must provide an operation.')

        self.fragments = fragments
        self.schema = schema
        self.operations = {}

        for operation_name, operation in operations.items():
            self.operations[operation_name] = fragment_operation(self.schema, operation)

    def get_operation_fragment(self, operation_name):
        return self.operations[operation_name]


def fragment_operation(schema, operation):
    field_asts = operation.selection_set.selections
    root_type = get_operation_root_type(schema, operation)
    execute_serially = operation.operation == 'mutation'
    return generate_fragment(root_type, field_asts, execute_serially)


def generate_fragment(type, field_asts, execute_serially=False):
    field_fragments = {}
    for field_ast in field_asts:
        field_name = field_ast.name.value
        field_def = type.fields[field_name]
        field_base_type = get_base_type(field_def.type)
        if not isinstance(field_base_type, GraphQLObjectType):
            continue
        field_fragments[field_name] = generate_fragment(field_base_type, field_ast.selection_set.selections)

    return Fragment(
        type,
        field_asts,
        field_fragments,
        execute_serially=execute_serially
    )


def build_query(schema, document_ast):
    static_context = QueryBuilder(schema, document_ast)
