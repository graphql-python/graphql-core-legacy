from ...error import GraphQLError
from ...type.definition import (
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLUnionType,
)
from ...utils.type_from_ast import type_from_ast
from .base import ValidationRule


class PossibleFragmentSpreads(ValidationRule):
    def enter_InlineFragment(self, node, key, parent, path, ancestors):
        frag_type = self.context.get_type()
        parent_type = self.context.get_parent_type()
        if frag_type and parent_type and not self.do_types_overlap(frag_type, parent_type):
            self.context.report_error(GraphQLError(
                self.type_incompatible_anon_spread_message(parent_type, frag_type),
                [node]
            ))

    def enter_FragmentSpread(self, node, key, parent, path, ancestors):
        frag_name = node.name.value
        frag_type = self.get_fragment_type(self.context, frag_name)
        parent_type = self.context.get_parent_type()
        if frag_type and parent_type and not self.do_types_overlap(frag_type, parent_type):
            self.context.report_error(GraphQLError(
                self.type_incompatible_spread_message(frag_name, parent_type, frag_type),
                [node]
            ))

    @staticmethod
    def get_fragment_type(context, name):
        frag = context.get_fragment(name)
        return frag and type_from_ast(context.get_schema(), frag.type_condition)

    @staticmethod
    def do_types_overlap(t1, t2):
        if t1 == t2:
            return True
        if isinstance(t1, GraphQLObjectType):
            if isinstance(t2, GraphQLObjectType):
                return False
            return t1 in t2.get_possible_types()
        if isinstance(t1, GraphQLInterfaceType) or isinstance(t1, GraphQLUnionType):
            if isinstance(t2, GraphQLObjectType):
                return t2 in t1.get_possible_types()

            t1_type_names = {possible_type.name: possible_type for possible_type in t1.get_possible_types()}
            return any(t.name in t1_type_names for t in t2.get_possible_types())

    @staticmethod
    def type_incompatible_spread_message(frag_name, parent_type, frag_type):
        return 'Fragment {} cannot be spread here as objects of type {} can never be of type {}'.format(frag_name,
                                                                                                        parent_type,
                                                                                                        frag_type)

    @staticmethod
    def type_incompatible_anon_spread_message(parent_type, frag_type):
        return 'Fragment cannot be spread here as objects of type {} can never be of type {}'.format(parent_type,
                                                                                                     frag_type)
