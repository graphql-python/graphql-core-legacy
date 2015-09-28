import itertools
from ..error import GraphQLError
from ..language import ast
from ..language.printer import print_ast
from ..language.visitor import Visitor, visit
from ..type.definition import (
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLUnionType,
    get_named_type,
    is_composite_type,
    is_input_type,
    is_leaf_type,
)
from ..utils import is_valid_literal_value, type_from_ast
from .utils import DefaultOrderedDict, PairSet


class ValidationRule(Visitor):
    def __init__(self, context):
        self.context = context


class UniqueOperationNames(ValidationRule):
    def __init__(self, context):
        super(UniqueOperationNames, self).__init__(context)
        self.known_operation_names = {}

    def enter_OperationDefinition(self, node, *args):
        operation_name = node.name
        if not operation_name:
            return

        if operation_name.value in self.known_operation_names:
            return GraphQLError(
                self.duplicate_operation_name_message(operation_name.value),
                [self.known_operation_names[operation_name.value], operation_name]
            )

        self.known_operation_names[operation_name.value] = operation_name

    @staticmethod
    def duplicate_operation_name_message(operation_name):
        return 'There can only be one operation named "{}".'.format(operation_name)


class LoneAnonymousOperation(ValidationRule):
    operation_count = 0

    def __init__(self, context):
        super(LoneAnonymousOperation, self).__init__(context)

    def enter_Document(self, node, *args):
        self.operation_count = \
            sum(1 for definition in node.definitions if isinstance(definition, ast.OperationDefinition))

    def enter_OperationDefinition(self, node, *args):
        if not node.name and self.operation_count > 1:
            return GraphQLError(self.anonymous_operation_not_alone_message(), [node])

    @staticmethod
    def anonymous_operation_not_alone_message():
        return 'This anonymous operation must be the only defined operation.'


class KnownTypeNames(ValidationRule):
    def enter_NamedType(self, node, *args):
        type_name = node.name.value
        type = self.context.get_schema().get_type(type_name)

        if not type:
            return GraphQLError(self.unknown_type_message(type_name), [node])

    @staticmethod
    def unknown_type_message(type):
        return 'Unknown type "{}".'.format(type)


class FragmentsOnCompositeTypes(ValidationRule):
    def enter_InlineFragment(self, node, *args):
        type = self.context.get_type()

        if type and not is_composite_type(type):
            return GraphQLError(
                self.inline_fragment_on_non_composite_error_message(print_ast(node.type_condition)),
                [node.type_condition]
            )

    def enter_FragmentDefinition(self, node, *args):
        type = self.context.get_type()

        if type and not is_composite_type(type):
            return GraphQLError(
                self.fragment_on_non_composite_error_message(node.name.value, print_ast(node.type_condition)),
                [node.type_condition]
            )

    @staticmethod
    def inline_fragment_on_non_composite_error_message(type):
        return 'Fragment cannot condition on non composite type "{}".'.format(type)

    @staticmethod
    def fragment_on_non_composite_error_message(frag_name, type):
        return 'Fragment "{}" cannot condition on non composite type "{}".'.format(frag_name, type)


class VariablesAreInputTypes(ValidationRule):
    def enter_VariableDefinition(self, node, *args):
        type = type_from_ast(self.context.get_schema(), node.type)

        if type and not is_input_type(type):
            return GraphQLError(
                self.non_input_type_on_variable_message(node.variable.name.value, print_ast(node.type)),
                [node.type]
            )

    @staticmethod
    def non_input_type_on_variable_message(variable_name, type_name):
        return 'Variable "${}" cannot be non-input type "{}".'.format(variable_name, type_name)


class ScalarLeafs(ValidationRule):
    def enter_Field(self, node, *args):
        type = self.context.get_type()

        if not type:
            return

        if is_leaf_type(type):
            if node.selection_set:
                return GraphQLError(
                    self.no_subselection_allowed_message(node.name.value, type),
                    [node.selection_set]
                )

        elif not node.selection_set:
            return GraphQLError(
                self.required_subselection_message(node.name.value, type),
                [node]
            )

    @staticmethod
    def no_subselection_allowed_message(field, type):
        return 'Field "{}" of type "{}" must not have a sub selection.'.format(field, type)

    @staticmethod
    def required_subselection_message(field, type):
        return 'Field "{}" of type "{}" must have a sub selection.'.format(field, type)


class FieldsOnCorrectType(ValidationRule):
    def enter_Field(self, node, *args):
        type = self.context.get_parent_type()
        if not type:
            return

        field_def = self.context.get_field_def()
        if not field_def:
            return GraphQLError(
                self.undefined_field_message(node.name.value, type.name),
                [node]
            )

    @staticmethod
    def undefined_field_message(field_name, type):
        return 'Cannot query field "{}" on "{}".'.format(field_name, type)


class UniqueFragmentNames(ValidationRule):
    def __init__(self, context):
        super(UniqueFragmentNames, self).__init__(context)
        self.known_fragment_names = {}

    def enter_FragmentDefinition(self, node, *args):
        fragment_name = node.name.value
        if fragment_name in self.known_fragment_names:
            return GraphQLError(
                self.duplicate_fragment_name_message(fragment_name),
                [self.known_fragment_names[fragment_name], node.name]
            )

        self.known_fragment_names[fragment_name] = node.name

    @staticmethod
    def duplicate_fragment_name_message(field):
        return 'There can only be one fragment named "{}".'.format(field)


class KnownFragmentNames(ValidationRule):
    def enter_FragmentSpread(self, node, *args):
        fragment_name = node.name.value
        fragment = self.context.get_fragment(fragment_name)

        if not fragment:
            return GraphQLError(
                self.unknown_fragment_message(fragment_name),
                [node.name]
            )

    @staticmethod
    def unknown_fragment_message(fragment_name):
        return 'Unknown fragment "{}".'.format(fragment_name)


class NoUnusedFragments(ValidationRule):
    def __init__(self, context):
        super(NoUnusedFragments, self).__init__(context)
        self.fragment_definitions = []
        self.spreads_within_operation = []
        self.fragment_adjacencies = {}
        self.spread_names = set()

    def enter_OperationDefinition(self, *args):
        self.spread_names = set()
        self.spreads_within_operation.append(self.spread_names)

    def enter_FragmentDefinition(self, node, *args):
        self.fragment_definitions.append(node)
        self.spread_names = set()
        self.fragment_adjacencies[node.name.value] = self.spread_names

    def enter_FragmentSpread(self, node, *args):
        self.spread_names.add(node.name.value)

    def leave_Document(self, *args):
        fragment_names_used = set()

        def reduce_spread_fragments(spreads):
            for fragment_name in spreads:
                if fragment_name in fragment_names_used:
                    continue

                fragment_names_used.add(fragment_name)
                if fragment_name in self.fragment_adjacencies:
                    reduce_spread_fragments(self.fragment_adjacencies[fragment_name])

        for spreads in self.spreads_within_operation:
            reduce_spread_fragments(spreads)

        errors = [
            GraphQLError(
                self.unused_fragment_message(fragment_definition.name.value),
                [fragment_definition]
            )
            for fragment_definition in self.fragment_definitions
            if fragment_definition.name.value not in fragment_names_used
        ]

        if errors:
            return errors

    @staticmethod
    def unused_fragment_message(fragment_name):
        return 'Fragment "{}" is never used.'.format(fragment_name)


class PossibleFragmentSpreads(ValidationRule):
    def enter_InlineFragment(self, node, *args):
        frag_type = self.context.get_type()
        parent_type = self.context.get_parent_type()
        if frag_type and parent_type and not self.do_types_overlap(frag_type, parent_type):
            return GraphQLError(
                self.type_incompatible_anon_spread_message(parent_type, frag_type),
                [node]
            )

    def enter_FragmentSpread(self, node, *args):
        frag_name = node.name.value
        frag_type = self.get_fragment_type(self.context, frag_name)
        parent_type = self.context.get_parent_type()
        if frag_type and parent_type and not self.do_types_overlap(frag_type, parent_type):
            return GraphQLError(
                self.type_incompatible_spread_message(frag_name, parent_type, frag_type),
                [node]
            )

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


class NoFragmentCycles(ValidationRule):
    def __init__(self, context):
        super(NoFragmentCycles, self).__init__(context)
        self.spreads_in_fragment = {
            node.name.value: self.gather_spreads(node)
            for node in context.get_ast().definitions
            if isinstance(node, ast.FragmentDefinition)
        }
        self.known_to_lead_to_cycle = set()

    def enter_FragmentDefinition(self, node, *args):
        errors = []
        initial_name = node.name.value
        spread_path = []

        # This will convert the ast.FragmentDefinition to something that we can add
        # to a set. Otherwise we get a `unhashable type: dict` error.
        # This makes it so that we can define a way to uniquely identify a FragmentDefinition
        # within a set.
        fragment_node_to_hashable = lambda fs: (fs.loc['start'], fs.loc['end'], fs.name.value)

        def detect_cycle_recursive(fragment_name):
            spread_nodes = self.spreads_in_fragment[fragment_name]

            for spread_node in spread_nodes:
                if fragment_node_to_hashable(spread_node) in self.known_to_lead_to_cycle:
                    continue

                if spread_node.name.value == initial_name:
                    cycle_path = spread_path + [spread_node]
                    self.known_to_lead_to_cycle |= set(map(fragment_node_to_hashable, cycle_path))

                    errors.append(GraphQLError(
                        self.cycle_error_message(initial_name, [s.name.value for s in spread_path]),
                        cycle_path
                    ))
                    continue

                if any(spread is spread_node for spread in spread_path):
                    continue

                spread_path.append(spread_node)
                detect_cycle_recursive(spread_node.name.value)
                spread_path.pop()

        detect_cycle_recursive(initial_name)
        if errors:
            return errors

    @staticmethod
    def cycle_error_message(fragment_name, spread_names):
        via = ' via {}'.format(', '.join(spread_names)) if spread_names else ''
        return 'Cannot spread fragment "{}" within itself{}.'.format(fragment_name, via)

    @classmethod
    def gather_spreads(cls, node):
        visitor = cls.CollectFragmentSpreadNodesVisitor()
        visit(node, visitor)
        return visitor.collect_fragment_spread_nodes()

    class CollectFragmentSpreadNodesVisitor(Visitor):
        def __init__(self):
            self.spread_nodes = []

        def enter_FragmentSpread(self, node, *args):
            self.spread_nodes.append(node)

        def collect_fragment_spread_nodes(self):
            return self.spread_nodes


class NoUndefinedVariables(ValidationRule):
    visit_spread_fragments = True
    operation = None

    def __init__(self, context):
        self.visited_fragment_names = set()
        self.defined_variable_names = set()
        super(NoUndefinedVariables, self).__init__(context)

    @staticmethod
    def undefined_var_message(var_name):
        return 'Variable "${}" is not defined.'.format(var_name)

    @staticmethod
    def undefined_var_by_op_message(var_name, op_name):
        return 'Variable "${}" is not defined by operation "{}".'.format(
            var_name, op_name
        )

    def enter_OperationDefinition(self, node, *args):
        self.operation = node
        self.visited_fragment_names = set()
        self.defined_variable_names = set()

    def enter_VariableDefinition(self, node, *args):
        self.defined_variable_names.add(node.variable.name.value)

    def enter_Variable(self, variable, key, parent, path, ancestors):
        var_name = variable.name.value
        if var_name not in self.defined_variable_names:
            within_fragment = any(isinstance(node, ast.FragmentDefinition) for node in ancestors)
            if within_fragment and self.operation and self.operation.name:
                return GraphQLError(
                    self.undefined_var_by_op_message(var_name, self.operation.name.value),
                    [variable, self.operation]
                )

            return GraphQLError(
                self.undefined_var_message(var_name),
                [variable]
            )

    def enter_FragmentSpread(self, spread_ast, *args):
        if spread_ast.name.value in self.visited_fragment_names:
            return False

        self.visited_fragment_names.add(spread_ast.name.value)


class NoUnusedVariables(ValidationRule):
    visited_fragment_names = None
    variable_definitions = None
    variable_name_used = None
    visit_spread_fragments = True

    def __init__(self, context):
        super(NoUnusedVariables, self).__init__(context)

    def enter_OperationDefinition(self, *args):
        self.visited_fragment_names = set()
        self.variable_definitions = []
        self.variable_name_used = set()

    def leave_OperationDefinition(self, *args):
        errors = [
            GraphQLError(
                self.unused_variable_message(variable_definition.variable.name.value),
                [variable_definition]
            )
            for variable_definition in self.variable_definitions
            if variable_definition.variable.name.value not in self.variable_name_used
        ]

        if errors:
            return errors

    def enter_VariableDefinition(self, node, *args):
        if self.variable_definitions is not None:
            self.variable_definitions.append(node)

        return False

    def enter_Variable(self, node, *args):
        if self.variable_name_used is not None:
            self.variable_name_used.add(node.name.value)

    def enter_FragmentSpread(self, node, *args):
        if self.visited_fragment_names is not None:
            spread_name = node.name.value
            if spread_name in self.visited_fragment_names:
                return False

            self.visited_fragment_names.add(spread_name)

    @staticmethod
    def unused_variable_message(variable_name):
        return 'Variable "${}" is never used.'.format(variable_name)


class KnownDirectives(ValidationRule):
    def enter_Directive(self, node, key, parent, path, ancestors):
        directive_def = next((
            definition for definition in self.context.get_schema().get_directives()
            if definition.name == node.name.value
        ), None)

        if not directive_def:
            return GraphQLError(
                self.unknown_directive_message(node.name.value),
                [node]
            )

        applied_to = ancestors[-1]

        if isinstance(applied_to, ast.OperationDefinition) and not directive_def.on_operation:
            return GraphQLError(
                self.misplaced_directive_message(node.name.value, 'operation'),
                [node]
            )

        if isinstance(applied_to, ast.Field) and not directive_def.on_field:
            return GraphQLError(
                self.misplaced_directive_message(node.name.value, 'field'),
                [node]
            )

        if (isinstance(applied_to, (ast.FragmentSpread, ast.InlineFragment, ast.FragmentDefinition)) and
                not directive_def.on_fragment):
            return GraphQLError(
                self.misplaced_directive_message(node.name.value, 'fragment'),
                [node]
            )

    @staticmethod
    def unknown_directive_message(directive_name):
        return 'Unknown directive "{}".'.format(directive_name)

    @staticmethod
    def misplaced_directive_message(directive_name, placement):
        return 'Directive "{}" may not be used on "{}".'.format(directive_name, placement)


class KnownArgumentNames(ValidationRule):
    def enter_Argument(self, node, key, parent, path, ancestors):
        argument_of = ancestors[-1]

        if isinstance(argument_of, ast.Field):
            field_def = self.context.get_field_def()
            if not field_def:
                return

            field_arg_def = next((arg for arg in field_def.args if arg.name == node.name.value), None)

            if not field_arg_def:
                parent_type = self.context.get_parent_type()
                assert parent_type
                return GraphQLError(
                    self.unknown_arg_message(node.name.value, field_def.name, parent_type.name),
                    [node]
                )

        elif isinstance(argument_of, ast.Directive):
            directive = self.context.get_directive()
            if not directive:
                return

            directive_arg_def = next((arg for arg in directive.args if arg.name == node.name.value), None)

            if not directive_arg_def:
                return GraphQLError(
                    self.unknown_directive_arg_message(node.name.value, directive.name),
                    [node]
                )

    @staticmethod
    def unknown_arg_message(arg_name, field_name, type):
        return 'Unknown argument "{}" on field "{}" of type "{}".'.format(arg_name, field_name, type)

    @staticmethod
    def unknown_directive_arg_message(arg_name, directive_name):
        return 'Unknown argument "{}" on directive "@{}".'.format(arg_name, directive_name)


class UniqueArgumentNames(ValidationRule):
    def __init__(self, context):
        super(UniqueArgumentNames, self).__init__(context)
        self.known_arg_names = {}

    def enter_Field(self, *args):
        self.known_arg_names = {}

    def enter_Directive(self, *args):
        self.known_arg_names = {}

    def enter_Argument(self, node, *args):
        arg_name = node.name.value

        if arg_name in self.known_arg_names:
            return GraphQLError(
                self.duplicate_arg_message(arg_name),
                [self.known_arg_names[arg_name], node.name]
            )

        self.known_arg_names[arg_name] = node.name

    @staticmethod
    def duplicate_arg_message(field):
        return 'There can only be one argument named "{}".'.format(field)


class ArgumentsOfCorrectType(ValidationRule):
    def enter_Argument(self, node, *args):
        arg_def = self.context.get_argument()
        if arg_def and not is_valid_literal_value(arg_def.type, node.value):
            return GraphQLError(
                self.bad_value_message(node.name.value, arg_def.type,
                                       print_ast(node.value)),
                [node.value]
            )

    @staticmethod
    def bad_value_message(arg_name, type, value):
        return 'Argument "{}" expected type "{}" but got: {}.'.format(arg_name, type, value)


class ProvidedNonNullArguments(ValidationRule):
    def leave_Field(self, node, *args):
        field_def = self.context.get_field_def()
        if not field_def:
            return False

        errors = []
        arg_asts = node.arguments or []
        arg_ast_map = {arg.name.value: arg for arg in arg_asts}

        for arg_def in field_def.args:
            arg_ast = arg_ast_map.get(arg_def.name, None)
            if not arg_ast and isinstance(arg_def.type, GraphQLNonNull):
                errors.append(GraphQLError(
                    self.missing_field_arg_message(node.name.value, arg_def.name, arg_def.type),
                    [node]
                ))

        if errors:
            return errors

    def leave_Directive(self, node, *args):
        directive_def = self.context.get_directive()
        if not directive_def:
            return False

        errors = []
        arg_asts = node.arguments or []
        arg_ast_map = {arg.name.value: arg for arg in arg_asts}

        for arg_def in directive_def.args:
            arg_ast = arg_ast_map.get(arg_def.name, None)
            if not arg_ast and isinstance(arg_def.type, GraphQLNonNull):
                errors.append(GraphQLError(
                    self.missing_directive_arg_message(node.name.value, arg_def.name, arg_def.type),
                    [node]
                ))

        if errors:
            return errors

    @staticmethod
    def missing_field_arg_message(name, arg_name, type):
        return 'Field "{}" argument "{}" of type "{}" is required but not provided.'.format(name, arg_name, type)

    @staticmethod
    def missing_directive_arg_message(name, arg_name, type):
        return 'Directive "{}" argument "{}" of type "{}" is required but not provided.'.format(name, arg_name, type)


class DefaultValuesOfCorrectType(ValidationRule):
    def enter_VariableDefinition(self, node, *args):
        name = node.variable.name.value
        default_value = node.default_value
        type = self.context.get_input_type()

        if isinstance(type, GraphQLNonNull) and default_value:
            return GraphQLError(
                self.default_for_non_null_arg_message(name, type, type.of_type),
                [default_value]
            )

        if type and default_value and not is_valid_literal_value(type, default_value):
            return GraphQLError(
                self.bad_value_for_default_arg_message(name, type, print_ast(default_value)),
                [default_value]
            )

    @staticmethod
    def default_for_non_null_arg_message(var_name, type, guess_type):
        return 'Variable "${}" of type "{}" is required and will not use the default value. ' \
               'Perhaps you meant to use type "{}".'.format(var_name, type, guess_type)

    @staticmethod
    def bad_value_for_default_arg_message(var_name, type, value):
        return 'Variable "${}" of type "{}" has invalid default value: {}.'.format(var_name, type, value)


class VariablesInAllowedPosition(ValidationRule):
    visit_spread_fragments = True

    def __init__(self, context):
        super(VariablesInAllowedPosition, self).__init__(context)
        self.var_def_map = {}
        self.visited_fragment_names = set()

    def enter_OperationDefinition(self, *args):
        self.var_def_map = {}
        self.visited_fragment_names = set()

    def enter_VariableDefinition(self, node, *args):
        self.var_def_map[node.variable.name.value] = node

    def enter_Variable(self, node, *args):
        var_name = node.name.value
        var_def = self.var_def_map.get(var_name)
        var_type = var_def and type_from_ast(self.context.get_schema(), var_def.type)
        input_type = self.context.get_input_type()
        if var_type and input_type and not self.var_type_allowed_for_type(self.effective_type(var_type, var_def),
                                                                          input_type):
            return GraphQLError(self.bad_var_pos_message(var_name, var_type, input_type),
                                [node])

    def enter_FragmentSpread(self, node, *args):
        if node.name.value in self.visited_fragment_names:
            return False
        self.visited_fragment_names.add(node.name.value)

    @staticmethod
    def effective_type(var_type, var_def):
        if not var_def.default_value or isinstance(var_def, GraphQLNonNull):
            return var_type

        return GraphQLNonNull(var_type)

    @classmethod
    def var_type_allowed_for_type(cls, var_type, expected_type):
        if isinstance(expected_type, GraphQLNonNull):
            if isinstance(var_type, GraphQLNonNull):
                return cls.var_type_allowed_for_type(var_type.of_type, expected_type.of_type)

            return False

        if isinstance(var_type, GraphQLNonNull):
            return cls.var_type_allowed_for_type(var_type.of_type, expected_type)

        if isinstance(var_type, GraphQLList) and isinstance(expected_type, GraphQLList):
            return cls.var_type_allowed_for_type(var_type.of_type, expected_type.of_type)

        return var_type == expected_type

    @staticmethod
    def bad_var_pos_message(var_name, var_type, expected_type):
        return 'Variable "{}" of type "{}" used in position expecting type "{}".'.format(var_name, var_type,
                                                                                         expected_type)


class OverlappingFieldsCanBeMerged(ValidationRule):
    def __init__(self, context):
        super(OverlappingFieldsCanBeMerged, self).__init__(context)
        self.compared_set = PairSet()

    def find_conflicts(self, field_map):
        conflicts = []
        for response_name, fields in field_map.items():
            field_len = len(fields)
            if field_len <= 1:
                continue

            for field_a in fields:
                for field_b in fields:
                    conflict = self.find_conflict(response_name, field_a, field_b)
                    if conflict:
                        conflicts.append(conflict)

        return conflicts

    @staticmethod
    def ast_to_hashable(ast):
        """
        This function will take an AST, and return a portion of it that is unique enough to identify the AST,
        but without the unhashable bits.
        """
        if not ast:
            return None

        return ast.__class__, ast.loc['start'], ast.loc['end']

    def find_conflict(self, response_name, pair1, pair2):
        ast1, def1 = pair1
        ast2, def2 = pair2

        ast1_hashable = self.ast_to_hashable(ast1)
        ast2_hashable = self.ast_to_hashable(ast2)

        if ast1 is ast2 or self.compared_set.has(ast1_hashable, ast2_hashable):
            return

        self.compared_set.add(ast1_hashable, ast2_hashable)

        name1 = ast1.name.value
        name2 = ast2.name.value

        if name1 != name2:
            return (
                (response_name, '{} and {} are different fields'.format(name1, name2)),
                (ast1, ast2)
            )

        type1 = def1 and def1.type
        type2 = def2 and def2.type

        if type1 and type2 and not self.same_type(type1, type2):
            return (
                (response_name, 'they return differing types {} and {}'.format(type1, type2)),
                (ast1, ast2)
            )

        if not self.same_arguments(ast1.arguments, ast2.arguments):
            return (
                (response_name, 'they have differing arguments'),
                (ast1, ast2)
            )

        if not self.same_directives(ast1.directives, ast2.directives):
            return (
                (response_name, 'they have differing directives'),
                (ast1, ast2)
            )

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

            conflicts = self.find_conflicts(subfield_map)
            if conflicts:
                return (
                    (response_name, [conflict[0] for conflict in conflicts]),
                    tuple(itertools.chain((ast1, ast2), *[conflict[1] for conflict in conflicts]))
                )

    def leave_SelectionSet(self, node, *args):
        field_map = self.collect_field_asts_and_defs(
            self.context.get_parent_type(),
            node
        )

        conflicts = self.find_conflicts(field_map)
        if conflicts:
            return [
                GraphQLError(self.fields_conflict_message(reason_name, reason), list(fields)) for
                (reason_name, reason), fields in conflicts
            ]

    @staticmethod
    def same_type(type1, type2):
        return type1.is_same_type(type2)

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

    @classmethod
    def same_directives(cls, directives1, directives2):
        # Check to see if they are empty directives or nones. If they are, we can
        # bail out early.
        if not (directives1 or directives2):
            return True

        if len(directives1) != len(directives2):
            return False

        directives2_values_to_arg = {a.name.value: a for a in directives2}

        for directive1 in directives1:
            directive2 = directives2_values_to_arg.get(directive1.name.value)
            if not directive2:
                return False

            if not cls.same_arguments(directive1.arguments, directive2.arguments):
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
                ast_and_defs[response_name].append((selection, field_def))

            elif isinstance(selection, ast.InlineFragment):
                self.collect_field_asts_and_defs(
                    type_from_ast(self.context.get_schema(), selection.type_condition),
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
        return 'Fields "{}" conflict because {}'.format(reason_name, cls.reason_message(reason))

    @classmethod
    def reason_message(cls, reason):
        if isinstance(reason, list):
            return ' and '.join('subfields "{}" conflict because {}'.format(reason_name, cls.reason_message(sub_reason))
                                for reason_name, sub_reason in reason)

        return reason


class UniqueInputFieldNames(ValidationRule):
    def __init__(self, context):
        super(UniqueInputFieldNames, self).__init__(context)
        self.known_names = {}

    def enter_ObjectValue(self, *args):
        self.known_names = {}

    def enter_ObjectField(self, node, *args):
        field_name = node.name.value
        if field_name in self.known_names:
            return GraphQLError(
                self.duplicate_input_field_message(field_name),
                [self.known_names[field_name], node.name]
            )

        self.known_names[field_name] = node.name

    @staticmethod
    def duplicate_input_field_message(field_name):
        return 'There can only be one input field named "{}".'.format(field_name)
