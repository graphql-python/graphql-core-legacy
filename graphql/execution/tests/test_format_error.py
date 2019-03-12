# coding: utf-8
import pytest

from graphql.error import GraphQLError, format_error


@pytest.mark.parametrize(
    "error",
    [
        GraphQLError("UNIÇODÉ!"),
        GraphQLError("\xd0\xbe\xd1\x88\xd0\xb8\xd0\xb1\xd0\xba\xd0\xb0"),
    ],
)
def test_unicode_format_error(error):
    # type: (GraphQLError) -> None
    assert isinstance(format_error(error), dict)
