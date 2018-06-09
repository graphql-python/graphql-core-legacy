#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `graphql.backend.decider` module."""

from ..base import GraphQLBackend
from ..cache import GraphQLCachedBackend
from ..decider import GraphQLDeciderBackend

from .schema import schema


class FakeBackend(GraphQLBackend):
    reached = False

    def __init__(self, raises=False):
        self.raises = raises

    def document_from_string(self, *args, **kwargs):
        self.reached = True
        if self.raises:
            raise Exception("Backend failed")

    def reset(self):
        self.reached = False


def test_decider_backend_healthy_backend():
    backend1 = FakeBackend()
    backend2 = FakeBackend()
    decider_backend = GraphQLDeciderBackend([backend1, backend2])

    decider_backend.document_from_string(schema, "{ hello }")
    assert backend1.reached
    assert not backend2.reached


def test_decider_backend_unhealthy_backend():
    backend1 = FakeBackend(raises=True)
    backend2 = FakeBackend()
    decider_backend = GraphQLDeciderBackend([backend1, backend2])

    decider_backend.document_from_string(schema, "{ hello }")
    assert backend1.reached
    assert backend2.reached


def test_decider_backend_dont_use_cache():
    backend1 = FakeBackend()
    backend2 = FakeBackend()
    decider_backend = GraphQLDeciderBackend([backend1, backend2])

    decider_backend.document_from_string(schema, "{ hello }")
    assert backend1.reached
    assert not backend2.reached

    backend1.reset()
    decider_backend.document_from_string(schema, "{ hello }")
    assert backend1.reached


def test_decider_backend_use_cache_if_provided():
    backend1 = FakeBackend()
    backend2 = FakeBackend()
    decider_backend = GraphQLDeciderBackend(
        [GraphQLCachedBackend(backend1), GraphQLCachedBackend(backend2)]
    )

    decider_backend.document_from_string(schema, "{ hello }")
    assert backend1.reached
    assert not backend2.reached

    backend1.reset()
    decider_backend.document_from_string(schema, "{ hello }")
    assert not backend1.reached
