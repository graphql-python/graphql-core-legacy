from pytest import raises
from graphql.core.type import (
    GraphQLSchema,
    GraphQLScalarType,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLInputObjectType,
    GraphQLInputObjectField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLField,
    GraphQLString
)
from graphql.core.type.definition import GraphQLArgument

_none = lambda *args: None
_true = lambda *args: True
_false = lambda *args: False

SomeScalarType = GraphQLScalarType(
    name='SomeScalar',
    serialize=_none,
    parse_value=_none,
    parse_literal=_none
)

SomeObjectType = GraphQLObjectType(
    name='SomeObject',
    fields={
        'f': GraphQLField(GraphQLString)
    }
)

ObjectWithIsTypeOf = GraphQLObjectType(
    name='ObjectWithIsTypeOf',
    is_type_of=_true,
    fields={
        'f': GraphQLField(GraphQLString)
    }
)

SomeUnionType = GraphQLUnionType(
    name='SomeUnion',
    resolve_type=_none,
    types=[SomeObjectType]
)

SomeInterfaceType = GraphQLInterfaceType(
    name='SomeInterface',
    resolve_type=_none,
    fields={
        'f': GraphQLField(GraphQLString)
    }
)

SomeEnumType = GraphQLEnumType(
    name='SomeEnum',
    values={
        'ONLY': GraphQLEnumValue()
    }
)

SomeInputObjectType = GraphQLInputObjectType(
    name='SomeInputObject',
    fields={
        'val': GraphQLInputObjectField(GraphQLString, default_value='hello')
    }
)


def with_modifiers(types):
    return (
        types +
        [GraphQLList(t) for t in types] +
        [GraphQLNonNull(t) for t in types] +
        [GraphQLNonNull(GraphQLList(t)) for t in types]
    )


output_types = with_modifiers([
    GraphQLString,
    SomeScalarType,
    SomeEnumType,
    SomeEnumType,
    SomeUnionType,
    SomeInterfaceType
])

not_output_types = with_modifiers([
    SomeInputObjectType
]) + [str]

input_types = with_modifiers([
    GraphQLString,
    SomeScalarType,
    SomeEnumType,
    SomeInputObjectType
])

not_input_types = with_modifiers([
    SomeEnumType,
    SomeUnionType,
    SomeInterfaceType
]) + [str]


def schema_with_field_type(t):
    return GraphQLSchema(
        query=GraphQLObjectType(
            name='Query',
            fields={
                'f': GraphQLField(t)
            }
        )
    )


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ASchemaMustHaveObjectRootTypes:
    def test_accepts_a_schema_whose_query_type_is_an_object_type(self):
        assert GraphQLSchema(query=SomeObjectType)

    def test_accepts_a_schema_whose_query_and_mutation_types_are_object_types(self):
        MutationType = GraphQLObjectType(
            name='Mutation',
            fields={'edit': GraphQLField(GraphQLString)}
        )

        assert GraphQLSchema(query=SomeObjectType, mutation=MutationType)

    def test_rejects_a_schema_without_a_query_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=None)

        assert str(excinfo.value) == 'Schema query must be Object Type but got: None.'

    def test_rejects_a_schema_whose_query_type_is_an_input_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=SomeInputObjectType)

        assert str(excinfo.value) == 'Schema query must be Object Type but got: SomeInputObject.'

    def test_rejects_a_schema_whose_mutation_type_is_an_input_type(self):
        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=SomeObjectType, mutation=SomeInputObjectType)

        assert str(excinfo.value) == 'Schema mutation must be Object Type but got: SomeInputObject.'


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ASchemaMustContainUniquelyNamedTypes:
    def test_it_rejects_a_schema_which_defines_a_builtin_type(self):
        FakeString = GraphQLScalarType(
            name='String',
            serialize=_none
        )

        QueryType = GraphQLObjectType(
            name='Query',
            fields={
                'normal': GraphQLField(GraphQLString),
                'fake': GraphQLField(FakeString)
            }
        )

        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=QueryType)

        assert str(excinfo.value) == 'Schema must contain unique named types but contains multiple types named ' \
                                     '"String".'

    # noinspection PyUnusedLocal
    def test_it_rejects_a_schema_which_have_same_named_objects_implementing_an_interface(self):
        AnotherInterface = GraphQLInterfaceType(
            name='AnotherInterface',
            resolve_type=_none,
            fields={
                'f': GraphQLField(GraphQLString)
            }
        )

        FirstBadObject = GraphQLObjectType(
            name='BadObject',
            interfaces=[AnotherInterface],
            fields={'f': GraphQLField(GraphQLString)}
        )

        SecondBadObject = GraphQLObjectType(
            name='BadObject',
            interfaces=[AnotherInterface],
            fields={'f': GraphQLField(GraphQLString)}
        )

        QueryType = GraphQLObjectType(
            name='Query',
            fields={
                'iface': GraphQLField(AnotherInterface)
            }
        )

        with raises(AssertionError) as excinfo:
            GraphQLSchema(query=QueryType)

        assert str(excinfo.value) == 'Schema must contain unique named types but contains multiple types named ' \
                                     '"BadObject".'


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_ObjectsMustHaveFields:
    def test_accepts_an_object_type_with_fields_object(self):
        assert schema_with_field_type(GraphQLObjectType(
            name='SomeObject',
            fields={
                'f': GraphQLField(GraphQLString)
            }
        ))

    def test_accepts_an_object_type_with_a_field_function(self):
        assert schema_with_field_type(GraphQLObjectType(
            name='SomeObject',
            fields=lambda: {
                'f': GraphQLField(GraphQLString)
            }
        ))

    def test_rejects_an_object_type_with_missing_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields=None
            ))

        assert str(excinfo.value) == 'SomeObject fields must be a mapping (dict / OrderedDict) with field names ' \
                                     'as keys or a function which returns such a mapping.'

    def test_rejects_an_object_type_with_incorrectly_named_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields={
                    'bad-name-with-dashes': GraphQLField(GraphQLString)
                }
            ))

        assert str(excinfo.value) == 'Names must match /^[_a-zA-Z][_a-zA-Z0-9]*$/ but "bad-name-with-dashes" does not.'

    def test_rejects_an_object_type_with_incorrectly_typed_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields=[
                    GraphQLField(GraphQLString)
                ]
            ))

        assert str(excinfo.value) == 'SomeObject fields must be a mapping (dict / OrderedDict) with field names ' \
                                     'as keys or a function which returns such a mapping.'

    def test_rejects_an_object_type_with_empty_fields(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields={}
            ))

        assert str(excinfo.value) == 'SomeObject fields must be a mapping (dict / OrderedDict) with field names ' \
                                     'as keys or a function which returns such a mapping.'

    def test_rejects_an_object_type_with_a_field_function_that_returns_nothing(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields=_none
            ))

        assert str(excinfo.value) == 'SomeObject fields must be a mapping (dict / OrderedDict) with field names ' \
                                     'as keys or a function which returns such a mapping.'

    def test_rejects_an_object_type_with_a_field_function_that_returns_empty(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields=lambda: {}
            ))

        assert str(excinfo.value) == 'SomeObject fields must be a mapping (dict / OrderedDict) with field names ' \
                                     'as keys or a function which returns such a mapping.'

    def test_rejects_an_object_type_with_a_field_with_an_invalid_value(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields={'f': 'hello'}
            ))

        assert str(excinfo.value) == 'SomeObject.f must be an instance of GraphQLField.'

    def test_rejects_an_object_type_with_a_field_function_with_an_invalid_value(self):
        with raises(AssertionError) as excinfo:
            schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields=lambda: {'f': 'hello'}
            ))

        assert str(excinfo.value) == 'SomeObject.f must be an instance of GraphQLField.'


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_FieldArgsMustBeProperlyNamed:
    def test_accepts_field_args_with_valid_names(self):
        assert schema_with_field_type(GraphQLObjectType(
            name='SomeObject',
            fields={
                'goodField': GraphQLField(
                    GraphQLString,
                    args={
                        'goodArg': GraphQLArgument(GraphQLString)
                    }
                )
            }
        ))

    def test_reject_field_args_with_invalid_names(self):
        with raises(AssertionError) as excinfo:
            assert schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields={
                    'badField': GraphQLField(
                        GraphQLString,
                        args={
                            'bad-name-with-dashes': GraphQLArgument(GraphQLString)
                        }
                    )
                }
            ))

        assert str(excinfo.value) == 'Names must match /^[_a-zA-Z][_a-zA-Z0-9]*$/ but "bad-name-with-dashes" does not.'


# noinspection PyMethodMayBeStatic,PyPep8Naming
class TestTypeSystem_FieldArgsMustBeObjects:
    def test_accepts_an_object_with_field_args(self):
        assert schema_with_field_type(GraphQLObjectType(
            name='SomeObject',
            fields={
                'goodField': GraphQLField(
                    GraphQLString,
                    args={
                        'goodArg': GraphQLArgument(GraphQLString)
                    }
                )
            }
        ))

    def test_rejects_an_object_with_incorrectly_typed_field_args(self):
        with raises(AssertionError) as excinfo:
            assert schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields={
                    'badField': GraphQLField(
                        GraphQLString,
                        args=[GraphQLArgument(GraphQLString)]
                    )
                }
            ))

        assert str(excinfo.value) == 'SomeObject.badField args must be a mapping (dict / OrderedDict) with argument ' \
                                     'names as keys.'

    def test_rejects_an_object_with_incorrectly_typed_field_args_with_an_invalid_value(self):
        with raises(AssertionError) as excinfo:
            assert schema_with_field_type(GraphQLObjectType(
                name='SomeObject',
                fields={
                    'badField': GraphQLField(
                        GraphQLString,
                        args={'badArg': 'I am bad!'}
                    )
                }
            ))

        assert str(excinfo.value) == 'SomeObject.badField(badArg:) argument must be an instance of GraphQLArgument.'

# describe('Type System: Object interfaces must be array', () => {
# describe('Type System: Union types must be array', () => {
# describe('Type System: Input Objects must have fields', () => {
# describe('Type System: Object types must be assertable', () => {
# describe('Type System: Interface types must be resolvable', () => {
# describe('Type System: Scalar types must be serializable', () => {
# describe('Type System: Enum types must be well defined', () => {
# describe('Type System: Object fields must have output types', () => {
# describe('Type System: Objects can only implement interfaces', () => {
# describe('Type System: Unions must represent Object types', () => {
# describe('Type System: Interface fields must have output types', () => {
# describe('Type System: Field arguments must have input types', () => {
# describe('Type System: Input Object fields must have input types', () => {
# describe('Type System: List must accept GraphQL types', () => {
# describe('Type System: NonNull must accept GraphQL types', () => {
# describe('Objects must adhere to Interface they implement', () => {
