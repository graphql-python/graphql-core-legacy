from graphql.core.execution.middlewares.utils import (merge_resolver_tags,
                                                      resolver_has_tag,
                                                      tag_resolver)


def test_tag_resolver():
    resolver = lambda: None

    tag_resolver(resolver, 'test')
    assert resolver_has_tag(resolver, 'test')
    assert not resolver_has_tag(resolver, 'not test')


def test_merge_resolver_tags():
    a = lambda: None
    b = lambda: None

    tag_resolver(a, 'a')
    tag_resolver(b, 'b')

    merge_resolver_tags(a, b)

    assert resolver_has_tag(a, 'a')
    assert not resolver_has_tag(a, 'b')

    assert resolver_has_tag(b, 'a')
    assert resolver_has_tag(b, 'b')


def test_resolver_has_tag_with_untagged_resolver():
    a = lambda: None

    assert not resolver_has_tag(a, 'anything')


def test_merge_resolver_from_untagged_source():
    a = lambda: None
    b = lambda: None

    merge_resolver_tags(a, b)
    assert not hasattr(b, '_resolver_tags')


def test_merge_resolver_to_untagged_target():
    a = lambda: None
    b = lambda: None

    tag_resolver(a, 'test')
    merge_resolver_tags(a, b)

    assert resolver_has_tag(b, 'test')
