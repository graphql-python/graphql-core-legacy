from ..utils import type_from_ast
from ..error import GraphQLError
from ..type.definition import is_composite_type, is_input_type, is_leaf_type
from ..language import ast
from ..language.visitor import Visitor
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
    pass


class KnownFragmentNames(ValidationRule):
    pass


class NoUnusedFragments(ValidationRule):
    pass


class PossibleFragmentSpreads(ValidationRule):
    pass


class NoFragmentCycles(ValidationRule):
    pass


class NoUndefinedVariables(ValidationRule):
    pass


class NoUnusedVariables(ValidationRule):
    pass


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
    pass


class ArgumentsOfCorrectType(ValidationRule):
    pass


class ProvidedNonNullArguments(ValidationRule):
    pass


class DefaultValuesOfCorrectType(ValidationRule):
    pass


class VariablesInAllowedPosition(ValidationRule):
    pass


class OverlappingFieldsCanBeMerged(ValidationRule):
    pass
