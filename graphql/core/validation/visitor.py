from ..language.visitor import Visitor


class TypeInfoVisitor(Visitor):
    __slots__ = 'visitor', 'type_info'

    def __init__(self, type_info, visitor):
        self.type_info = type_info
        self.visitor = visitor

    def enter(self, node, key, parent, path, ancestors):
        self.type_info.enter(node)
        result = self.visitor.enter(node, key, parent, path, ancestors)
        if result is False:
            self.type_info.leave(node)
            return False

    def leave(self, node, key, parent, path, ancestors):
        self.visitor.leave(node, key, parent, path, ancestors)
        self.type_info.leave(node)


class ParallelVisitor(Visitor):
    __slots__ = 'skipping', 'visitors'

    def __init__(self, visitors):
        self.visitors = visitors
        self.skipping = [None] * len(visitors)

    def enter(self, node, key, parent, path, ancestors):
        for i, visitor in enumerate(self.visitors):
            if not self.skipping[i]:
                result = visitor.enter(node, key, parent, path, ancestors)
                if result is False:
                    self.skipping[i] = node

    def leave(self, node, key, parent, path, ancestors):
        for i, visitor in enumerate(self.visitors):
            if not self.skipping[i]:
                visitor.leave(node, key, parent, path, ancestors)
            else:
                self.skipping[i] = None
