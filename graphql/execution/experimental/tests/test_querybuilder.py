# from ..querybuilder import generate_fragment, fragment_operation, QueryBuilder
# from ..fragment import Fragment

# from ....language.parser import parse
# from ....language import ast
# from ....type import (GraphQLEnumType, GraphQLInterfaceType, GraphQLList,
#                       GraphQLNonNull, GraphQLObjectType, GraphQLScalarType,
#                       GraphQLSchema, GraphQLUnionType, GraphQLString, GraphQLInt, GraphQLField)


# def test_generate_fragment():
#     Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt)})
#     Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node))})
#     node_field_asts = ast.SelectionSet(selections=[
#         ast.Field(
#             name=ast.Name(value='id'),
#         )
#     ])
#     query_field_asts = [
#         ast.Field(
#             name=ast.Name(value='nodes'),
#             selection_set=node_field_asts
#         )
#     ]
#     QueryFragment = generate_fragment(Query, query_field_asts)

#     assert QueryFragment == Fragment(
#         Query,
#         query_field_asts,
#         field_fragments={
#             'nodes': Fragment(
#                 Node,
#                 node_field_asts.selections
#             )
#         },
#     )


# def test_fragment_operation_query():
#     Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt)})
#     Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node))})

#     schema = GraphQLSchema(query=Query)

#     node_field_asts = ast.SelectionSet(selections=[
#         ast.Field(
#             name=ast.Name(value='id'),
#         )
#     ])
#     query_field_asts = ast.SelectionSet(selections=[
#         ast.Field(
#             name=ast.Name(value='nodes'),
#             selection_set=node_field_asts
#         )
#     ])
#     operation_ast = ast.OperationDefinition(
#         operation='query',
#         selection_set=query_field_asts
#     )
#     QueryFragment = fragment_operation(schema, operation_ast)

#     assert QueryFragment == Fragment(
#         Query,
#         query_field_asts.selections,
#         field_fragments={
#             'nodes': Fragment(
#                 Node,
#                 node_field_asts.selections
#             )
#         },
#     )


# def test_fragment_operation_mutation():
#     Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt)})
#     Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node))})

#     schema = GraphQLSchema(query=Query, mutation=Query)

#     node_field_asts = ast.SelectionSet(selections=[
#         ast.Field(
#             name=ast.Name(value='id'),
#         )
#     ])
#     query_field_asts = ast.SelectionSet(selections=[
#         ast.Field(
#             name=ast.Name(value='nodes'),
#             selection_set=node_field_asts
#         )
#     ])
#     operation_ast = ast.OperationDefinition(
#         operation='mutation',
#         selection_set=query_field_asts
#     )
#     MutationFragment = fragment_operation(schema, operation_ast)

#     assert MutationFragment == Fragment(
#         Query,
#         query_field_asts.selections,
#         field_fragments={
#             'nodes': Fragment(
#                 Node,
#                 node_field_asts.selections
#             )
#         },
#         execute_serially=True
#     )


# def test_query_builder_operation():
#     Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt)})
#     Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node))})

#     schema = GraphQLSchema(query=Query, mutation=Query)
#     document_ast = parse('''query MyQuery {
#         nodes {
#             id
#         }
#     }''')
#     query_builder = QueryBuilder(schema, document_ast)
#     QueryFragment = query_builder.get_operation_fragment('MyQuery')
#     node_field_asts = ast.SelectionSet(selections=[
#         ast.Field(
#             name=ast.Name(value='id'),
#             arguments=[],
#             directives=[],
#             selection_set=None,
#         )
#     ])
#     query_field_asts = ast.SelectionSet(selections=[
#         ast.Field(
#             name=ast.Name(value='nodes'),
#             arguments=[],
#             directives=[],
#             selection_set=node_field_asts
#         )
#     ])
#     assert QueryFragment == Fragment(
#         Query,
#         query_field_asts.selections,
#         field_fragments={
#             'nodes': Fragment(
#                 Node,
#                 node_field_asts.selections
#             )
#         }
#     )


# def test_query_builder_execution():
#     Node = GraphQLObjectType('Node', fields={'id': GraphQLField(GraphQLInt, resolver=lambda obj, **__: obj)})
#     Query = GraphQLObjectType('Query', fields={'nodes': GraphQLField(GraphQLList(Node), resolver=lambda *_, **__: range(3))})

#     schema = GraphQLSchema(query=Query)
#     document_ast = parse('''query MyQuery {
#         nodes {
#             id
#         }
#     }''')
#     query_builder = QueryBuilder(schema, document_ast)
#     QueryFragment = query_builder.get_operation_fragment('MyQuery')
#     root = None
#     expected = {
#         'nodes': [{
#             'id': n
#         } for n in range(3)]
#     }
#     assert QueryFragment.resolver(lambda: root) == expected
