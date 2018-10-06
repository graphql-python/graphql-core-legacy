from pytest import mark, raises

from rx import Observable

from graphql.language import parse
from graphql.pyutils import EventEmitter, EventEmitterObservable
from graphql.type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLField,
    GraphQLInt,
    GraphQLList,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)
from graphql.subscription import subscribe

EmailType = GraphQLObjectType(
    "Email",
    {
        "from": GraphQLField(GraphQLString),
        "subject": GraphQLField(GraphQLString),
        "message": GraphQLField(GraphQLString),
        "unread": GraphQLField(GraphQLBoolean),
    },
)

InboxType = GraphQLObjectType(
    "Inbox",
    {
        "total": GraphQLField(
            GraphQLInt, resolve=lambda inbox, _info: len(inbox["emails"])
        ),
        "unread": GraphQLField(
            GraphQLInt,
            resolve=lambda inbox, _info: sum(
                1 for email in inbox["emails"] if email["unread"]
            ),
        ),
        "emails": GraphQLField(GraphQLList(EmailType)),
    },
)

QueryType = GraphQLObjectType("Query", {"inbox": GraphQLField(InboxType)})

EmailEventType = GraphQLObjectType(
    "EmailEvent", {"email": GraphQLField(EmailType), "inbox": GraphQLField(InboxType)}
)


def anext(iterable):
    """Return the next item from an async iterator."""
    # print(iterable.last_next)
    # print(dir(iterable)

    if not hasattr(iterable, "iterable"):
        return
    return next(iterable.iterable)
    # return iterable.last_value  # .first()  # .__anext__()


def email_schema_with_resolvers(subscribe_fn=None, resolve_fn=None):
    return GraphQLSchema(
        query=QueryType,
        subscription=GraphQLObjectType(
            "Subscription",
            {
                "importantEmail": GraphQLField(
                    EmailEventType,
                    args={"priority": GraphQLArgument(GraphQLInt)},
                    resolve=resolve_fn,
                    subscribe=subscribe_fn,
                )
            },
        ),
    )


email_schema = email_schema_with_resolvers()

def get_iter(subscription):
    if isinstance(subscription, Observable):
        # def on_next(value):
        #     print("ON NEXT", subscription, value)
        #     subscription.last_value = value

        # subscription.subscribe(on_next=on_next)
        blocking_subs = subscription.to_blocking()
        # subscription = subscription.subscribe()
        subscription.iterable = iter(blocking_subs)
    return subscription


def create_subscription(pubsub, schema=email_schema, ast=None, variables=None):
    data = {
        "inbox": {
            "emails": [
                {
                    "from": "joe@graphql.org",
                    "subject": "Hello",
                    "message": "Hello World",
                    "unread": False,
                }
            ]
        },
        "importantEmail": lambda _info, priority=None: EventEmitterObservable(
            pubsub, "importantEmail"
        ),
    }

    def send_important_email(new_email):
        data["inbox"]["emails"].append(new_email)
        # Returns true if the event was consumed by a subscriber.
        return pubsub.emit(
            "importantEmail",
            {"importantEmail": {"email": new_email, "inbox": data["inbox"]}},
        )

    default_ast = parse(
        """
        subscription ($priority: Int = 0) {
          importantEmail(priority: $priority) {
            email {
              from
              subject
            }
            inbox {
              unread
              total
            }
          }
        }
        """
    )

    # `subscribe` yields AsyncIterator or ExecutionResult
    subscription = subscribe(
        schema, ast or default_ast, data, variable_values=variables
    )
    subscription = get_iter(subscription)

    return (send_important_email, subscription)


# Check all error cases when initializing the subscription.
def describe_subscription_initialization_phase():
    def accepts_an_object_with_named_properties_as_arguments():
        document = parse(
            """
            subscription {
              importantEmail
            }
            """
        )

        def empty_async_iterator(_info):
            return Observable.empty()

        subscribe(email_schema, document, {"importantEmail": empty_async_iterator})

    def accepts_multiple_subscription_fields_defined_in_schema():
        pubsub = EventEmitter()
        SubscriptionTypeMultiple = GraphQLObjectType(
            "Subscription",
            {
                "importantEmail": GraphQLField(EmailEventType),
                "nonImportantEmail": GraphQLField(EmailEventType),
            },
        )

        test_schema = GraphQLSchema(
            query=QueryType, subscription=SubscriptionTypeMultiple
        )

        send_important_email, subscription = create_subscription(pubsub, test_schema)
        # assert isinstance(subscription, Observable)

        send_important_email(
            {
                "from": "yuzhi@graphql.org",
                "subject": "Alright",
                "message": "Tests are good",
                "unread": True,
            }
        )

        anext(subscription)

    def accepts_type_definition_with_sync_subscribe_function():
        pubsub = EventEmitter()

        def subscribe_email(_inbox, _info):
            return EventEmitterObservable(pubsub, "importantEmail")

        schema = GraphQLSchema(
            query=QueryType,
            subscription=GraphQLObjectType(
                "Subscription",
                {
                    "importantEmail": GraphQLField(
                        GraphQLString, subscribe=subscribe_email
                    )
                },
            ),
        )

        ast = parse(
            """
            subscription {
              importantEmail
            }
            """
        )

        subscription = subscribe(schema, ast)
        assert isinstance(subscription, Observable)

        pubsub.emit("importantEmail", {"importantEmail": {}})

        anext(subscription)

    def accepts_type_definition_with_async_subscribe_function():
        pubsub = EventEmitter()

        def subscribe_email(_inbox, _info):
            return EventEmitterObservable(pubsub, "importantEmail")

        schema = GraphQLSchema(
            query=QueryType,
            subscription=GraphQLObjectType(
                "Subscription",
                {
                    "importantEmail": GraphQLField(
                        GraphQLString, subscribe=subscribe_email
                    )
                },
            ),
        )

        ast = parse(
            """
            subscription {
              importantEmail
            }
            """
        )

        subscription = subscribe(schema, ast)
        assert isinstance(subscription, Observable)

        pubsub.emit("importantEmail", {"importantEmail": {}})

        anext(subscription)

    def should_only_resolve_the_first_field_of_invalid_multi_field():
        did_resolve = {"importantEmail": False, "nonImportantEmail": False}

        def subscribe_important(_inbox, _info):
            did_resolve["importantEmail"] = True
            return EventEmitterObservable(EventEmitter(), "event")

        def subscribe_non_important(_inbox, _info):
            did_resolve["nonImportantEmail"] = True
            return EventEmitterObservable(EventEmitter(), "event")

        SubscriptionTypeMultiple = GraphQLObjectType(
            "Subscription",
            {
                "importantEmail": GraphQLField(
                    EmailEventType, subscribe=subscribe_important
                ),
                "nonImportantEmail": GraphQLField(
                    EmailEventType, subscribe=subscribe_non_important
                ),
            },
        )

        test_schema = GraphQLSchema(
            query=QueryType, subscription=SubscriptionTypeMultiple
        )

        ast = parse(
            """
            subscription {
              importantEmail
              nonImportantEmail
            }
            """
        )

        subscription = subscribe(test_schema, ast)
        assert isinstance(subscription, Observable)
        ignored = anext(subscription)  # Ask for a result, but ignore it.
        assert did_resolve["importantEmail"] is True
        assert did_resolve["nonImportantEmail"] is False

        #         # Close subscription
        # noinspection PyUnresolvedReferences
        # subscription.dispose()

    #         with raises(StopAsyncIteration):
    #             ignored

    #     # noinspection PyArgumentList
    def throws_an_error_if_schema_is_missing():
        document = parse(
            """
            subscription {
              importantEmail
            }
            """
        )

        with raises(TypeError) as exc_info:
            # noinspection PyTypeChecker
            subscribe(None, document)

        assert str(exc_info.value) == "Expected None to be a GraphQL schema."

        with raises(TypeError) as exc_info:
            # noinspection PyTypeChecker
            subscribe(document=document)

        msg = str(exc_info.value)
        # assert "missing" in msg and "argument: 'schema'" in msg

    #     # noinspection PyArgumentList
    def throws_an_error_if_document_is_missing():
        with raises(TypeError) as exc_info:
            # noinspection PyTypeChecker
            subscribe(email_schema, None)

        assert str(exc_info.value) == "Must provide document"

        with raises(TypeError) as exc_info:
            # noinspection PyTypeChecker
            subscribe(schema=email_schema)

        msg = str(exc_info.value)
        # assert "missing" in msg and "argument: 'document'" in msg

    #     @mark.asyncio
    def resolves_to_an_error_for_unknown_subscription_field():
        ast = parse(
            """
            subscription {
              unknownField
            }
            """
        )

        pubsub = EventEmitter()

        _, subscription = create_subscription(pubsub, ast=ast)

        assert subscription == (
            None,
            [
                {
                    "message": "The subscription field 'unknownField' is not defined.",
                    "locations": [(3, 15)],
                }
            ],
        )

    def throws_an_error_if_subscribe_does_not_return_an_iterator():
        invalid_email_schema = GraphQLSchema(
            query=QueryType,
            subscription=GraphQLObjectType(
                "Subscription",
                {
                    "importantEmail": GraphQLField(
                        GraphQLString, subscribe=lambda _inbox, _info: "test"
                    )
                },
            ),
        )

        pubsub = EventEmitter()

        with raises(TypeError) as exc_info:
            create_subscription(pubsub, invalid_email_schema)

        assert str(exc_info.value) == (
            "Subscription field must return AsyncIterable or an Observable. Received: 'test'"
        )

    def resolves_to_an_error_for_subscription_resolver_errors():
        def test_reports_error(schema):
            result = subscribe(
                schema,
                parse(
                    """
                    subscription {
                      importantEmail
                    }
                    """
                ),
            )

            assert result == (
                None,
                [
                    {
                        "message": "test error",
                        "locations": [(3, 23)],
                        "path": ["importantEmail"],
                    }
                ],
            )

        # Returning an error
        def return_error(*args):
            return TypeError("test error")

        subscription_returning_error_schema = email_schema_with_resolvers(return_error)
        test_reports_error(subscription_returning_error_schema)

        # Throwing an error
        def throw_error(*args):
            raise TypeError("test error")

        subscription_throwing_error_schema = email_schema_with_resolvers(throw_error)
        test_reports_error(subscription_throwing_error_schema)

        # Resolving to an error
        def resolve_error(*args):
            return TypeError("test error")

        subscription_resolving_error_schema = email_schema_with_resolvers(resolve_error)
        test_reports_error(subscription_resolving_error_schema)

        # Rejecting with an error
        def reject_error(*args):
            return TypeError("test error")

        subscription_rejecting_error_schema = email_schema_with_resolvers(reject_error)
        test_reports_error(subscription_rejecting_error_schema)

    def resolves_to_an_error_if_variables_were_wrong_type():
        # If we receive variables that cannot be coerced correctly, subscribe()
        # will resolve to an ExecutionResult that contains an informative error
        # description.
        ast = parse(
            """
            subscription ($priority: Int) {
              importantEmail(priority: $priority) {
                email {
                  from
                  subject
                }
                inbox {
                  unread
                  total
                }
              }
            }
            """
        )

        pubsub = EventEmitter()
        data = {
            "inbox": {
                "emails": [
                    {
                        "from": "joe@graphql.org",
                        "subject": "Hello",
                        "message": "Hello World",
                        "unread": False,
                    }
                ]
            },
            "importantEmail": lambda _info: EventEmitterObservable(
                pubsub, "importantEmail"
            ),
        }

        result = subscribe(
            email_schema, ast, data, variable_values={"priority": "meow"}
        )

        result == (
            None,
            [
                {
                    "message": "Variable '$priority' got invalid value 'meow'; Expected"
                    " type Int; Int cannot represent non-integer value: 'meow'",
                    "locations": [(2, 27)],
                }
            ],
        )

        assert result.errors[0].original_error is not None


# Once a subscription returns a valid AsyncIterator, it can still yield errors.
def describe_subscription_publish_phase():
    def produces_a_payload_for_multiple_subscribe_in_same_subscription():
        pubsub = EventEmitter()
        send_important_email, subscription = create_subscription(pubsub)
        _, second_subscription = create_subscription(pubsub)

        # assert isinstance(subscription, Observable)
        # assert isinstance(second_subscription, Observable)

        assert (
            send_important_email(
                {
                    "from": "yuzhi@graphql.org",
                    "subject": "Alright",
                    "message": "Tests are good",
                    "unread": True,
                }
            )
            is True
        )
        # print(next(i))
        payload1 = anext(subscription)
        payload2 = anext(second_subscription)

        expected_payload = {
            "importantEmail": {
                "email": {"from": "yuzhi@graphql.org", "subject": "Alright"},
                "inbox": {"unread": 1, "total": 2},
            }
        }

        assert payload1 == (expected_payload, None)
        assert payload2 == (expected_payload, None)

    def produces_a_payload_per_subscription_event():
        pubsub = EventEmitter()
        send_important_email, subscription = create_subscription(pubsub)

        # Wait for the next subscription payload.

        # A new email arrives!
        assert (
            send_important_email(
                {
                    "from": "yuzhi@graphql.org",
                    "subject": "Alright",
                    "message": "Tests are good",
                    "unread": True,
                }
            )
            is True
        )

        payload = anext(subscription)

        # The previously waited on payload now has a value.
        assert payload == (
            {
                "importantEmail": {
                    "email": {"from": "yuzhi@graphql.org", "subject": "Alright"},
                    "inbox": {"unread": 1, "total": 2},
                }
            },
            None,
        )

        # Another new email arrives, before subscription.___anext__ is called.
        assert (
            send_important_email(
                {
                    "from": "hyo@graphql.org",
                    "subject": "Tools",
                    "message": "I <3 making things",
                    "unread": True,
                }
            )
            is True
        )

        # The next waited on payload will have a value.
        assert anext(subscription) == (
            {
                "importantEmail": {
                    "email": {"from": "hyo@graphql.org", "subject": "Tools"},
                    "inbox": {"unread": 2, "total": 3},
                }
            },
            None,
        )

        # The client decides to disconnect.
        # noinspection PyUnresolvedReferences
        # print(dir(subscription))
        # subscription.do_on_dispose(True)
        pubsub.complete()

        # Which may result in disconnecting upstream services as well.
        assert (
            send_important_email(
                {
                    "from": "adam@graphql.org",
                    "subject": "Important",
                    "message": "Read me please",
                    "unread": True,
                }
            )
            is False
        )  # No more listeners.

        # Awaiting subscription after closing it results in completed results.
        with raises(StopIteration):
            assert anext(subscription)


    def event_order_is_correct_for_multiple_publishes():
        pubsub = EventEmitter()
        send_important_email, subscription = create_subscription(pubsub)

        # A new email arrives!
        assert (
            send_important_email(
                {
                    "from": "yuzhi@graphql.org",
                    "subject": "Message",
                    "message": "Tests are good",
                    "unread": True,
                }
            )
            is True
        )

        # A new email arrives!
        assert (
            send_important_email(
                {
                    "from": "yuzhi@graphql.org",
                    "subject": "Message 2",
                    "message": "Tests are good 2",
                    "unread": True,
                }
            )
            is True
        )

        payload = anext(subscription)

        assert payload == (
            {
                "importantEmail": {
                    "email": {"from": "yuzhi@graphql.org", "subject": "Message"},
                    "inbox": {"unread": 1, "total": 2},
                }
            },
            None,
        )

        payload = anext(subscription)

        assert payload == (
            {
                "importantEmail": {
                    "email": {"from": "yuzhi@graphql.org", "subject": "Message 2"},
                    "inbox": {"unread": 2, "total": 3},
                }
            },
            None,
        )

    def should_handle_error_during_execution_of_source_event():
        def subscribe_fn(_event, _info):
            def gen():
                yield {"email": {"subject": "Hello"}}
                yield {"email": {"subject": "Goodbye"}}
                yield {"email": {"subject": "Bonjour"}}
            return Observable.from_(gen())

        def resolve_fn(event, _info):
            if event["email"]["subject"] == "Goodbye":
                raise RuntimeError("Never leave")
            return event

        erroring_email_schema = email_schema_with_resolvers(subscribe_fn, resolve_fn)

        subscription = get_iter(subscribe(
            erroring_email_schema,
            parse(
                """
            subscription {
              importantEmail {
                email {
                  subject
                }
              }
            }
            """
            ),
        ))

        payload1 = anext(subscription)
        assert payload1 == ({"importantEmail": {"email": {"subject": "Hello"}}}, None)

        # An error in execution is presented as such.
        payload2 = anext(subscription)
        assert payload2 == (
            {"importantEmail": None},
            [
                {
                    "message": "Never leave",
                    "locations": [(3, 15)],
                    "path": ["importantEmail"],
                }
            ],
        )

        # However that does not close the response event stream. Subsequent
        # events are still executed.
        payload3 = anext(subscription)
        assert payload3 == ({"importantEmail": {"email": {"subject": "Bonjour"}}}, None)

    # def should_pass_through_error_thrown_in_source_event_stream():
    #     def cat(err):
    #         return Observable.empty()

    #     def subscribe_fn(_event, _info):
    #         def gen():
    #             yield {"email": {"subject": "Hello"}}
    #             raise Exception("test error")
    #         return Observable.from_(gen()).catch_exception(cat)

    #     def resolve_fn(event, _info):
    #         return event

    #     erroring_email_schema = email_schema_with_resolvers(subscribe_fn, resolve_fn)

    #     subscription = get_iter(subscribe(
    #         erroring_email_schema,
    #         parse(
    #             """
    #         subscription {
    #           importantEmail {
    #             email {
    #               subject
    #             }
    #           }
    #         }
    #         """
    #         ),
    #     ))

    #     payload1 = anext(subscription)
    #     assert payload1 == ({"importantEmail": {"email": {"subject": "Hello"}}}, None)

    #     with raises(RuntimeError) as exc_info:
    #         anext(subscription)

    #     assert str(exc_info.value) == "test error"

    #     with raises(StopAsyncIteration):
    #         anext(subscription)
