from copy import copy

from graphql.language import Node


class SampleTestNode(Node):
    __slots__ = ("alpha", "beta", "loc")

    kind = "sample_test"

    def __init__(self, alpha, beta=None, loc=None):
        self.alpha = alpha
        self.beta = beta
        self.loc = loc


def describe_node_class():
    def initializes_with_keywords():
        node = SampleTestNode(alpha=1, beta=2, loc=0)
        assert node.alpha == 1
        assert node.beta == 2
        assert node.loc == 0
        node = SampleTestNode(alpha=1, loc=None)
        assert node.loc is None
        assert node.alpha == 1
        assert node.beta is None
        # node = SampleTestNode(alpha=1, beta=2, gamma=3)
        # assert node.alpha == 1
        # assert node.beta == 2
        # assert not hasattr(node, "gamma")

    def has_representation_with_loc():
        node = SampleTestNode(alpha=1, beta=2)
        assert repr(node) == "SampleTestNode(alpha=1, beta=2, loc=None)"
        node = SampleTestNode(alpha=1, beta=2, loc=3)
        assert repr(node) == "SampleTestNode(alpha=1, beta=2, loc=3)"

    def can_check_equality():
        node = SampleTestNode(alpha=1, beta=2)
        node2 = SampleTestNode(alpha=1, beta=2)
        assert node2 == node
        node2 = SampleTestNode(alpha=1, beta=1)
        assert node2 != node
        # node2 = Node(alpha=1, beta=2)
        # assert node2 != node

    def can_create_shallow_copy():
        node = SampleTestNode(alpha=1, beta=2)
        node2 = copy(node)
        assert node2 is not node
        assert node2 == node

    def provides_snake_cased_kind_as_class_attribute():
        assert SampleTestNode.kind == "sample_test"

    def provides_keys_as_class_attribute():
        assert SampleTestNode.__slots__ == ("alpha", "beta", "loc")
