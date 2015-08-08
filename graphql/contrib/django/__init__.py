from graphql.api import Schema
from singledispatch import singledispatch
from django.db import models


@singledispatch
def convert_django_field(field, schema):
    raise NotImplemented


@convert_django_field.register(models.CharField)
def _(field, schema):  # flake8: noqa
    return schema.Field(schema.String)


@convert_django_field.register(models.AutoField)
def _(field, schema):  # flake8: noqa
    return schema.Field(schema.ID)


@convert_django_field.register(models.IntegerField)
def _(field, schema):  # flake8: noqa
    return schema.Field(schema.Int)


@convert_django_field.register(models.BigIntegerField)
def _(field, schema):  # flake8: noqa
    raise NotImplemented


@convert_django_field.register(models.BooleanField)
def _(field, schema):  # flake8: noqa
    return schema.Field(schema.Boolean)


@convert_django_field.register(models.FloatField)
def _(field, schema):  # flake8: noqa
    return schema.Field(schema.Float)


class DjangoSchema(Schema):
    def __init__(self):
        super(DjangoSchema, self).__init__()

    def _define_object(self, dct):
        # Override
        model = dct.get('__model__')
        if model:
            for field in model._meta.get_fields():
                if field.is_relation:
                    pass  # TODO
                else:
                    dct[field.name] = convert_django_field(field, self)
                    # ... TODO
        return super(DjangoSchema, self)._define_object(dct)
