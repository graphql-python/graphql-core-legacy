from ...error import GraphQLError
from .base import ValidationRule


class NoUnusedFragments(ValidationRule):
    __slots__ = 'fragment_definitions', 'spreads_within_operation', 'fragment_adjacencies', 'spread_names'

    def __init__(self, context):
        super(NoUnusedFragments, self).__init__(context)
        self.spreads_within_operation = []
        self.fragment_definitions = []

    def enter_OperationDefinition(self, node, key, parent, path, ancestors):
        self.spreads_within_operation.append(self.context.get_fragment_spreads(node))
        return False

    def enter_FragmentDefinition(self, node, key, parent, path, ancestors):
        self.fragment_definitions.append(node)
        return False

    def leave_Document(self, node, key, parent, path, ancestors):
        fragment_names_used = set()

        def reduce_spread_fragments(spreads):
            for spread in spreads:
                frag_name = spread.name.value
                if frag_name in fragment_names_used:
                    continue

                fragment_names_used.add(frag_name)
                fragment = self.context.get_fragment(frag_name)
                if fragment:
                    reduce_spread_fragments(self.context.get_fragment_spreads(fragment))

        for spreads in self.spreads_within_operation:
            reduce_spread_fragments(spreads)

        errors = [
            GraphQLError(
                self.unused_fragment_message(fragment_definition.name.value),
                [fragment_definition]
            )
            for fragment_definition in self.fragment_definitions
            if fragment_definition.name.value not in fragment_names_used
            ]

        if errors:
            return errors

    @staticmethod
    def unused_fragment_message(fragment_name):
        return 'Fragment "{}" is never used.'.format(fragment_name)
