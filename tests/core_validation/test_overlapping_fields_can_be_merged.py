from graphql.core.language.location import SourceLocation as L
from graphql.core.type.definition import GraphQLObjectType, GraphQLArgument, GraphQLNonNull, GraphQLUnionType, \
    GraphQLList, GraphQLField
from graphql.core.type.scalars import GraphQLString, GraphQLInt, GraphQLID
from graphql.core.type.schema import GraphQLSchema
from graphql.core.validation.rules import OverlappingFieldsCanBeMerged
from utils import expect_passes_rule, expect_fails_rule, expect_fails_rule_with_schema, expect_passes_rule_with_schema


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


def test_same_aliases_with_different_field_targets():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment sameAliasesWithDifferentFieldTargets on Dog {
        fido: name
        fido: nickname
    }
    ''', [
        fields_conflict('fido', 'name and nickname are different fields', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_alias_masking_direct_field_access():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment aliasMaskingDirectFieldAccess on Dog {
        name: nickname
        name
    }
    ''', [
        fields_conflict('name', 'nickname and name are different fields', L(3, 9), L(4, 9))
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


def test_conflicting_directives():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingDirectiveArgs on Dog {
        name @include(if: true)
        name @skip(if: false)
    }
    ''', [
        fields_conflict('name', 'they have differing directives', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_conflicting_directive_args():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingDirectiveArgs on Dog {
        name @include(if: true)
        name @include(if: false)
    }
    ''', [
        fields_conflict('name', 'they have differing directives', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_conflicting_args_with_matching_directives():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingArgsWithMatchingDirectiveArgs on Dog {
        doesKnowCommand(dogCommand: SIT) @include(if: true)
        doesKnowCommand(dogCommand: HEEL) @include(if: true)
    }
    ''', [
        fields_conflict('doesKnowCommand', 'they have differing arguments', L(3, 9), L(4, 9))
    ], sort_list=False)


def test_conflicting_directives_with_matching_args():
    expect_fails_rule(OverlappingFieldsCanBeMerged, '''
    fragment conflictingDirectiveArgsWithMatchingArgs on Dog {
        doesKnowCommand(dogCommand: SIT) @include(if: true)
        doesKnowCommand(dogCommand: SIT) @skip(if: false)
    }
    ''', [
        fields_conflict('doesKnowCommand', 'they have differing directives', L(3, 9), L(4, 9))
    ], sort_list=False)


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
            L(3, 9), L(6, 9), L(4, 13), L(7, 13))
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
            L(3, 9), L(7, 9), L(4, 13), L(8, 13), L(5, 13), L(9, 13)
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
            L(3, 9), L(8, 9), L(4, 13), L(9, 13), L(5, 17), L(10, 17)
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
            L(4, 13), L(7, 13), L(5, 17), L(8, 17)
        )
    ], sort_list=False)


StringBox = GraphQLObjectType('StringBox', {
    'scalar': GraphQLField(GraphQLString)
})

IntBox = GraphQLObjectType('IntBox', {
    'scalar': GraphQLField(GraphQLInt)
})

NonNullStringBox1 = GraphQLObjectType('NonNullStringBox1', {
    'scalar': GraphQLField(GraphQLNonNull(GraphQLString))
})

NonNullStringBox2 = GraphQLObjectType('NonNullStringBox2', {
    'scalar': GraphQLField(GraphQLNonNull(GraphQLString))
})

BoxUnion = GraphQLUnionType('BoxUnion', [
    StringBox, IntBox, NonNullStringBox1, NonNullStringBox2
], resolve_type=lambda *_: StringBox)

Connection = GraphQLObjectType('Connection', {
    'edges': GraphQLField(GraphQLList(GraphQLObjectType('Edge', {
        'node': GraphQLField(GraphQLObjectType('Node', {
            'id': GraphQLField(GraphQLID),
            'name': GraphQLField(GraphQLString)
        }))
    })))
})

schema = GraphQLSchema(GraphQLObjectType('QueryRoot', {
    'boxUnion': GraphQLField(BoxUnion),
    'connection': GraphQLField(Connection)
}))


def test_conflicting_scalar_return_types():
    expect_fails_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        boxUnion {
            ...on IntBox {
                scalar
            }
            ...on StringBox {
                scalar
            }
        }
    }

    ''', [
        fields_conflict('scalar', 'they return differing types Int and String', L(5, 17), L(8, 17))
    ], sort_list=False)


def test_same_wrapped_scalar_return_types():
    expect_passes_rule_with_schema(schema, OverlappingFieldsCanBeMerged, '''
    {
        boxUnion {
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
            L(14, 9), L(5, 13),
            L(15, 13), L(6, 17),
            L(16, 17), L(7, 21),
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
