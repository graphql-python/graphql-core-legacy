import pytest

from graphql import graphql, graphql_async
from graphql.error import format_error

from .starwars_schema import StarWarsSchema


@pytest.fixture(params=['sync', 'async'])
def execute_graphql(request):
    async def _execute(
            schema,
            query,
            variable_values=None
    ):
        if request.param == 'sync':
            return graphql(schema, query, variable_values=variable_values)
        else:
            return await graphql_async(schema, query, variable_values=variable_values)
    return _execute


@pytest.fixture
def execute_and_validate_result(execute_graphql):
    async def _execute_and_validate(
            schema,
            query,
            expected,
            variable_values=None
    ):
        result = await execute_graphql(schema, query, variable_values=variable_values)
        assert not result.errors
        assert result.data == expected
    return _execute_and_validate


@pytest.mark.asyncio
async def test_hero_name_query(execute_and_validate_result):
    query = """
        query HeroNameQuery {
          hero {
            name
          }
        }
    """
    expected = {"hero": {"name": "R2-D2"}}
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_hero_name_and_friends_query(execute_and_validate_result):
    query = """
        query HeroNameAndFriendsQuery {
          hero {
            id
            name
            friends {
              name
            }
          }
        }
    """
    expected = {
        "hero": {
            "id": "2001",
            "name": "R2-D2",
            "friends": [
                {"name": "Luke Skywalker"},
                {"name": "Han Solo"},
                {"name": "Leia Organa"},
            ],
        }
    }
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_nested_query(execute_and_validate_result):
    query = """
        query NestedQuery {
          hero {
            name
            friends {
              name
              appearsIn
              friends {
                name
              }
            }
          }
        }
    """
    expected = {
        "hero": {
            "name": "R2-D2",
            "friends": [
                {
                    "name": "Luke Skywalker",
                    "appearsIn": ["NEWHOPE", "EMPIRE", "JEDI"],
                    "friends": [
                        {"name": "Han Solo"},
                        {"name": "Leia Organa"},
                        {"name": "C-3PO"},
                        {"name": "R2-D2"},
                    ],
                },
                {
                    "name": "Han Solo",
                    "appearsIn": ["NEWHOPE", "EMPIRE", "JEDI"],
                    "friends": [
                        {"name": "Luke Skywalker"},
                        {"name": "Leia Organa"},
                        {"name": "R2-D2"},
                    ],
                },
                {
                    "name": "Leia Organa",
                    "appearsIn": ["NEWHOPE", "EMPIRE", "JEDI"],
                    "friends": [
                        {"name": "Luke Skywalker"},
                        {"name": "Han Solo"},
                        {"name": "C-3PO"},
                        {"name": "R2-D2"},
                    ],
                },
            ],
        }
    }
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_fetch_luke_query(execute_and_validate_result):
    query = """
        query FetchLukeQuery {
          human(id: "1000") {
            name
          }
        }
    """
    expected = {"human": {"name": "Luke Skywalker"}}
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_fetch_some_id_query(execute_and_validate_result):
    query = """
        query FetchSomeIDQuery($someId: String!) {
          human(id: $someId) {
            name
          }
        }
    """
    params = {"someId": "1000"}
    expected = {"human": {"name": "Luke Skywalker"}}
    await execute_and_validate_result(StarWarsSchema, query, expected, variable_values=params)


@pytest.mark.asyncio
async def test_fetch_some_id_query2(execute_and_validate_result):
    query = """
        query FetchSomeIDQuery($someId: String!) {
          human(id: $someId) {
            name
          }
        }
    """
    params = {"someId": "1002"}
    expected = {"human": {"name": "Han Solo"}}
    await execute_and_validate_result(StarWarsSchema, query, expected, variable_values=params)


@pytest.mark.asyncio
async def test_invalid_id_query(execute_and_validate_result):
    query = """
        query humanQuery($id: String!) {
          human(id: $id) {
            name
          }
        }
    """
    params = {"id": "not a valid id"}
    expected = {"human": None}
    await execute_and_validate_result(StarWarsSchema, query, expected, variable_values=params)


@pytest.mark.asyncio
async def test_fetch_luke_aliased(execute_and_validate_result):
    query = """
        query FetchLukeAliased {
          luke: human(id: "1000") {
            name
          }
        }
    """
    expected = {"luke": {"name": "Luke Skywalker"}}
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_fetch_luke_and_leia_aliased(execute_and_validate_result):
    query = """
        query FetchLukeAndLeiaAliased {
          luke: human(id: "1000") {
            name
          }
          leia: human(id: "1003") {
            name
          }
        }
    """
    expected = {"luke": {"name": "Luke Skywalker"}, "leia": {"name": "Leia Organa"}}
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_duplicate_fields(execute_and_validate_result):
    query = """
        query DuplicateFields {
          luke: human(id: "1000") {
            name
            homePlanet
          }
          leia: human(id: "1003") {
            name
            homePlanet
          }
        }
    """
    expected = {
        "luke": {"name": "Luke Skywalker", "homePlanet": "Tatooine"},
        "leia": {"name": "Leia Organa", "homePlanet": "Alderaan"},
    }
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_use_fragment(execute_and_validate_result):
    query = """
        query UseFragment {
          luke: human(id: "1000") {
            ...HumanFragment
          }
          leia: human(id: "1003") {
            ...HumanFragment
          }
        }
        fragment HumanFragment on Human {
          name
          homePlanet
        }
    """
    expected = {
        "luke": {"name": "Luke Skywalker", "homePlanet": "Tatooine"},
        "leia": {"name": "Leia Organa", "homePlanet": "Alderaan"},
    }
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_check_type_of_r2(execute_and_validate_result):
    query = """
        query CheckTypeOfR2 {
          hero {
            __typename
            name
          }
        }
    """
    expected = {"hero": {"__typename": "Droid", "name": "R2-D2"}}
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_check_type_of_luke(execute_and_validate_result):
    query = """
        query CheckTypeOfLuke {
          hero(episode: EMPIRE) {
            __typename
            name
          }
        }
    """
    expected = {"hero": {"__typename": "Human", "name": "Luke Skywalker"}}
    await execute_and_validate_result(StarWarsSchema, query, expected)


@pytest.mark.asyncio
async def test_parse_error(execute_graphql):
    query = """
        qeury
    """
    result = await execute_graphql(StarWarsSchema, query)
    assert result.invalid
    formatted_error = format_error(result.errors[0])
    assert formatted_error["locations"] == [{"column": 9, "line": 2}]
    assert (
        'Syntax Error GraphQL (2:9) Unexpected Name "qeury"'
        in formatted_error["message"]
    )
    assert result.data is None
