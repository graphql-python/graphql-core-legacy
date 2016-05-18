import itertools

from ...error import GraphQLError
from ...language import ast
from ...language.printer import print_ast
from ...pyutils.default_ordered_dict import DefaultOrderedDict
from ...pyutils.pair_set import PairSet
from ...type.definition import (GraphQLInterfaceType, GraphQLList,
                                GraphQLNonNull, GraphQLObjectType,
                                get_named_type, is_leaf_type)
from ...utils.type_comparators import is_equal_type
from ...utils.type_from_ast import type_from_ast
from .base import ValidationRule


class OverlappingFieldsCanBeMerged(ValidationRule):
    __slots__ = 'compared_set',

    def __init__(self, context):
        super(OverlappingFieldsCanBeMerged, self).__init__(context)
        self.compared_set = PairSet()

    def find_conflicts(self, parent_fields_are_mutually_exclusive, field_map):
        conflicts = []
        for response_name, fields in field_map.items():
            field_len = len(fields)
            if field_len <= 1:
                continue

            for field_a in fields:
                for field_b in fields:
                    conflict = self.find_conflict(
                        parent_fields_are_mutually_exclusive,
                        response_name,
                        field_a,
                        field_b
                    )
                    if conflict:
                        conflicts.append(conflict)

        return conflicts

    def find_conflict(self, parent_fields_are_mutually_exclusive, response_name, field1, field2):
        parent_type1, ast1, def1 = field1
        parent_type2, ast2, def2 = field2

        # Not a pair
        if ast1 is ast2:
            return

        # Memoize, do not report the same issue twice.
        # Note: Two overlapping ASTs could be encountered both when
        # `parentFieldsAreMutuallyExclusive` is true and is false, which could
        # produce different results (when `true` being a subset of `false`).
        # However we do not need to include this piece of information when
        # memoizing since this rule visits leaf fields before their parent fields,
        # ensuring that `parentFieldsAreMutuallyExclusive` is `false` the first
        # time two overlapping fields are encountered, ensuring that the full
        # set of validation rules are always checked when necessary.

        # if parent_type1 != parent_type2 and \
        #         isinstance(parent_type1, GraphQLObjectType) and \
        #         isinstance(parent_type2, GraphQLObjectType):
        #     return

        if self.compared_set.has(ast1, ast2):
            return

        self.compared_set.add(ast1, ast2)

        # The return type for each field.
        type1 = def1 and def1.type
        type2 = def2 and def2.type

        # If it is known that two fields could not possibly apply at the same
        # time, due to the parent types, then it is safe to permit them to diverge
        # in aliased field or arguments used as they will not present any ambiguity
        # by differing.
        # It is known that two parent types could never overlap if they are
        # different Object types. Interface or Union types might overlap - if not
        # in the current state of the schema, then perhaps in some future version,
        # thus may not safely diverge.

        fields_are_mutually_exclusive = (
            parent_fields_are_mutually_exclusive or (
                parent_type1 != parent_type2 and
                isinstance(parent_type1, GraphQLObjectType) and
                isinstance(parent_type2, GraphQLObjectType)
            )
        )

        if not fields_are_mutually_exclusive:
            name1 = ast1.name.value
            name2 = ast2.name.value

            if name1 != name2:
                return (
                    (response_name, '{} and {} are different fields'.format(name1, name2)),
                    [ast1],
                    [ast2]
                )

            if not self.same_arguments(ast1.arguments, ast2.arguments):
                return (
                    (response_name, 'they have differing arguments'),
                    [ast1],
                    [ast2]
                )

        if type1 and type2 and do_types_conflict(type1, type2):
            return (
                (response_name, 'they return conflicting types {} and {}'.format(type1, type2)),
                [ast1],
                [ast2]
            )

        subfield_map = self.get_subfield_map(ast1, type1, ast2, type2)
        if subfield_map:
            conflicts = self.find_conflicts(fields_are_mutually_exclusive, subfield_map)
            return self.subfield_conflicts(conflicts, response_name, ast1, ast2)

    def get_subfield_map(self, ast1, type1, ast2, type2):
        selection_set1 = ast1.selection_set
        selection_set2 = ast2.selection_set

        if selection_set1 and selection_set2:
            visited_fragment_names = set()

            subfield_map = self.collect_field_asts_and_defs(
                get_named_type(type1),
                selection_set1,
                visited_fragment_names
            )

            subfield_map = self.collect_field_asts_and_defs(
                get_named_type(type2),
                selection_set2,
                visited_fragment_names,
                subfield_map
            )
            return subfield_map

    def subfield_conflicts(self, conflicts, response_name, ast1, ast2):
        if conflicts:
            return (
                (response_name, [conflict[0] for conflict in conflicts]),
                tuple(itertools.chain([ast1], *[conflict[1] for conflict in conflicts])),
                tuple(itertools.chain([ast2], *[conflict[2] for conflict in conflicts]))
            )

    def leave_SelectionSet(self, node, key, parent, path, ancestors):
        # Note: we validate on the reverse traversal so deeper conflicts will be
        # caught first, for correct calculation of mutual exclusivity and for
        # clearer error messages.
        field_map = self.collect_field_asts_and_defs(
            self.context.get_parent_type(),
            node
        )

        conflicts = self.find_conflicts(False, field_map)
        if conflicts:
            for (reason_name, reason), fields1, fields2 in conflicts:
                self.context.report_error(
                    GraphQLError(
                        self.fields_conflict_message(
                            reason_name,
                            reason),
                        list(fields1) +
                        list(fields2)))

    @staticmethod
    def same_type(type1, type2):
        return is_equal_type(type1, type2)
        # return type1.is_same_type(type2)

    @staticmethod
    def same_value(value1, value2):
        return (not value1 and not value2) or print_ast(value1) == print_ast(value2)

    @classmethod
    def same_arguments(cls, arguments1, arguments2):
        # Check to see if they are empty arguments or nones. If they are, we can
        # bail out early.
        if not (arguments1 or arguments2):
            return True

        if len(arguments1) != len(arguments2):
            return False

        arguments2_values_to_arg = {a.name.value: a for a in arguments2}

        for argument1 in arguments1:
            argument2 = arguments2_values_to_arg.get(argument1.name.value)
            if not argument2:
                return False

            if not cls.same_value(argument1.value, argument2.value):
                return False

        return True

    def collect_field_asts_and_defs(self, parent_type, selection_set, visited_fragment_names=None, ast_and_defs=None):
        if visited_fragment_names is None:
            visited_fragment_names = set()

        if ast_and_defs is None:
            # An ordered dictionary is required, otherwise the error message will be out of order.
            # We need to preserve the order that the item was inserted into the dict, as that will dictate
            # in which order the reasons in the error message should show.
            # Otherwise, the error messages will be inconsistently ordered for the same AST.
            # And this can make it so that tests fail half the time, and fool a user into thinking that
            # the errors are different, when in-fact they are the same, just that the ordering of the reasons differ.
            ast_and_defs = DefaultOrderedDict(list)

        for selection in selection_set.selections:
            if isinstance(selection, ast.Field):
                field_name = selection.name.value
                field_def = None
                if isinstance(parent_type, (GraphQLObjectType, GraphQLInterfaceType)):
                    field_def = parent_type.get_fields().get(field_name)

                response_name = selection.alias.value if selection.alias else field_name
                ast_and_defs[response_name].append((parent_type, selection, field_def))

            elif isinstance(selection, ast.InlineFragment):
                type_condition = selection.type_condition
                inline_fragment_type = \
                    type_from_ast(self.context.get_schema(), type_condition) \
                    if type_condition else parent_type

                self.collect_field_asts_and_defs(
                    inline_fragment_type,
                    selection.selection_set,
                    visited_fragment_names,
                    ast_and_defs
                )

            elif isinstance(selection, ast.FragmentSpread):
                fragment_name = selection.name.value
                if fragment_name in visited_fragment_names:
                    continue

                visited_fragment_names.add(fragment_name)
                fragment = self.context.get_fragment(fragment_name)

                if not fragment:
                    continue

                self.collect_field_asts_and_defs(
                    type_from_ast(self.context.get_schema(), fragment.type_condition),
                    fragment.selection_set,
                    visited_fragment_names,
                    ast_and_defs
                )

        return ast_and_defs

    @classmethod
    def fields_conflict_message(cls, reason_name, reason):
        return (
            'Fields "{}" conflict because {}. '
            'Use different aliases on the fields to fetch both if this was '
            'intentional.'
        ).format(reason_name, cls.reason_message(reason))

    @classmethod
    def reason_message(cls, reason):
        if isinstance(reason, list):
            return ' and '.join('subfields "{}" conflict because {}'.format(reason_name, cls.reason_message(sub_reason))
                                for reason_name, sub_reason in reason)

        return reason


def do_types_conflict(type1, type2):
    if isinstance(type1, GraphQLList):
        if isinstance(type2, GraphQLList):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if isinstance(type2, GraphQLList):
        if isinstance(type1, GraphQLList):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if isinstance(type1, GraphQLNonNull):
        if isinstance(type2, GraphQLNonNull):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if isinstance(type2, GraphQLNonNull):
        if isinstance(type1, GraphQLNonNull):
            return do_types_conflict(type1.of_type, type2.of_type)
        return True

    if is_leaf_type(type1) or is_leaf_type(type2):
        return type1 != type2

    return False
