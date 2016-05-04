import copy

from graphql.language.visitor_meta import QUERY_DOCUMENT_KEYS, VisitorMeta


def test_ast_is_hashable():
    for node_class in QUERY_DOCUMENT_KEYS:
        node = node_class(loc=None, **{k: k for k in node_class._fields})
        assert hash(node)


def test_ast_is_copyable():
    for node_class in QUERY_DOCUMENT_KEYS:
        node = node_class(loc=None, **{k: k for k in node_class._fields})
        assert copy.copy(node) == node


def test_ast_is_reprable():
    for node_class in QUERY_DOCUMENT_KEYS:
        node = node_class(loc=None, **{k: k for k in node_class._fields})
        assert repr(node)
