from pytest import mark

from graphql import graphql

from .star_wars_schema import star_wars_schema


def describe_star_wars_query_tests():
    def describe_basic_queries():
        def correctly_identifies_r2_d2_as_hero_of_the_star_wars_saga():
            query = """
                query HeroNameQuery {
                  hero {
                    name
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == ({"hero": {"name": "R2-D2"}}, None)

        def accepts_an_object_with_named_properties_to_graphql():
            query = """
                query HeroNameQuery {
                  hero {
                    name
                  }
                }
                """
            result = graphql(schema=star_wars_schema, source=query).get()
            assert result == ({"hero": {"name": "R2-D2"}}, None)

        def allows_us_to_query_for_the_id_and_friends_of_r2_d2():
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
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {
                    "hero": {
                        "id": "2001",
                        "name": "R2-D2",
                        "friends": [
                            {"name": "Luke Skywalker"},
                            {"name": "Han Solo"},
                            {"name": "Leia Organa"},
                        ],
                    }
                },
                None,
            )

    def describe_nested_queries():
        def allows_us_to_query_for_the_friends_of_friends_of_r2_d2():
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
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {
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
                },
                None,
            )

    def describe_using_ids_and_query_parameters_to_refetch_objects():
        def allows_us_to_query_for_r2_d2_directly_using_his_id():
            query = """
                query {
                  droid(id: "2001") {
                    name
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == ({"droid": {"name": "R2-D2"}}, None)

        def allows_us_to_query_for_luke_directly_using_his_id():
            query = """
                query FetchLukeQuery {
                  human(id: "1000") {
                    name
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == ({"human": {"name": "Luke Skywalker"}}, None)

        def allows_creating_a_generic_query_to_fetch_luke_using_his_id():
            query = """
                query FetchSomeIDQuery($someId: String!) {
                  human(id: $someId) {
                    name
                  }
                }
                """
            params = {"someId": "1000"}
            result = graphql(star_wars_schema, query, variable_values=params).get()
            assert result == ({"human": {"name": "Luke Skywalker"}}, None)

        def allows_creating_a_generic_query_to_fetch_han_using_his_id():
            query = """
                query FetchSomeIDQuery($someId: String!) {
                  human(id: $someId) {
                    name
                  }
                }
                """
            params = {"someId": "1002"}
            result = graphql(star_wars_schema, query, variable_values=params).get()
            assert result == ({"human": {"name": "Han Solo"}}, None)

        def generic_query_that_gets_null_back_when_passed_invalid_id():
            query = """
                query humanQuery($id: String!) {
                  human(id: $id) {
                    name
                  }
                }
                """
            params = {"id": "not a valid id"}
            result = graphql(star_wars_schema, query, variable_values=params).get()
            assert result == ({"human": None}, None)

    def describe_using_aliases_to_change_the_key_in_the_response():
        def allows_us_to_query_for_luke_changing_his_key_with_an_alias():
            query = """
                query FetchLukeAliased {
                  luke: human(id: "1000") {
                    name
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == ({"luke": {"name": "Luke Skywalker"}}, None)

        def query_for_luke_and_leia_using_two_root_fields_and_an_alias():
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
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {"luke": {"name": "Luke Skywalker"}, "leia": {"name": "Leia Organa"}},
                None,
            )

    def describe_uses_fragments_to_express_more_complex_queries():
        def allows_us_to_query_using_duplicated_content():
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
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {
                    "luke": {"name": "Luke Skywalker", "homePlanet": "Tatooine"},
                    "leia": {"name": "Leia Organa", "homePlanet": "Alderaan"},
                },
                None,
            )

        def allows_us_to_use_a_fragment_to_avoid_duplicating_content():
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
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {
                    "luke": {"name": "Luke Skywalker", "homePlanet": "Tatooine"},
                    "leia": {"name": "Leia Organa", "homePlanet": "Alderaan"},
                },
                None,
            )

    def describe_using_typename_to_find_the_type_of_an_object():
        def allows_us_to_verify_that_r2_d2_is_a_droid():
            query = """
                query CheckTypeOfR2 {
                  hero {
                    __typename
                    name
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == ({"hero": {"__typename": "Droid", "name": "R2-D2"}}, None)

        def allows_us_to_verify_that_luke_is_a_human():
            query = """
                query CheckTypeOfLuke {
                  hero(episode: EMPIRE) {
                    __typename
                    name
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {"hero": {"__typename": "Human", "name": "Luke Skywalker"}},
                None,
            )

    def describe_reporting_errors_raised_in_resolvers():
        def correctly_reports_error_on_accessing_secret_backstory():
            query = """
                query HeroNameQuery {
                  hero {
                    name
                    secretBackstory
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {"hero": {"name": "R2-D2", "secretBackstory": None}},
                [
                    {
                        "message": "secretBackstory is secret.",
                        "locations": [(5, 21)],
                        "path": ["hero", "secretBackstory"],
                    }
                ],
            )

        def correctly_reports_error_on_accessing_backstory_in_a_list():
            query = """
                query HeroNameQuery {
                  hero {
                    name
                    friends {
                      name
                      secretBackstory
                    }
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {
                    "hero": {
                        "name": "R2-D2",
                        "friends": [
                            {"name": "Luke Skywalker", "secretBackstory": None},
                            {"name": "Han Solo", "secretBackstory": None},
                            {"name": "Leia Organa", "secretBackstory": None},
                        ],
                    }
                },
                [
                    {
                        "message": "secretBackstory is secret.",
                        "locations": [(7, 23)],
                        "path": ["hero", "friends", 0, "secretBackstory"],
                    },
                    {
                        "message": "secretBackstory is secret.",
                        "locations": [(7, 23)],
                        "path": ["hero", "friends", 1, "secretBackstory"],
                    },
                    {
                        "message": "secretBackstory is secret.",
                        "locations": [(7, 23)],
                        "path": ["hero", "friends", 2, "secretBackstory"],
                    },
                ],
            )

        def correctly_reports_error_on_accessing_through_an_alias():
            query = """
                query HeroNameQuery {
                  mainHero: hero {
                    name
                    story: secretBackstory
                  }
                }
                """
            result = graphql(star_wars_schema, query).get()
            assert result == (
                {"mainHero": {"name": "R2-D2", "story": None}},
                [
                    {
                        "message": "secretBackstory is secret.",
                        "locations": [(5, 21)],
                        "path": ["mainHero", "story"],
                    }
                ],
            )

