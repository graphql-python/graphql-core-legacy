#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `graphql.backend.decider` module."""

import pytest

from ..base import GraphQLBackend, GraphQLDocument
from ..core import GraphQLCoreBackend
from ..cache import GraphQLCachedBackend
from ..decider import GraphQLDeciderBackend

from .schema import schema
from typing import Any


class FakeBackend(GraphQLBackend):
    reached = False

    def __init__(self, raises=False):
        # type: (bool) -> None
        self.raises = raises

    def document_from_string(self, *args, **kwargs):
        # type: (*Any, **Any) -> None
        self.reached = True
        if self.raises:
            raise Exception("Backend failed")

    def reset(self):
        # type: () -> None
        self.reached = False


def test_decider_backend_healthy_backend():
    # type: () -> None
    backend1 = FakeBackend()
    backend2 = FakeBackend()
    decider_backend = GraphQLDeciderBackend([backend1, backend2])

    decider_backend.document_from_string(schema, "{ hello }")
    assert backend1.reached
    assert not backend2.reached


def test_decider_backend_unhealthy_backend():
    # type: () -> None
    backend1 = FakeBackend(raises=True)
    backend2 = FakeBackend()
    decider_backend = GraphQLDeciderBackend([backend1, backend2])

    decider_backend.document_from_string(schema, "{ hello }")
    assert backend1.reached
    assert backend2.reached


def test_decider_backend_dont_use_cache():
    # type: () -> None
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
    # type: () -> None
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
