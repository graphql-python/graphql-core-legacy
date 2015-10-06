from . import rules as Rules
from ..error import GraphQLError
from ..language.ast import FragmentDefinition, FragmentSpread
from ..language.visitor import Visitor, visit
from ..type import GraphQLSchema
from ..utils.type_info import TypeInfo

specified_rules = [
    Rules.UniqueOperationNames,
    Rules.LoneAnonymousOperation,
    Rules.KnownTypeNames,
    Rules.FragmentsOnCompositeTypes,
    Rules.VariablesAreInputTypes,
    Rules.ScalarLeafs,
    Rules.FieldsOnCorrectType,
    Rules.UniqueFragmentNames,
    Rules.KnownFragmentNames,
    Rules.NoUnusedFragments,
    Rules.PossibleFragmentSpreads,
    Rules.NoFragmentCycles,
    Rules.NoUndefinedVariables,
    Rules.NoUnusedVariables,
    Rules.KnownDirectives,
    Rules.KnownArgumentNames,
    Rules.UniqueArgumentNames,
    Rules.ArgumentsOfCorrectType,
    Rules.ProvidedNonNullArguments,
    Rules.DefaultValuesOfCorrectType,
    Rules.VariablesInAllowedPosition,
    Rules.OverlappingFieldsCanBeMerged,
    Rules.UniqueInputFieldNames
]


def validate(schema, ast, rules=None):
    assert schema, 'Must provide schema'
    assert ast, 'Must provide document'
    assert isinstance(schema, GraphQLSchema)
    if rules is None:
        rules = specified_rules
    return visit_using_rules(schema, ast, rules)


def visit_using_rules(schema, ast, rules):
    type_info = TypeInfo(schema)
    context = ValidationContext(schema, ast, type_info)
    errors = []
    rules = [rule(context) for rule in rules]
    visit(ast, ValidationVisitor(rules, context, type_info, errors))
    return errors


class ValidationVisitor(Visitor):
    def __init__(self, rules, context, type_info, errors):
        self.context = context
        self.rules = rules
        self.total_rules = len(rules)
        self.type_info = type_info
        self.errors = errors
        self.ignore_children = {}

    def enter(self, node, key, parent, path, ancestors):
        self.type_info.enter(node)
        to_ignore = None
        rules_wanting_to_visit_fragment = None

        skipped = 0
        for rule in self.rules:
            if rule in self.ignore_children:
                skipped += 1
                continue

            visit_spread_fragments = getattr(rule, 'visit_spread_fragments', False)

            if isinstance(node, FragmentDefinition) and key and visit_spread_fragments:
                if to_ignore is None:
                    to_ignore = []

                to_ignore.append(rule)
                continue

            result = rule.enter(node, key, parent, path, ancestors)

            if result and is_error(result):
                append(self.errors, result)
                result = False

            if result is None and visit_spread_fragments and isinstance(node, FragmentSpread):
                if rules_wanting_to_visit_fragment is None:
                    rules_wanting_to_visit_fragment = []

                rules_wanting_to_visit_fragment.append(rule)

            if result is False:
                if to_ignore is None:
                    to_ignore = []

                to_ignore.append(rule)

        if rules_wanting_to_visit_fragment:
            fragment = self.context.get_fragment(node.name.value)

            if fragment:
                sub_visitor = ValidationVisitor(rules_wanting_to_visit_fragment, self.context, self.type_info,
                                                self.errors)
                visit(fragment, sub_visitor)

        should_skip = (len(to_ignore) if to_ignore else 0 + skipped) == self.total_rules

        if should_skip:
            self.type_info.leave(node)

        elif to_ignore:
            for rule in to_ignore:
                self.ignore_children[rule] = node

        if should_skip:
            return False

    def leave(self, node, key, parent, path, ancestors):
        for rule in self.rules:
            if rule in self.ignore_children:
                if self.ignore_children[rule] is node:
                    del self.ignore_children[rule]

                continue

            result = rule.leave(node, key, parent, path, ancestors)

            if result and is_error(result):
                append(self.errors, result)

        self.type_info.leave(node)


def is_error(value):
    if isinstance(value, list):
        return all(isinstance(item, GraphQLError) for item in value)
    return isinstance(value, GraphQLError)


def append(arr, items):
    if isinstance(items, list):
        arr.extend(items)
    else:
        arr.append(items)


class ValidationContext(object):
    def __init__(self, schema, ast, type_info):
        self._schema = schema
        self._ast = ast
        self._type_info = type_info
        self._fragments = None

    def get_schema(self):
        return self._schema

    def get_ast(self):
        return self._ast

    def get_fragment(self, name):
        fragments = self._fragments
        if fragments is None:
            self._fragments = fragments = {}
            for statement in self.get_ast().definitions:
                if isinstance(statement, FragmentDefinition):
                    fragments[statement.name.value] = statement
        return fragments.get(name)

    def get_type(self):
        return self._type_info.get_type()

    def get_parent_type(self):
        return self._type_info.get_parent_type()

    def get_input_type(self):
        return self._type_info.get_input_type()

    def get_field_def(self):
        return self._type_info.get_field_def()

    def get_directive(self):
        return self._type_info.get_directive()

    def get_argument(self):
        return self._type_info.get_argument()
