from ..language.visitor import Visitor


class ValidationVisitor(Visitor):
    __slots__ = 'context', 'instance', 'type_info'

    def __init__(self, instance, context, type_info):
        self.context = context
        self.instance = instance
        self.type_info = type_info

    def enter(self, node, key, parent, path, ancestors):
        self.type_info.enter(node)
        result = self.instance.enter(node, key, parent, path, ancestors)
        if result is False:
            self.type_info.leave(node)

        return result

    def leave(self, node, key, parent, path, ancestors):
        result = self.instance.leave(node, key, parent, path, ancestors)

        self.type_info.leave(node)
        return result
