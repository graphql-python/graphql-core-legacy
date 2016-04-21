from graphql.language.location import SourceLocation as L
from graphql.type.definition import (GraphQLArgument, GraphQLField,
                                          GraphQLInterfaceType, GraphQLList,
                                          GraphQLNonNull, GraphQLObjectType)
from graphql.type.scalars import GraphQLID, GraphQLInt, GraphQLString
from graphql.type.schema import GraphQLSchema
from graphql.validation.rules import OverlappingFieldsCanBeMerged
from .utils import (expect_fails_rule, expect_fails_rule_with_schema,
                   expect_passes_rule, expect_passes_rule_with_schema)


def fields_conflict(reason_name, reason, *locations):
    return {
        'message': OverlappingFieldsCanBeMerged.fields_conflict_message(reason_name, reason),
        'locations': list(locations)
    }


def test_unique_fields():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment uniqueFields on Dog {
        name
        nickname
    }
    ''')


def test_identical_fields():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment mergeIdenticalFields on Dog {
        name
        name
    }
    ''')


def test_identical_fields_with_identical_args():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment mergeIdenticalFieldsWithIdenticalArgs on Dog {
        doesKnowCommand(dogCommand: SIT)
        doesKnowCommand(dogCommand: SIT)
    }
    ''')


def test_identical_fields_with_identical_directives():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment mergeSameFieldsWithSameDirectives on Dog {
        name @include(if: true)
        name @include(if: true)
    }
    ''')


def test_different_args_with_different_aliases():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment differentArgsWithDifferentAliases on Dog {
        knowsSit: doesKnowCommand(dogCommand: SIT)
        knowsDown: doesKnowCommand(dogCommand: DOWN)
    }
    ''')


def test_different_directives_with_different_aliases():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment differentDirectivesWithDifferentAliases on Dog {
        nameIfTrue: name @include(if: true)
        nameIfFalse: name @include(if: false)
    }
    ''')


def test_different_skip_or_include_directives_accepted():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment differentDirectivesWithDifferentAliases on Dog {
        name @include(if: true)
        name @include(if: false)
    }
    ''')


def test_same_aliases_with_different_field_targets():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment sameAliasesWithDifferentFieldTargets on Dog {
        fido: name
        fido: nickname
    }
    ''', [
        fields_conflict('fido', 'name and nickname are different fields', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_same_aliases_allowed_on_nonoverlapping_fields():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment sameAliasesWithDifferentFieldTargets on Pet {
        ... on Dog {
            name
        }
        ... on Cat {
            name: nickname
        }
    }
    ''')


def test_alias_masking_direct_field_access():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment aliasMaskingDirectFieldAccess on Dog {
        name: nickname
        name
    }
    ''', [
        fields_conflict('name', 'nickname and name are different fields', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_diferent_args_second_adds_an_argument():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingArgs on Dog {
        doesKnowCommand
        doesKnowCommand(dogCommand: HEEL)
    }
    ''', [
        fields_conflict('doesKnowCommand', 'they have differing arguments', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_diferent_args_second_missing_an_argument():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingArgs on Dog {
        doesKnowCommand(dogCommand: SIT)
        doesKnowCommand
    }
    ''', [
        fields_conflict('doesKnowCommand', 'they have differing arguments', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_conflicting_args():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingArgs on Dog {
        doesKnowCommand(dogCommand: SIT)
        doesKnowCommand(dogCommand: HEEL)
    }
    ''', [
        fields_conflict('doesKnowCommand', 'they have differing arguments', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_allows_different_args_where_no_conflict_is_possible():
    expect_passes_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingArgs on Pet {
        ... on Dog {
            name(surname: true)
        }
        ... on Cat {
            name
        }
    }
    ''')


def test_encounters_conflict_in_fragments():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    {
        ...A
        ...B
    }
    fragment A on Type {
        x: a
    }
    fragment B on Type {
        x: b
    }
    ''', [
        fields_conflict('x', 'a and b are different fields', L(7, 9), L(10, 9))
    ], sort_list=False)


def test_reports_each_conflict_once():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    {
        f1 {
            ...A
            ...B
        }
        f2 {
            ...B
            ...A
        }
        f3 {
            ...A
            ...B
            x: c
        }
    }
    fragment A on Type {
        x: a
    }
    fragment B on Type {
        x: b
    }
    ''', [
        fields_conflict('x', 'a and b are different fields', L(18, 9), L(21, 9)),
        fields_conflict('x', 'a and c are different fields', L(18, 9), L(14, 13)),
        fields_conflict('x', 'b and c are different fields', L(21, 9), L(14, 13))
    ], sort_list=False)


def test_deep_conflict():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    {
        field {
            x: a
        }
        field {
            x: b
        }
    }
    ''', [
        fields_conflict(
            'field', [('x', 'a and b are different fields')],
            L(3, 9), L(4, 13), L(6, 9), L(7, 13))
    ], sort_list=False)


def test_deep_conflict_with_multiple_issues():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    {
        field {
            x: a
            y: c
        }
        field {
            x: b
            y: d
        }
    }
    ''', [
        fields_conflict(
            'field', [('x', 'a and b are different fields'), ('y', 'c and d are different fields')],
            L(3, 9), L(4, 13), L(5, 13), L(7, 9), L(8, 13), L(9, 13)
        )
    ], sort_list=False)


def test_very_deep_conflict():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    {
        field {
            deepField {
                x: a
            }
        },
        field {
            deepField {
                x: b
            }
        }
    }
    ''', [
        fields_conflict(
            'field', [['deepField', [['x', 'a and b are different fields']]]],
            L(3, 9), L(4, 13), L(5, 17), L(8, 9), L(9, 13), L(10, 17)
        )
    ], sort_list=False)


def test_reports_deep_conflict_to_nearest_common_ancestor():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    {
        field {
            deepField {
                x: a
            }
            deepField {
                x: b
            }
        },
        field {
            deepField {
                y
            }
        }
    }
    ''', [
        fields_conflict(
            'deepField', [('x', 'a and b are different fields')],
            L(4, 13), L(5, 17), L(7, 13), L(8, 17)
        )
    ], sort_list=False)


SomeBox = GraphQLInterfaceType('SomeBox', {
    'unrelatedField': GraphQLField(GraphQLString)
}, resolve_type=lambda *_: StringBox)

StringBox = GraphQLObjectType('StringBox', {
    'scalar': GraphQLField(GraphQLString),
    'unrelatedField': GraphQLField(GraphQLString)
}, interfaces=[SomeBox])

IntBox = GraphQLObjectType('IntBox', {
    'scalar': GraphQLField(GraphQLInt),
    'unrelatedField': GraphQLField(GraphQLString)
}, interfaces=[SomeBox])

NonNullStringBox1 = GraphQLInterfaceType('NonNullStringBox1', {
    'scalar': GraphQLField(GraphQLNonNull(GraphQLString))
}, resolve_type=lambda *_: StringBox)

NonNullStringBox1Impl = GraphQLObjectType('NonNullStringBox1Impl', {
    'scalar': GraphQLField(GraphQLNonNull(GraphQLString)),
    'unrelatedField': GraphQLField(GraphQLString)
}, interfaces=[SomeBox, NonNullStringBox1])

NonNullStringBox2 = GraphQLInterfaceType('NonNullStringBox2', {
    'scalar': GraphQLField(GraphQLNonNull(GraphQLString))
}, resolve_type=lambda *_: StringBox)

NonNullStringBox2Impl = GraphQLObjectType('NonNullStringBox2Impl', {
    'scalar': GraphQLField(GraphQLNonNull(GraphQLString)),
    'unrelatedField': GraphQLField(GraphQLString)
}, interfaces=[SomeBox, NonNullStringBox2])

Connection = GraphQLObjectType('Connection', {
    'edges': GraphQLField(GraphQLList(GraphQLObjectType('Edge', {
        'node': GraphQLField(GraphQLObjectType('Node', {
            'id': GraphQLField(GraphQLID),
            'name': GraphQLField(GraphQLString)
        }))
    })))
})

schema = GraphQLSchema(GraphQLObjectType('QueryRoot', {
    'someBox': GraphQLField(SomeBox),
    'connection': GraphQLField(Connection)
}))


def test_conflicting_return_types_which_potentially_overlap():
    expect_fails_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        someBox {
            ...on IntBox {
                scalar
            }
            ...on NonNullStringBox1 {
                scalar
            }
        }
    }

    ''', [
        fields_conflict('scalar', 'they return differing types Int and String!', L(5, 17), L(8, 17))
    ], sort_list=False)


def test_allows_differing_return_types_which_cannot_overlap():
    expect_passes_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        someBox {
            ...on IntBox {
                scalar
            }
            ...on StringBox {
                scalar
            }
        }
    }
    ''')


def test_same_wrapped_scalar_return_types():
    expect_passes_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        someBox {
            ...on NonNullStringBox1 {
              scalar
            }
            ...on NonNullStringBox2 {
              scalar
            }
        }
    }
    ''')


def test_allows_inline_typeless_fragments():
    expect_passes_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        a
        ... {
            a
        }
    }
    ''')


def test_compares_deep_types_including_list():
    expect_fails_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        connection {
            ...edgeID
            edges {
                node {
                    id: name
                }
            }
        }
    }

    fragment edgeID on Connection {
        edges {
            node {
                id
            }
        }
    }
    ''', [
        fields_conflict(
            'edges', [['node', [['id', 'id and name are different fields']]]],
            L(14, 9), L(15, 13),
            L(16, 17), L(5, 13),
            L(6, 17), L(7, 21),
        )
    ], sort_list=False)


def test_ignores_unknown_types():
    expect_passes_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        boxUnion {
            ...on UnknownType {
                scalar
            }
            ...on NonNullStringBox2 {
                scalar
            }
        }
    }
    ''')
