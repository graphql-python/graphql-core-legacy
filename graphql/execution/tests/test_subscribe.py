from collections import OrderedDict, namedtuple

from rx import Observable, Observer
from rx.subjects import Subject

from graphql import (GraphQLBoolean, GraphQLField, GraphQLInt, GraphQLList,
                     GraphQLObjectType, GraphQLSchema, GraphQLString, graphql,
                     parse, subscribe)

Email = namedtuple('Email', 'from_,subject,message,unread')

EmailType = GraphQLObjectType(
    name='Email',
    fields=OrderedDict([
        ('from', GraphQLField(GraphQLString, resolver=lambda x, info: x.from_)),
        ('subject', GraphQLField(GraphQLString)),
        ('message', GraphQLField(GraphQLString)),
        ('unread', GraphQLField(GraphQLBoolean)),
    ])
)

InboxType = GraphQLObjectType(
    name='Inbox',
    fields=OrderedDict([
        ('total', GraphQLField(GraphQLInt,
                               resolver=lambda inbox, context: len(inbox.emails))),
        ('unread', GraphQLField(GraphQLInt,
                                resolver=lambda inbox, context: len([e for e in inbox.emails if e.unread]))),
        ('emails', GraphQLField(GraphQLList(EmailType))),
    ])
)

QueryType = GraphQLObjectType(
    name='Query',
    fields=OrderedDict([
        ('inbox', GraphQLField(InboxType)),
    ])
)

EmailEventType = GraphQLObjectType(
    name='EmailEvent',
    fields=OrderedDict([
        ('email', GraphQLField(EmailType,
                               resolver=lambda root, info: root[0])),
        ('inbox', GraphQLField(InboxType,
                               resolver=lambda root, info: root[1])),
    ])
)


def get_unbound_function(func):
    if not getattr(func, '__self__', True):
        return func.__func__
    return func


def email_schema_with_resolvers(resolve_fn=None):
    def default_resolver(root, info):
        func = getattr(root, 'importantEmail', None)
        if func:
            func = get_unbound_function(func)
            return func()
        return Observable.empty()

    return GraphQLSchema(
        query=QueryType,
        subscription=GraphQLObjectType(
            name='Subscription',
            fields=OrderedDict([
                ('importantEmail', GraphQLField(
                    EmailEventType,
                    resolver=resolve_fn or default_resolver,
                ))
            ])
        )
    )


email_schema = email_schema_with_resolvers()


class MyObserver(Observer):
    def on_next(self, value):
        self.has_on_next = value

    def on_error(self, err):
        self.has_on_error = err

    def on_completed(self):
        self.has_on_completed = True


def create_subscription(stream, schema=email_schema, ast=None, vars=None):
    class Root(object):
        class inbox(object):
            emails = [
                Email(
                    from_='joe@graphql.org',
                    subject='Hello',
                    message='Hello World',
                    unread=False,
                )
            ]

        def importantEmail():
            return stream

    def send_important_email(new_email):
        Root.inbox.emails.append(new_email)
        stream.on_next((new_email, Root.inbox))
        # stream.on_completed()

    default_ast = parse('''
    subscription {
      importantEmail {
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
  ''')

    return send_important_email, graphql(
        schema,
        ast or default_ast,
        Root,
        None,
        vars,
        allow_subscriptions=True,
    )


def test_accepts_an_object_with_named_properties_as_arguments():
    document = parse('''
      subscription {
        importantEmail
      }
  ''')
    result = subscribe(
        email_schema,
        document,
        root_value=None
    )
    assert isinstance(result, Observable)


def test_accepts_multiple_subscription_fields_defined_in_schema():
    SubscriptionTypeMultiple = GraphQLObjectType(
        name='Subscription',
        fields=OrderedDict([
            ('importantEmail', GraphQLField(EmailEventType)),
            ('nonImportantEmail', GraphQLField(EmailEventType)),
        ])
    )
    test_schema = GraphQLSchema(
        query=QueryType,
        subscription=SubscriptionTypeMultiple
    )

    stream = Subject()
    send_important_email, subscription = create_subscription(
        stream, test_schema)

    email = Email(
        from_='yuzhi@graphql.org',
        subject='Alright',
        message='Tests are good',
        unread=True,
    )
    l = []
    stream.subscribe(l.append)
    send_important_email(email)
    assert l[0][0] == email


def test_accepts_type_definition_with_sync_subscribe_function():
    SubscriptionType = GraphQLObjectType(
        name='Subscription',
        fields=OrderedDict([
            ('importantEmail', GraphQLField(
                EmailEventType, resolver=lambda *_: Observable.from_([None]))),
        ])
    )
    test_schema = GraphQLSchema(
        query=QueryType,
        subscription=SubscriptionType
    )

    stream = Subject()
    send_important_email, subscription = create_subscription(
        stream, test_schema)

    email = Email(
        from_='yuzhi@graphql.org',
        subject='Alright',
        message='Tests are good',
        unread=True,
    )
    l = []
    subscription.subscribe(l.append)
    send_important_email(email)

    assert l  # [0].data == {'importantEmail': None}


def test_throws_an_error_if_subscribe_does_not_return_an_iterator():
    SubscriptionType = GraphQLObjectType(
        name='Subscription',
        fields=OrderedDict([
            ('importantEmail', GraphQLField(
                EmailEventType, resolver=lambda *_: None)),
        ])
    )
    test_schema = GraphQLSchema(
        query=QueryType,
        subscription=SubscriptionType
    )

    stream = Subject()
    _, subscription = create_subscription(
        stream, test_schema)

    assert str(
        subscription.errors[0]) == 'Subscription must return Async Iterable or Observable. Received: None'


def test_returns_an_error_if_subscribe_function_returns_error():
    exc = Exception("Throw!")

    def thrower(root, info):
        raise exc

    erroring_email_schema = email_schema_with_resolvers(thrower)
    result = subscribe(erroring_email_schema, parse('''
        subscription {
          importantEmail
        }
    '''))

    assert result.errors == [exc]


# Subscription Publish Phase
def test_produces_a_payload_for_multiple_subscribe_in_same_subscription():
    stream = Subject()
    send_important_email, subscription1 = create_subscription(stream)
    subscription2 = create_subscription(stream)[1]

    payload1 = []
    payload2 = []

    subscription1.subscribe(payload1.append)
    subscription2.subscribe(payload2.append)

    email = Email(
        from_='yuzhi@graphql.org',
        subject='Alright',
        message='Tests are good',
        unread=True,
    )

    send_important_email(email)
    expected_payload = {
        'importantEmail': {
            'email': {
                'from': 'yuzhi@graphql.org',
                'subject': 'Alright',
            },
            'inbox': {
                'unread': 1,
                'total': 2,
            },
        }
    }

    assert payload1[0].data == expected_payload
    assert payload2[0].data == expected_payload


# Subscription Publish Phase
def test_produces_a_payload_per_subscription_event():
    stream = Subject()
    send_important_email, subscription = create_subscription(stream)

    payload = []

    subscription.subscribe(payload.append)
    send_important_email(Email(
        from_='yuzhi@graphql.org',
        subject='Alright',
        message='Tests are good',
        unread=True,
    ))
    expected_payload = {
        'importantEmail': {
            'email': {
                'from': 'yuzhi@graphql.org',
                'subject': 'Alright',
            },
            'inbox': {
                'unread': 1,
                'total': 2,
            },
        }
    }

    assert len(payload) == 1
    assert payload[0].data == expected_payload

    send_important_email(Email(
        from_='hyo@graphql.org',
        subject='Tools',
        message='I <3 making things',
        unread=True,
    ))
    expected_payload = {
        'importantEmail': {
            'email': {
                'from': 'hyo@graphql.org',
                'subject': 'Tools',
            },
            'inbox': {
                'unread': 2,
                'total': 3,
            },
        }
    }

    assert len(payload) == 2
    assert payload[-1].data == expected_payload

    # The client decides to disconnect
    stream.on_completed()

    send_important_email(Email(
        from_='adam@graphql.org',
        subject='Important',
        message='Read me please',
        unread=True,
    ))

    assert len(payload) == 2


def test_event_order_is_correct_for_multiple_publishes():
    stream = Subject()
    send_important_email, subscription = create_subscription(stream)

    payload = []

    subscription.subscribe(payload.append)
    send_important_email(Email(
        from_='yuzhi@graphql.org',
        subject='Message',
        message='Tests are good',
        unread=True,
    ))
    send_important_email(Email(
        from_='yuzhi@graphql.org',
        subject='Message 2',
        message='Tests are good 2',
        unread=True,
    ))

    expected_payload1 = {
        'importantEmail': {
            'email': {
                'from': 'yuzhi@graphql.org',
                'subject': 'Message',
            },
            'inbox': {
                'unread': 1,
                'total': 2,
            },
        }
    }

    expected_payload2 = {
        'importantEmail': {
            'email': {
                'from': 'yuzhi@graphql.org',
                'subject': 'Message 2',
            },
            'inbox': {
                'unread': 2,
                'total': 3,
            },
        }
    }

    assert len(payload) == 2
    print(payload)
    assert payload[0].data == expected_payload1
    assert payload[1].data == expected_payload2
