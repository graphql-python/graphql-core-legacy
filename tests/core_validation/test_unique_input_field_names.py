from graphql.core.language.location import SourceLocation as L
from graphql.core.validation.rules import UniqueInputFieldNames
from utils import expect_passes_rule, expect_fails_rule


def duplicate_field(name, l1, l2):
    return {
        'message': UniqueInputFieldNames.duplicate_input_field_message(name),
        'locations': [l1, l2]
    }


def test_input_object_with_fields():
    expect_passes_rule(UniqueInputFieldNames, '''
    {
        field(arg: { f: true })
    }
    ''')


def test_same_input_object_within_two_args():
    expect_passes_rule(UniqueInputFieldNames, '''
    {
        field(arg1: { f: true }, arg2: { f: true })
    }
    ''')


def test_multiple_input_object_fields():
    expect_passes_rule(UniqueInputFieldNames, '''
    {
        field(arg: { f1: "value", f2: "value", f3: "value" })
    }
    ''')


def test_duplicate_input_object_fields():
    expect_fails_rule(UniqueInputFieldNames, '''
    {
        field(arg: { f1: "value", f1: "value" })
    }
    ''', [
        duplicate_field("f1", L(3, 22), L(3, 35))
    ])


def test_many_duplicate_input_object_fields():
    expect_fails_rule(UniqueInputFieldNames, '''
    {
        field(arg: { f1: "value", f1: "value", f1: "value" })
    }
    ''', [
        duplicate_field('f1', L(3, 22), L(3, 35)),
        duplicate_field('f1', L(3, 22), L(3, 48))
    ])