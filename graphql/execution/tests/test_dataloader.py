# type: ignore
from collections import namedtuple

import pytest
from promise import Promise
from promise.dataloader import DataLoader
from rx.subjects import Subject

from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLID,
    GraphQLArgument,
    GraphQLNonNull,
    GraphQLSchema,
    GraphQLString,
    GraphQLList,
    GraphQLInt,
    parse,
    execute,
)
from graphql.execution.executors.sync import SyncExecutor
from graphql.execution.executors.thread import ThreadExecutor


@pytest.mark.parametrize(
    "executor",
    [
        SyncExecutor(),
        # ThreadExecutor(),
    ],
)
def test_batches_correctly(executor):
    # type: (SyncExecutor) -> None

    Business = GraphQLObjectType(
        "Business",
        lambda: {
            "id": GraphQLField(GraphQLID, resolver=lambda root, info, **args: root)
        },
    )

    Query = GraphQLObjectType(
        "Query",
        lambda: {
            "getBusiness": GraphQLField(
                Business,
                args={"id": GraphQLArgument(GraphQLNonNull(GraphQLID))},
                resolver=lambda root, info, **args: info.context.business_data_loader.load(
                    args.get("id")
                ),
            )
        },
    )

    schema = GraphQLSchema(query=Query)

    doc = """
{
    business1: getBusiness(id: "1") {
        id
    }
    business2: getBusiness(id: "2") {
        id
    }
}
    """
    doc_ast = parse(doc)

    load_calls = []

    class BusinessDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            # type: (List[str]) -> Promise
            load_calls.append(keys)
            return Promise.resolve(keys)

    class Context(object):
        business_data_loader = BusinessDataLoader()

    result = execute(schema, doc_ast, None, context_value=Context(), executor=executor)
    assert not result.errors
    assert result.data == {"business1": {"id": "1"}, "business2": {"id": "2"}}
    assert load_calls == [["1", "2"]]


@pytest.mark.parametrize(
    "executor",
    [
        SyncExecutor(),
        # ThreadExecutor(),  # Fails on pypy :O
    ],
)
def test_batches_multiple_together(executor):
    # type: (SyncExecutor) -> None

    Location = GraphQLObjectType(
        "Location",
        lambda: {
            "id": GraphQLField(GraphQLID, resolver=lambda root, info, **args: root)
        },
    )

    Business = GraphQLObjectType(
        "Business",
        lambda: {
            "id": GraphQLField(GraphQLID, resolver=lambda root, info, **args: root),
            "location": GraphQLField(
                Location,
                resolver=lambda root, info, **args: info.context.location_data_loader.load(
                    "location-{}".format(root)
                ),
            ),
        },
    )

    Query = GraphQLObjectType(
        "Query",
        lambda: {
            "getBusiness": GraphQLField(
                Business,
                args={"id": GraphQLArgument(GraphQLNonNull(GraphQLID))},
                resolver=lambda root, info, **args: info.context.business_data_loader.load(
                    args.get("id")
                ),
            )
        },
    )

    schema = GraphQLSchema(query=Query)

    doc = """
{
    business1: getBusiness(id: "1") {
        id
        location {
            id
        }
    }
    business2: getBusiness(id: "2") {
        id
        location {
            id
        }
    }
}
    """
    doc_ast = parse(doc)

    business_load_calls = []

    class BusinessDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            # type: (List[str]) -> Promise
            business_load_calls.append(keys)
            return Promise.resolve(keys)

    location_load_calls = []

    class LocationDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            # type: (List[str]) -> Promise
            location_load_calls.append(keys)
            return Promise.resolve(keys)

    class Context(object):
        business_data_loader = BusinessDataLoader()
        location_data_loader = LocationDataLoader()

    result = execute(schema, doc_ast, None, context_value=Context(), executor=executor)
    assert not result.errors
    assert result.data == {
        "business1": {"id": "1", "location": {"id": "location-1"}},
        "business2": {"id": "2", "location": {"id": "location-2"}},
    }
    assert business_load_calls == [["1", "2"]]
    assert location_load_calls == [["location-1", "location-2"]]


@pytest.mark.parametrize(
    "executor",
    [
        SyncExecutor(),
        # ThreadExecutor(),
    ],
)
def test_batches_subscription_result(executor):
    # type: (SyncExecutor) -> None
    Tag = namedtuple("Tag", "id,name")
    Post = namedtuple("Post", "id,tag_id")

    tags = {
        1: Tag(id=1, name="#music"),
        2: Tag(id=2, name="#beautiful"),
    }

    TagType = GraphQLObjectType(
        "Tag",
        lambda: {
            "id": GraphQLField(GraphQLInt),
            "name": GraphQLField(GraphQLString),
        },
    )

    PostType = GraphQLObjectType(
        "Post",
        lambda: {
            "id": GraphQLField(GraphQLInt),
            "tag": GraphQLField(
                TagType,
                resolver=lambda root, info: info.context.tags_data_loader.load(
                    root.tag_id
                ),
            ),
        },
    )

    new_posts_in_stream = Subject()

    Subscription = GraphQLObjectType(
        "Subscription",
        lambda: {
            "newPosts": GraphQLField(
                GraphQLList(PostType),
                resolver=lambda root, info: new_posts_in_stream,
            ),
        },
    )

    schema = GraphQLSchema(
        query=GraphQLObjectType(
            "Query",
            lambda: {"posts": GraphQLField(GraphQLList(PostType))},
        ),
        subscription=Subscription,
    )

    doc = """
        subscription {
            newPosts {
                id
                tag {
                    id
                    name
                }
            }
        }
    """
    doc_ast = parse(doc)

    load_calls = []

    class TagsDataLoader(DataLoader):
        def batch_load_fn(self, keys):
            # type: (List[str]) -> Promise
            load_calls.append(keys)
            return Promise.resolve([tags[key] for key in keys])

    class Context(object):
        tags_data_loader = TagsDataLoader()

    new_posts_out_stream = execute(
        schema,
        doc_ast,
        None,
        context_value=Context(),
        allow_subscriptions=True,
        executor=executor,
    )

    subscription_results = []
    new_posts_out_stream.subscribe(subscription_results.append)

    def create_new_posts(posts):
        Context.tags_data_loader.clear_all()
        new_posts_in_stream.on_next(posts)

    create_new_posts(
        [
            Post(id=1, tag_id=1),
            Post(id=2, tag_id=2),
            Post(id=3, tag_id=1),
        ]
    )
    create_new_posts(
        [
            Post(id=4, tag_id=1),
            Post(id=5, tag_id=1),
        ]
    )

    expected_data_1 = {
        "newPosts": [
            {"id": 1, "tag": {"id": 1, "name": "#music"}},
            {"id": 2, "tag": {"id": 2, "name": "#beautiful"}},
            {"id": 3, "tag": {"id": 1, "name": "#music"}},
        ]
    }
    expected_data_2 = {
        "newPosts": [
            {"id": 4, "tag": {"id": 1, "name": "#music"}},
            {"id": 5, "tag": {"id": 1, "name": "#music"}},
        ]
    }

    assert subscription_results[0].data == expected_data_1
    assert subscription_results[1].data == expected_data_2
    assert load_calls == [[1, 2], [1]]
