from collections import Counter, OrderedDict

from ...error import GraphQLError
from ...type.definition import is_abstract_type
from .base import ValidationRule

try:
    # Python 2
    from itertools import izip
except ImportError:
    # Python 3
    izip = zip


class OrderedCounter(Counter, OrderedDict):
    pass


class FieldsOnCorrectType(ValidationRule):

    def enter_Field(self, node, key, parent, path, ancestors):
        type = self.context.get_parent_type()
        if not type:
            return

        field_def = self.context.get_field_def()
        if not field_def:
            # This isn't valid. Let's find suggestions, if any.
            suggested_types = []
            if is_abstract_type(type):
                schema = self.context.get_schema()
                suggested_types = get_sibling_interfaces_including_field(schema, type, node.name.value)
                suggested_types += get_implementations_including_field(schema, type, node.name.value)
            self.context.report_error(GraphQLError(
                self.undefined_field_message(node.name.value, type.name, suggested_types),
                [node]
            ))

    @staticmethod
    def undefined_field_message(field_name, type, suggested_types):
        message = 'Cannot query field "{}" on type "{}".'.format(field_name, type)
        MAX_LENGTH = 5
        if suggested_types:
            suggestions = ', '.join(['"{}"'.format(t) for t in suggested_types[:MAX_LENGTH]])
            l_suggested_types = len(suggested_types)
            if l_suggested_types > MAX_LENGTH:
                suggestions += ", and {} other types".format(l_suggested_types - MAX_LENGTH)
            message += " However, this field exists on {}.".format(suggestions)
            message += " Perhaps you meant to use an inline fragment?"
        return message


def get_implementations_including_field(schema, type, field_name):
    '''Return implementations of `type` that include `fieldName` as a valid field.'''
    return sorted(map(lambda t: t.name, filter(lambda t: field_name in t.get_fields(), schema.get_possible_types(type))))


def get_sibling_interfaces_including_field(schema, type, field_name):
    '''Go through all of the implementations of type, and find other interaces
    that they implement. If those interfaces include `field` as a valid field,
    return them, sorted by how often the implementations include the other
    interface.'''

    implementing_objects = schema.get_possible_types(type)
    suggested_interfaces = OrderedCounter()
    for t in implementing_objects:
        for i in t.get_interfaces():
            if field_name not in i.get_fields():
                continue
            suggested_interfaces[i.name] += 1
    most_common = suggested_interfaces.most_common()
    if not most_common:
        return []
    # Get first element of each list (excluding the counter int)
    return list(next(izip(*most_common)))
