import time

from graphql.execution import execute
from graphql.execution.tracing import TracingMiddleware
from graphql.language.parser import parse
from graphql.type import (GraphQLArgument, GraphQLBoolean, GraphQLField,
                          GraphQLID, GraphQLInt, GraphQLList, GraphQLNonNull,
                          GraphQLObjectType, GraphQLSchema, GraphQLString)


def test_tracing(mocker):
    time_mock = mocker.patch('time.time')
    time_mock.side_effect = range(0, 10000)

    BlogImage = GraphQLObjectType('BlogImage', {
        'url': GraphQLField(GraphQLString),
        'width': GraphQLField(GraphQLInt),
        'height': GraphQLField(GraphQLInt),
    })

    BlogAuthor = GraphQLObjectType('Author', lambda: {
        'id': GraphQLField(GraphQLString),
        'name': GraphQLField(GraphQLString),
        'pic': GraphQLField(BlogImage,
                            args={
                                'width': GraphQLArgument(GraphQLInt),
                                'height': GraphQLArgument(GraphQLInt),
                            },
                            resolver=lambda obj, info, **args:
                            obj.pic(args['width'], args['height'])
                            ),
        'recentArticle': GraphQLField(BlogArticle),
    })

    BlogArticle = GraphQLObjectType('Article', {
        'id': GraphQLField(GraphQLNonNull(GraphQLString)),
        'isPublished': GraphQLField(GraphQLBoolean),
        'author': GraphQLField(BlogAuthor),
        'title': GraphQLField(GraphQLString),
        'body': GraphQLField(GraphQLString),
        'keywords': GraphQLField(GraphQLList(GraphQLString)),
    })

    BlogQuery = GraphQLObjectType('Query', {
        'article': GraphQLField(
            BlogArticle,
            args={'id': GraphQLArgument(GraphQLID)},
            resolver=lambda obj, info, **args: Article(args['id'])),
        'feed': GraphQLField(
            GraphQLList(BlogArticle),
            resolver=lambda *_: map(Article, range(1, 2 + 1))),
    })

    BlogSchema = GraphQLSchema(BlogQuery)

    class Article(object):

        def __init__(self, id):
            self.id = id
            self.isPublished = True
            self.author = Author()
            self.title = 'My Article {}'.format(id)
            self.body = 'This is a post'
            self.hidden = 'This data is not exposed in the schema'
            self.keywords = ['foo', 'bar', 1, True, None]

    class Author(object):
        id = 123
        name = 'John Smith'

        def pic(self, width, height):
            return Pic(123, width, height)

        @property
        def recentArticle(self): return Article(1)

    class Pic(object):

        def __init__(self, uid, width, height):
            self.url = 'cdn://{}'.format(uid)
            self.width = str(width)
            self.height = str(height)

    request = '''
    {
        feed {
          id
          ...articleFields
          author {
            id
            name
          }
        },
    }
    fragment articleFields on Article {
        title,
        body,
        hidden,
    }
    '''

    # Note: this is intentionally not validating to ensure appropriate
    # behavior occurs when executing an invalid query.
    result = execute(BlogSchema, parse(request), tracing=True)
    assert not result.errors
    assert result.data == \
        {
            "feed": [
                {
                    "id": "1",
                    "title": "My Article 1",
                    "body": "This is a post",
                    "author": {
                        "id": "123",
                        "name": "John Smith"
                    }
                },
                {
                    "id": "2",
                    "title": "My Article 2",
                    "body": "This is a post",
                    "author": {
                        "id": "123",
                        "name": "John Smith"
                    }
                },
            ],
        }

    assert result.extensions['tracing'] == {
        'version': 1,
        'startTime': time.strftime(TracingMiddleware.DATETIME_FORMAT, time.gmtime(0)),
        'endTime': time.strftime(TracingMiddleware.DATETIME_FORMAT, time.gmtime(40)),
        'duration': 40000,
        'execution': {
            'resolvers': [
                {'path': ['feed'],              'parentType': 'Query',      'fieldName': 'feed',    'returnType': '[Article]',  'startOffset': 3000,  'duration': 1000},
                {'path': ['feed', 0, 'id'],     'parentType': 'Article',    'fieldName': 'id',      'returnType': 'String!',    'startOffset': 6000,  'duration': 1000},
                {'path': ['feed', 0, 'title'],  'parentType': 'Article',    'fieldName': 'title',   'returnType': 'String',     'startOffset': 9000,  'duration': 1000},
                {'path': ['feed', 0, 'body'],   'parentType': 'Article',    'fieldName': 'body',    'returnType': 'String',     'startOffset': 12000, 'duration': 1000},
                {'path': ['feed', 0, 'author'], 'parentType': 'Article',    'fieldName': 'author',  'returnType': 'Author',     'startOffset': 15000, 'duration': 1000},
                {'path': ['feed', 1, 'id'],     'parentType': 'Article',    'fieldName': 'id',      'returnType': 'String!',    'startOffset': 18000, 'duration': 1000},
                {'path': ['feed', 1, 'title'],  'parentType': 'Article',    'fieldName': 'title',   'returnType': 'String',     'startOffset': 21000, 'duration': 1000},
                {'path': ['feed', 1, 'body'],   'parentType': 'Article',    'fieldName': 'body',    'returnType': 'String',     'startOffset': 24000, 'duration': 1000},
                {'path': ['feed', 1, 'author'], 'parentType': 'Article',    'fieldName': 'author',  'returnType': 'Author',     'startOffset': 27000, 'duration': 1000},
                {'path': ['feed', 0, 'author', 'id'],   'parentType': 'Author', 'fieldName': 'id',  'returnType': 'String',     'startOffset': 30000, 'duration': 1000},
                {'path': ['feed', 0, 'author', 'name'], 'parentType': 'Author', 'fieldName': 'name', 'returnType': 'String',    'startOffset': 33000, 'duration': 1000},
                {'path': ['feed', 1, 'author', 'id'],   'parentType': 'Author', 'fieldName': 'id',   'returnType': 'String',    'startOffset': 36000, 'duration': 1000},
                {'path': ['feed', 1, 'author', 'name'], 'parentType': 'Author', 'fieldName': 'name', 'returnType': 'String',    'startOffset': 39000, 'duration': 1000}
            ]
        }
    }

