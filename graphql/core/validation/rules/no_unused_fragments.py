from ...error import GraphQLError
from .base import ValidationRule


class NoUnusedFragments(ValidationRule):
    def __init__(self, context):
        super(NoUnusedFragments, self).__init__(context)
        self.fragment_definitions = []
        self.spreads_within_operation = []
        self.fragment_adjacencies = {}
        self.spread_names = set()

    def enter_OperationDefinition(self, node, key, parent, path, ancestors):
        self.spread_names = set()
        self.spreads_within_operation.append(self.spread_names)

    def enter_FragmentDefinition(self, node, key, parent, path, ancestors):
        self.fragment_definitions.append(node)
        self.spread_names = set()
        self.fragment_adjacencies[node.name.value] = self.spread_names

    def enter_FragmentSpread(self, node, key, parent, path, ancestors):
        self.spread_names.add(node.name.value)

    def leave_Document(self, node, key, parent, path, ancestors):
        fragment_names_used = set()

        def reduce_spread_fragments(spreads):
            for fragment_name in spreads:
                if fragment_name in fragment_names_used:
                    continue

                fragment_names_used.add(fragment_name)
                if fragment_name in self.fragment_adjacencies:
                    reduce_spread_fragments(self.fragment_adjacencies[fragment_name])

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
