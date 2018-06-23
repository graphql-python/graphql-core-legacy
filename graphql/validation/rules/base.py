from ...language.visitor import Visitor

if False:
    from ..validation import ValidationContext


class ValidationRule(Visitor):
    __slots__ = ("context",)

    def __init__(self, context):
        # type: (ValidationContext) -> None
        self.context = context
