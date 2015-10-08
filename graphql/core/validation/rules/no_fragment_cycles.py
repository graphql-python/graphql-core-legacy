from ...error import GraphQLError
from ...language import ast
from ...language.visitor import Visitor, visit
from .base import ValidationRule


class NoFragmentCycles(ValidationRule):
    def __init__(self, context):
        super(NoFragmentCycles, self).__init__(context)
        self.spreads_in_fragment = {
            node.name.value: self.gather_spreads(node)
            for node in context.get_ast().definitions
            if isinstance(node, ast.FragmentDefinition)
            }
        self.known_to_lead_to_cycle = set()

    def enter_FragmentDefinition(self, node, key, parent, path, ancestors):
        errors = []
        initial_name = node.name.value
        spread_path = []

        def detect_cycle_recursive(fragment_name):
            spread_nodes = self.spreads_in_fragment[fragment_name]

            for spread_node in spread_nodes:
                if spread_node in self.known_to_lead_to_cycle:
                    continue

                if spread_node.name.value == initial_name:
                    cycle_path = spread_path + [spread_node]
                    self.known_to_lead_to_cycle |= set(cycle_path)

                    errors.append(GraphQLError(
                        self.cycle_error_message(initial_name, [s.name.value for s in spread_path]),
                        cycle_path
                    ))
                    continue

                if any(spread is spread_node for spread in spread_path):
                    continue

                spread_path.append(spread_node)
                detect_cycle_recursive(spread_node.name.value)
                spread_path.pop()

        detect_cycle_recursive(initial_name)
        if errors:
            return errors

    @staticmethod
    def cycle_error_message(fragment_name, spread_names):
        via = ' via {}'.format(', '.join(spread_names)) if spread_names else ''
        return 'Cannot spread fragment "{}" within itself{}.'.format(fragment_name, via)

    @classmethod
    def gather_spreads(cls, node):
        visitor = cls.CollectFragmentSpreadNodesVisitor()
        visit(node, visitor)
        return visitor.collect_fragment_spread_nodes()

    class CollectFragmentSpreadNodesVisitor(Visitor):
        def __init__(self):
            self.spread_nodes = []

        def enter_FragmentSpread(self, node, key, parent, path, ancestors):
            self.spread_nodes.append(node)

        def collect_fragment_spread_nodes(self):
            return self.spread_nodes
