from typing import cast, Dict, List, Union

from ...error import GraphQLError
from ...language import ArgumentNode, DirectiveDefinitionNode, DirectiveNode, SKIP
from ...pyutils import quoted_or_list, suggestion_list
from ...type import specified_directives
from . import ASTValidationRule, SDLValidationContext, ValidationContext

__all__ = [
    "KnownArgumentNamesRule",
    "KnownArgumentNamesOnDirectivesRule",
    "unknown_arg_message",
    "unknown_directive_arg_message",
]


def unknown_arg_message(arg_name, field_name, type_name, suggested_args):
    message = ("Unknown argument '{}' on field '{}'" " of type '{}'.").format(
        arg_name, field_name, type_name
    )
    if suggested_args:
        message += " Did you mean {}?".format(quoted_or_list(suggested_args))
    return message


def unknown_directive_arg_message(arg_name, directive_name, suggested_args):
    message = ("Unknown argument '{}'" " on directive '@{}'.").format(
        arg_name, directive_name
    )
    if suggested_args:
        message += " Did you mean {}?".format(quoted_or_list(suggested_args))
    return message


class KnownArgumentNamesOnDirectivesRule(ASTValidationRule):
    """Known argument names on directives

    A GraphQL directive is only valid if all supplied arguments are defined.
    """

    def __init__(self, context):
        super(KnownArgumentNamesOnDirectivesRule, self).__init__(context)
        directive_args = {}

        schema = context.schema
        defined_directives = schema.directives if schema else specified_directives
        for directive in defined_directives:
            directive_args[directive.name] = list(directive.args)

        ast_definitions = context.document.definitions
        for def_ in ast_definitions:
            if isinstance(def_, DirectiveDefinitionNode):
                directive_args[def_.name.value] = (
                    [arg.name.value for arg in def_.arguments] if def_.arguments else []
                )

        self.directive_args = directive_args

    def enter_directive(self, directive_node, *_args):
        directive_name = directive_node.name.value
        known_args = self.directive_args.get(directive_name)
        if directive_node.arguments and known_args:
            for arg_node in directive_node.arguments:
                arg_name = arg_node.name.value
                if arg_name not in known_args:
                    suggestions = suggestion_list(arg_name, known_args)
                    self.report_error(
                        GraphQLError(
                            unknown_directive_arg_message(
                                arg_name, directive_name, suggestions
                            ),
                            arg_node,
                        )
                    )
        return SKIP


class KnownArgumentNamesRule(KnownArgumentNamesOnDirectivesRule):
    """Known argument names

    A GraphQL field is only valid if all supplied arguments are defined by
    that field.
    """

    def __init__(self, context):
        super(KnownArgumentNamesRule, self).__init__(context)

    def enter_argument(self, arg_node, *args):
        context = self.context
        arg_def = context.get_argument()
        field_def = context.get_field_def()
        parent_type = context.get_parent_type()
        if not arg_def and field_def and parent_type:
            arg_name = arg_node.name.value
            field_name = args[3][-1].name.value
            known_args_names = list(field_def.args)
            context.report_error(
                GraphQLError(
                    unknown_arg_message(
                        arg_name,
                        field_name,
                        parent_type.name,
                        suggestion_list(arg_name, known_args_names),
                    ),
                    arg_node,
                )
            )
