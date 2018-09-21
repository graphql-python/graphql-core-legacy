"""graphql.validation.rules package"""

from typing import Type

from ...error import GraphQLError
from ...language.visitor import Visitor
from ..validation_context import (
    ASTValidationContext,
    SDLValidationContext,
    ValidationContext,
)

__all__ = ["ASTValidationRule", "SDLValidationRule", "ValidationRule", "RuleType"]


class ASTValidationRule(Visitor):
    def __init__(self, context):
        self.context = context

    def report_error(self, error):
        self.context.report_error(error)


class SDLValidationRule(ASTValidationRule):
    def __init__(self, context):
        super(SDLValidationRule, self).__init__(context)


class ValidationRule(ASTValidationRule):
    def __init__(self, context):
        super(ValidationRule, self).__init__(context)


RuleType = Type[ASTValidationRule]
