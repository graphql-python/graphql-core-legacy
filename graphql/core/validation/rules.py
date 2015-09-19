from ..utils import type_from_ast, is_valid_literal_value
from ..error import GraphQLError
from ..type.definition import is_composite_type, is_input_type, is_leaf_type, GraphQLNonNull
from ..language import ast
from ..language.visitor import Visitor, visit
from ..language.printer import print_ast


class ValidationRule(Visitor):
    def __init__(self, context):
        self.context = context


class UniqueOperationNames(ValidationRule):
    def __init__(self, context):
        super(UniqueOperationNames, self).__init__(context)
        self.known_operation_names = {}

    def enter_OperationDefinition(self, node, *args):
        operation_name = node.name
        if operation_name:
            if operation_name.value in self.known_operation_names:
                return GraphQLError(
                    self.message(operation_name.value),
                    [self.known_operation_names[operation_name.value], operation_name]
                )
            self.known_operation_names[operation_name.value] = operation_name

    @staticmethod
    def message(operation_name):
        return 'There can only be one operation named "{}".'.format(operation_name)


class LoneAnonymousOperation(ValidationRule):
    def __init__(self, context):
        super(LoneAnonymousOperation, self).__init__(context)
        self._op_count = 0

    def enter_Document(self, node, *args):
        n = 0
        for definition in node.definitions:
            if isinstance(definition, ast.OperationDefinition):
                n += 1
        self._op_count = n

    def enter_OperationDefinition(self, node, *args):
        if not node.name and self._op_count > 1:
            return GraphQLError(self.message(), [node])

    @staticmethod
    def message():
        return 'This anonymous operation must be the only defined operation.'


class KnownTypeNames(ValidationRule):
    def enter_NamedType(self, node, *args):
        type_name = node.name.value
        type = self.context.get_schema().get_type(type_name)
        if not type:
            return GraphQLError(self.message(type_name), [node])

    @staticmethod
    def message(type):
        return 'Unknown type "{}".'.format(type)


class FragmentsOnCompositeTypes(ValidationRule):
    def enter_InlineFragment(self, node, *args):
        type = self.context.get_type()
        if type and not is_composite_type(type):
            return GraphQLError(
                self.inline_message(print_ast(node.type_condition)),
                [node.type_condition]
            )

    def enter_FragmentDefinition(self, node, *args):
        type = self.context.get_type()
        if type and not is_composite_type(type):
            return GraphQLError(
                self.message(node.name.value, print_ast(node.type_condition)),
                [node.type_condition]
            )

    @staticmethod
    def inline_message(type):
        return 'Fragment cannot condition on non composite type "{}".'.format(type)

    @staticmethod
    def message(frag_name, type):
        return 'Fragment "{}" cannot condition on non composite type "{}".'.format(frag_name, type)


class VariablesAreInputTypes(ValidationRule):
    def enter_VariableDefinition(self, node, *args):
        type = type_from_ast(self.context.get_schema(), node.type)

        if type and not is_input_type(type):
            variable_name = node.variable.name.value
            return GraphQLError(
                self.message(variable_name, print_ast(node.type)),
                [node.type]
            )

    @staticmethod
    def message(variable_name, type_name):
        return 'Variable "${}" cannot be non-input type "{}".'.format(variable_name, type_name)


class ScalarLeafs(ValidationRule):
    def enter_Field(self, node, *args):
        type = self.context.get_type()
        if type:
            if is_leaf_type(type):
                if node.selection_set:
                    return GraphQLError(
                        self.not_allowed_message(node.name.value, type),
                        [node.selection_set]
                    )
            elif not node.selection_set:
                return GraphQLError(
                    self.required_message(node.name.value, type),
                    [node]
                )

    @staticmethod
    def not_allowed_message(field, type):
        return 'Field "{}" of type "{}" must not have a sub selection.'.format(field, type)

    @staticmethod
    def required_message(field, type):
        return 'Field "{}" of type "{}" must have a sub selection.'.format(field, type)


class FieldsOnCorrectType(ValidationRule):
    def enter_Field(self, node, *args):
        type = self.context.get_parent_type()
        if type:
            field_def = self.context.get_field_def()
            if not field_def:
                return GraphQLError(
                    self.message(node.name.value, type.name),
                    [node]
                )

    @staticmethod
    def message(field_name, type):
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
        return 'There can only be one fragment named {}'.format(field)


class KnownFragmentNames(ValidationRule):
    def enter_FragmentSpread(self, node, *args):
        fragment_name = node.name.value
        try:
            self.context.get_fragment(fragment_name)
        except KeyError:
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
    pass


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
    pass


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
        directive_def = None
        for definition in self.context.get_schema().get_directives():
            if definition.name == node.name.value:
                directive_def = definition
                break
        if not directive_def:
            return GraphQLError(
                self.message(node.name.value),
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
    def message(directive_name):
        return 'Unknown directive "{}".'.format(directive_name)

    @staticmethod
    def misplaced_directive_message(directive_name, placement):
        return 'Directive "{}" may not be used on "{}".'.format(directive_name, placement)


class KnownArgumentNames(ValidationRule):
    def enter_Argument(self, node, key, parent, path, ancestors):
        argument_of = ancestors[-1]
        if isinstance(argument_of, ast.Field):
            field_def = self.context.get_field_def()
            if field_def:
                field_arg_def = None
                for arg in field_def.args:
                    if arg.name == node.name.value:
                        field_arg_def = arg
                        break
                if not field_arg_def:
                    parent_type = self.context.get_parent_type()
                    assert parent_type
                    return GraphQLError(
                        self.message(node.name.value, field_def.name, parent_type.name),
                        [node]
                    )
        elif isinstance(argument_of, ast.Directive):
            directive = self.context.get_directive()
            if directive:
                directive_arg_def = None
                for arg in directive.args:
                    if arg.name == node.name.value:
                        directive_arg_def = arg
                        break
                if not directive_arg_def:
                    return GraphQLError(
                        self.directive_message(node.name.value, directive.name),
                        [node]
                    )

    @staticmethod
    def message(arg_name, field_name, type):
        return 'Unknown argument "{}" on field "{}" of type "{}".'.format(arg_name, field_name, type)

    @staticmethod
    def directive_message(arg_name, directive_name):
        return 'Unknown argument "{}" on directive "@{}".'.format(arg_name, directive_name)


class UniqueArgumentNames(ValidationRule):
    def __init__(self, context):
        super(UniqueArgumentNames, self).__init__(context)
        self.known_arg_names = {}

    def enter_Field(self, node, *args):
        self.known_arg_names = {}

    def enter_Directive(self, node, key, parent, path, ancestors):
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
        return 'There can only be one argument named {}'.format(field)


class ArgumentsOfCorrectType(ValidationRule):
    pass


class ProvidedNonNullArguments(ValidationRule):
    def leave_Field(self, node, key, parent, path, ancestors):
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

    def leave_Directive(self, node, key, parent, path, ancestors):
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
    pass


class OverlappingFieldsCanBeMerged(ValidationRule):
    pass
