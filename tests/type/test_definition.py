from py.test import raises
from graphql.type import (
    GraphQLSchema,
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLUnionType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLInt,
    GraphQLString,
    GraphQLBoolean,
    GraphQLField,
    GraphQLArgument,
)

BlogImage = GraphQLObjectType('Image', {
    'url': GraphQLField(GraphQLString),
    'width': GraphQLField(GraphQLInt),
    'height': GraphQLField(GraphQLInt),
})

BlogAuthor = GraphQLObjectType('Author', lambda: {
    'id': GraphQLField(GraphQLString),
    'name': GraphQLField(GraphQLString),
    'pic': GraphQLField(
        BlogImage,
        args={
            'width': GraphQLArgument(GraphQLInt),
            'height': GraphQLArgument(GraphQLInt),
        }),
    'recentArticle': GraphQLField(BlogArticle)
})

BlogArticle = GraphQLObjectType('Article', lambda: {
    'id': GraphQLField(GraphQLString),
    'isPublished': GraphQLField(GraphQLBoolean),
    'author': GraphQLField(BlogAuthor),
    'title': GraphQLField(GraphQLString),
    'body': GraphQLField(GraphQLString),
})

BlogQuery = GraphQLObjectType('Query', {
    'article': GraphQLField(
        BlogArticle,
        args={
            'id': GraphQLArgument(GraphQLString),
        }),
    'feed': GraphQLField(GraphQLList(BlogArticle))
})

BlogMutation = GraphQLObjectType('Mutation', {
    'writeArticle': GraphQLField(BlogArticle)
})

ObjectType = GraphQLObjectType('Object', {})
InterfaceType = GraphQLInterfaceType('Interface')
UnionType = GraphQLUnionType('Union', [ObjectType])
EnumType = GraphQLEnumType('Enum', {})
InputObjectType = GraphQLInputObjectType('InputObject', {})


def test_defines_a_query_only_schema():
    BlogSchema = GraphQLSchema(BlogQuery)

    assert BlogSchema.get_query_type() == BlogQuery

    article_field = BlogQuery.get_fields()['article']
    assert article_field.type == BlogArticle
    assert article_field.type.name == 'Article'
    assert article_field.name == 'article'

    article_field_type = article_field.type
    assert isinstance(article_field_type, GraphQLObjectType)

    title_field = article_field_type.get_fields()['title']
    assert title_field.name == 'title'
    assert title_field.type == GraphQLString
    assert title_field.type.name == 'String'

    author_field = article_field_type.get_fields()['author']
    author_field_type = author_field.type
    assert isinstance(author_field_type, GraphQLObjectType)
    recent_article_field = author_field_type.get_fields()['recentArticle']

    assert recent_article_field.type == BlogArticle

    feed_field = BlogQuery.get_fields()['feed']
    assert feed_field.type.of_type == BlogArticle
    assert feed_field.name == 'feed'


def test_defines_a_mutation_schema():
    BlogSchema = GraphQLSchema(BlogQuery, BlogMutation)

    assert BlogSchema.get_mutation_type() == BlogMutation

    write_mutation = BlogMutation.get_fields()['writeArticle']
    assert write_mutation.type == BlogArticle
    assert write_mutation.type.name == 'Article'
    assert write_mutation.name == 'writeArticle'


def test_includes_interfaces_subtypes_in_the_type_map():
    SomeInterface = GraphQLInterfaceType('SomeInterface')
    SomeSubtype = GraphQLObjectType(
        name='SomeSubtype',
        fields={},
        interfaces=[SomeInterface]
    )
    schema = GraphQLSchema(SomeInterface)

    assert schema.get_type_map()['SomeSubtype'] == SomeSubtype


def test_stringifies_simple_types():
    assert str(GraphQLInt) == 'Int'
    assert str(BlogArticle) == 'Article'
    assert str(InterfaceType) == 'Interface'
    assert str(UnionType) == 'Union'
    assert str(EnumType) == 'Enum'
    assert str(InputObjectType) == 'InputObject'
    assert str(GraphQLNonNull(GraphQLInt)) == 'Int!'
    assert str(GraphQLList(GraphQLInt)) == '[Int]'
    assert str(GraphQLNonNull(GraphQLList(GraphQLInt))) == '[Int]!'
    assert str(GraphQLList(GraphQLNonNull(GraphQLInt))) == '[Int!]'
    assert str(GraphQLList(GraphQLList(GraphQLInt))) == '[[Int]]'


def test_identifies_input_types():
    pass # TODO


def test_identifies_output_types():
    pass # TODO


def test_prohibits_nesting_nonnull_inside_nonnull():
    with raises(Exception) as excinfo:
        GraphQLNonNull(GraphQLNonNull(GraphQLInt))
    assert 'nest' in str(excinfo.value)


def test_prohibits_putting_non_object_types_in_unions():
    bad_union_types = [
        GraphQLInt,
        GraphQLNonNull(GraphQLInt),
        GraphQLList(GraphQLInt),
        InterfaceType,
        UnionType,
        EnumType,
        InputObjectType
    ]
    for x in bad_union_types:
        with raises(Exception) as excinfo:
            GraphQLUnionType('BadUnion', [x])
        assert 'Union BadUnion may only contain object types, it cannot contain: ' + str(x) + '.' \
            == str(excinfo.value)
