from typing import Optional

from ...error import GraphQLError
from ...language import OperationDefinitionNode, OperationType
from . import ASTValidationRule

__all__ = ["SingleFieldSubscriptionsRule", "single_field_only_message"]


def single_field_only_message(name):
    return (
        "Subscription '{}'".format(name) if name else "Anonymous Subscription"
    ) + " must select only one top level field."


class SingleFieldSubscriptionsRule(ASTValidationRule):
    """Subscriptions must only include one field.

    A GraphQL subscription is valid only if it contains a single root
    """

    def enter_operation_definition(self, node, *_args):
        if node.operation == OperationType.SUBSCRIPTION:
            if len(node.selection_set.selections) != 1:
                self.report_error(
                    GraphQLError(
                        single_field_only_message(
                            node.name.value if node.name else None
                        ),
                        node.selection_set.selections[1:],
                    )
                )
