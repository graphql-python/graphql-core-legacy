from functools import partial
from collections import namedtuple
from graphql import GraphQLObjectType, GraphQLField, GraphQLList, GraphQLInt, GraphQLSchema, execute, parse, Source


def test_big_list_of_ints(benchmark):
    big_int_list = [x for x in range(10000)]

    def resolve_all_ints(root, args, context, info):
        return big_int_list

    Query = GraphQLObjectType('Query', fields={
        'allInts': GraphQLField(
            GraphQLList(GraphQLInt),
            resolver=resolve_all_ints
        )
    })
    hello_schema = GraphQLSchema(Query)
    source = Source('{ allInts }')
    ast = parse(source)
    big_list_query = partial(execute, hello_schema, ast)
    result = benchmark(big_list_query)
    # result = big_list_query()
    assert not result.errors
    assert result.data == {'allInts': big_int_list}


def test_big_list_of_containers_with_one_field(benchmark):
    Container = namedtuple('Container', 'x y z o')

    ContainerType = GraphQLObjectType('Container', fields={
        'x': GraphQLField(GraphQLInt),
        'y': GraphQLField(GraphQLInt),
        'z': GraphQLField(GraphQLInt),
        'o': GraphQLField(GraphQLInt),
    })

    big_container_list = [Container(x=x, y=x, z=x, o=x) for x in range(10000)]

    def resolve_all_containers(root, args, context, info):
        return big_container_list

    Query = GraphQLObjectType('Query', fields={
        'allContainers': GraphQLField(
            GraphQLList(ContainerType),
            resolver=resolve_all_containers
        )
    })
    hello_schema = GraphQLSchema(Query)
    source = Source('{ allContainers { x } }')
    ast = parse(source)
    big_list_query = partial(execute, hello_schema, ast)
    result = benchmark(big_list_query)
    # result = big_list_query()
    assert not result.errors
    assert result.data == {'allContainers': [{'x': c.x} for c in big_container_list]}


def test_big_list_of_containers_with_multiple_fields(benchmark):
    Container = namedtuple('Container', 'x y z o')

    ContainerType = GraphQLObjectType('Container', fields={
        'x': GraphQLField(GraphQLInt),
        'y': GraphQLField(GraphQLInt),
        'z': GraphQLField(GraphQLInt),
        'o': GraphQLField(GraphQLInt),
    })

    big_container_list = [Container(x=x, y=x, z=x, o=x) for x in range(10000)]

    def resolve_all_containers(root, args, context, info):
        return big_container_list

    Query = GraphQLObjectType('Query', fields={
        'allContainers': GraphQLField(
            GraphQLList(ContainerType),
            resolver=resolve_all_containers
        )
    })
    hello_schema = GraphQLSchema(Query)
    source = Source('{ allContainers { x, y, z } }')
    ast = parse(source)
    big_list_query = partial(execute, hello_schema, ast)
    result = benchmark(big_list_query)
    # result = big_list_query()
    assert not result.errors
    assert result.data == {'allContainers': [{'x': c.x, 'y': c.y, 'z': c.z} for c in big_container_list]}
