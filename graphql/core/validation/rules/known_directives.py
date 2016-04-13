from ...error import GraphQLError
from ...language import ast
from .base import ValidationRule


class KnownDirectives(ValidationRule):
    def enter_Directive(self, node, key, parent, path, ancestors):
        directive_def = next((
            definition for definition in self.context.get_schema().get_directives()
            if definition.name == node.name.value
        ), None)

        if not directive_def:
            return self.context.report_error(GraphQLError(
                self.unknown_directive_message(node.name.value),
                [node]
            ))

        applied_to = ancestors[-1]

        if isinstance(applied_to, ast.OperationDefinition) and not directive_def.on_operation:
            self.context.report_error(GraphQLError(
                self.misplaced_directive_message(node.name.value, 'operation'),
                [node]
            ))

        elif isinstance(applied_to, ast.Field) and not directive_def.on_field:
            self.context.report_error(GraphQLError(
                self.misplaced_directive_message(node.name.value, 'field'),
                [node]
            ))

        elif (isinstance(applied_to, (ast.FragmentSpread, ast.InlineFragment, ast.FragmentDefinition)) and
                not directive_def.on_fragment):
            self.context.report_error(GraphQLError(
                self.misplaced_directive_message(node.name.value, 'fragment'),
                [node]
            ))

    @staticmethod
    def unknown_directive_message(directive_name):
        return 'Unknown directive "{}".'.format(directive_name)

    @staticmethod
    def misplaced_directive_message(directive_name, placement):
        return 'Directive "{}" may not be used on "{}".'.format(directive_name, placement)
