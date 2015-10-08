from ...language.visitor import Visitor


class ValidationRule(Visitor):
    def __init__(self, context):
        self.context = context
