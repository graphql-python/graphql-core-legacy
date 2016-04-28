# TODO: Port once everything is done

# from graphql import graphql
# from graphql.error import format_error

# from .starwars_schema import StarWarsSchema


# def test_allows_querying_the_schema_for_types():
#     query = '''
#         query IntrospectionTypeQuery {
#           __schema {
#             types {
#               name
#             }
#           }
#         }
#     '''
#     expected = {
#         "__schema": {
#             "types": [
#                       {
#                        "name": "Query"
#                        }, 
#                       {
#                        "name": "Episode"
#                        }, 
#                       {
#                           "name": "Character"
#                        }, 
#                       {
#                           "name": "Human"
#                        }, 
#                       {
#                           "name": "String"
#                        }, 
#                       {
#                           "name": "Droid"
#                        }, 
#                       {
#                           "name": "__Schema"
#                        }, 
#                       {
#                           "name": "__Type"
#                        }, 
#                       {
#                           "name": "__TypeKind"
#                        }, 
#                       {
#                           "name": "Boolean"
#                        }, 
#                       {
#                           "name": "__Field"
#                        }, 
#                       {
#                           "name": "__InputValue"
#                        }, 
#                       {
#                           "name": "__EnumValue"
#                        }, 
#                       {
#                           "name": "__Directive"
#                        }]
#          }
#     }

#     result = graphql(StarWarsSchema, query)
#     assert not result.errors
#     assert result.data == expected
