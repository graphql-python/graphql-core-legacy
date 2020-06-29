#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `graphql.backend.core` module."""

import pytest

from graphql import GraphQLError
from graphql.execution.executors.sync import SyncExecutor
from graphql.validation.rules.base import ValidationRule

from ..base import GraphQLBackend, GraphQLDocument
from ..core import GraphQLCoreBackend
from .schema import schema

if False:
    from pytest_mock import MockFixture
    from typing import Any, List, Optional, Type
    from graphql.language.ast import Document


def test_core_backend():
    # type: () -> None
    """Sample pytest test function with the pytest fixture as an argument."""
    backend = GraphQLCoreBackend()
    assert isinstance(backend, GraphQLBackend)
    document = backend.document_from_string(schema, "{ hello }")
    assert isinstance(document, GraphQLDocument)
    result = document.execute()
    assert not result.errors
    assert result.data == {"hello": "World"}


def test_backend_is_not_cached_by_default():
    # type: () -> None
    """Sample pytest test function with the pytest fixture as an argument."""
    backend = GraphQLCoreBackend()
    document1 = backend.document_from_string(schema, "{ hello }")
    document2 = backend.document_from_string(schema, "{ hello }")
    assert document1 != document2


class BaseExecutor(SyncExecutor):
    executed = False

    def execute(self, *args, **kwargs):
        # type: (*Any, **Any) -> str
        self.executed = True
        return super(BaseExecutor, self).execute(*args, **kwargs)


def test_backend_can_execute_custom_executor():
    # type: () -> None
    executor = BaseExecutor()
    backend = GraphQLCoreBackend(executor=executor)
    document1 = backend.document_from_string(schema, "{ hello }")
    result = document1.execute()
    assert not result.errors
    assert result.data == {"hello": "World"}
    assert executor.executed


class AlwaysFailValidator(ValidationRule):
    # noinspection PyPep8Naming
    def enter_Document(self, node, key, parent, path, ancestors):
        # type: (Document, Optional[Any], Optional[Any], List, List) -> None
        self.context.report_error(GraphQLError("Test validator failure", [node]))


class CustomValidatorBackend(GraphQLCoreBackend):
    def get_validation_rules(self):
        # type: () -> List[Type[ValidationRule]]
        return [AlwaysFailValidator]


def test_backend_custom_validators_result():
    # type: () -> None
    backend = CustomValidatorBackend()
    assert isinstance(backend, CustomValidatorBackend)
    document = backend.document_from_string(schema, "{ hello }")
    assert isinstance(document, GraphQLDocument)
    result = document.execute()
    assert result.errors
    assert len(result.errors) == 1
    assert result.errors[0].message == "Test validator failure"


def test_backend_custom_validators_in_validation_args(mocker):
    # type: (MockFixture) -> None
    mocked_validate = mocker.patch("graphql.backend.core.validate")
    backend = CustomValidatorBackend()
    assert isinstance(backend, CustomValidatorBackend)
    document = backend.document_from_string(schema, "{ hello }")
    assert isinstance(document, GraphQLDocument)
    mocked_validate.assert_not_called()
    result = document.execute()
    mocked_validate.assert_called_once()
    (args, kwargs) = mocked_validate.call_args
    assert [AlwaysFailValidator] in args
