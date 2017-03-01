from collections import namedtuple
from functools import partial

from graphql import (GraphQLField, GraphQLInt, GraphQLList, GraphQLObjectType,
                     GraphQLSchema, Source, execute, parse)


# set global fixtures
Container = namedtuple('Container', 'x y z o')
big_int_list = [x for x in range(5000)]
big_container_list = [Container(x=x, y=x, z=x, o=x) for x in range(5000)]

ContainerType = GraphQLObjectType('Container',
    fields={
        'x': GraphQLField(GraphQLInt),
        'y': GraphQLField(GraphQLInt),
        'z': GraphQLField(GraphQLInt),
        'o': GraphQLField(GraphQLInt),
    })


def resolve_all_containers(root, args, context, info):
    return big_container_list


def resolve_all_ints(root, args, context, info):
    return big_int_list


def test_big_list_of_ints_to_graphql_schema(benchmark):
    @benchmark
    def schema():
        Query = GraphQLObjectType('Query', fields={
            'allInts': GraphQLField(
                GraphQLList(GraphQLInt),
                resolver=resolve_all_ints
            )
        })
        return GraphQLSchema(Query)


def test_big_list_of_ints_to_graphql_ast(benchmark):
    @benchmark
    def ast():
        source = Source('{ allInts }')
        return parse(source)


def test_big_list_of_ints_to_graphql_partial(benchmark):
    Query = GraphQLObjectType('Query', fields={
        'allInts': GraphQLField(
            GraphQLList(GraphQLInt),
            resolver=resolve_all_ints
        )
    })
    hello_schema = GraphQLSchema(Query)
    source = Source('{ allInts }')
    ast = parse(source)

    @benchmark
    def b():
        return partial(execute, hello_schema, ast)

def test_big_list_of_ints_to_graphql_total(benchmark):
    @benchmark
    def total():
        Query = GraphQLObjectType('Query', fields={
        'allInts': GraphQLField(
            GraphQLList(GraphQLInt),
                resolver=resolve_all_ints
            )
        })
        hello_schema = GraphQLSchema(Query)
        source = Source('{ allInts }')
        ast = parse(source)
        return partial(execute, hello_schema, ast)


def test_big_list_of_ints_base_serialize(benchmark):
    from ..executor import complete_leaf_value

    @benchmark
    def serialize():
        for i in big_int_list:
            GraphQLInt.serialize(i)


def test_total_big_list_of_containers_with_one_field_schema(benchmark):
    @benchmark
    def schema():
        Query = GraphQLObjectType('Query', fields={
            'allContainers': GraphQLField(
                GraphQLList(ContainerType),
                resolver=resolve_all_containers
            )
        })
        return GraphQLSchema(Query)


def test_total_big_list_of_containers_with_one_field_parse(benchmark):
    @benchmark
    def ast():
        source = Source('{ allContainers { x } }')
        ast = parse(source)


def test_total_big_list_of_containers_with_one_field_partial(benchmark):
    Query = GraphQLObjectType('Query', fields={
        'allContainers': GraphQLField(
            GraphQLList(ContainerType),
            resolver=resolve_all_containers
        )
    })
    hello_schema = GraphQLSchema(Query)
    source = Source('{ allContainers { x } }')
    ast = parse(source)

    @benchmark
    def b():
        return partial(execute, hello_schema, ast)


def test_total_big_list_of_containers_with_one_field_total(benchmark):
    @benchmark
    def total():
        Query = GraphQLObjectType('Query', fields={
            'allContainers': GraphQLField(
                GraphQLList(ContainerType),
                resolver=resolve_all_containers
            )
        })
        hello_schema = GraphQLSchema(Query)
        source = Source('{ allContainers { x } }')
        ast = parse(source)
        result = partial(execute, hello_schema, ast)


def test_total_big_list_of_containers_with_multiple_fields_partial(benchmark):
    Query = GraphQLObjectType('Query', fields={
        'allContainers': GraphQLField(
            GraphQLList(ContainerType),
            resolver=resolve_all_containers
        )
    })

    hello_schema = GraphQLSchema(Query)
    source = Source('{ allContainers { x, y, z } }')
    ast = parse(source)

    @benchmark
    def b():
        return partial(execute, hello_schema, ast)


def test_total_big_list_of_containers_with_multiple_fields(benchmark):
    @benchmark
    def total():
        Query = GraphQLObjectType('Query', fields={
            'allContainers': GraphQLField(
                GraphQLList(ContainerType),
                resolver=resolve_all_containers
            )
        })

        hello_schema = GraphQLSchema(Query)
        source = Source('{ allContainers { x, y, z } }')
        ast = parse(source)
        result = partial(execute, hello_schema, ast)
