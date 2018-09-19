from typing import Dict, List

from ...error import GraphQLError
from ...language import DirectiveNode, Node
from . import ASTValidationRule

__all__ = ["UniqueDirectivesPerLocationRule", "duplicate_directive_message"]


def duplicate_directive_message(directive_name):
    return ("The directive '{}'" " can only be used once at this location.").format(
        directive_name
    )


class UniqueDirectivesPerLocationRule(ASTValidationRule):
    """Unique directive names per location

    A GraphQL document is only valid if all directives at a given location
    are uniquely named.
    """

    # Many different AST nodes may contain directives. Rather than listing
    # them all, just listen for entering any node, and check to see if it
    # defines any directives.
    def enter(self, node, *_args):
        directives = getattr(node, "directives", None)
        if directives:
            known_directives = {}
            for directive in directives:
                directive_name = directive.name.value
                if directive_name in known_directives:
                    self.report_error(
                        GraphQLError(
                            duplicate_directive_message(directive_name),
                            [known_directives[directive_name], directive],
                        )
                    )
                else:
                    known_directives[directive_name] = directive
