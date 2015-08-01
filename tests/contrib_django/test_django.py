import django
from django.conf import settings
from graphql import graphql
from graphql.contrib.django import DjangoSchema

settings.configure(
    DATABASES={
        'INSTALLED_APPS': [
            'graphql',
        ],
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    }
)

from django.db import models

class Human(models.Model):
    name = models.CharField()

    class Meta:
        app_label = 'graphql'

django.setup()


def test_auto_definition():
    gql = DjangoSchema()

    class HumanType(gql.ObjectType):
        __typename__ = 'Human'
        __model__ = Human

    class QueryRoot(gql.QueryRoot):
        @gql.Field(gql.List(gql.NonNull(HumanType)))
        def humans(self, *args, **kwargs):
            return [Human(name='hi')]

    result = graphql(gql.to_internal(), '''{
        humans { name }
    }''')
    assert not result.errors
    assert result.data == {
        'humans': [
            {'name': 'hi'}
        ]
    }
