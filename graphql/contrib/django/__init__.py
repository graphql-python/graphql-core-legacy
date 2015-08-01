from graphql.api import Schema
from django.db import models


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
                    if isinstance(field, models.CharField):
                        dct[field.name] = self.Field(self.String)
                    # ... TODO
        return super(DjangoSchema, self)._define_object(dct)
