import django
from django.conf import settings
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
    i = models.IntegerField()
    si = models.SmallIntegerField()
    b = models.BooleanField()

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
            return [Human(id=1, name='hi', i=123, si=1, b=True)]

    result = gql.execute('''{
        humans { id, name, i, si, b }
    }''')
    assert not result.errors
    assert result.data == {
        'humans': [
            {'id': '1', 'name': 'hi', 'i': 123, 'si': 1, 'b': True}
        ]
    }
