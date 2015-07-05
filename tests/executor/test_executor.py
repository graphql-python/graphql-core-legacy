from graphql.executor import execute
from graphql.language import parse
from graphql.type import (GraphQLSchema, GraphQLObjectType, GraphQLField,
    GraphQLArgument, GraphQLList, GraphQLInt, GraphQLString)

def test_executes_arbitary_code():
    class Data(object):
        a = 'Apple'
        b = 'Banana'
        c = 'Cookie'
        d = 'Donut'
        e = 'Egg'
        f = 'Fish'

        def pic(self, size=50):
            return 'Pic of size: {}'.format(size)

        def deep(self):
            return DeepData()

        def promise(self):
            # FIXME: promise is unsupported
            return Data()


    class DeepData(object):
        a = 'Already Been Done'
        b = 'Boring'
        c = ['Contrived', None, 'Confusing']
        
        def deeper(self):
            return [Data(), None, Data()]

    doc = '''
        query Example($size: Int) {
            a,
            b,
            x: c
            ...c
            f
            ...on DataType {
                pic(size: $size)
                promise {
                    a
                }
            }
            deep {
                a
                b
                c
                deeper {
                    a
                    b
                }
            }
        }
        fragment c on DataType {
            d
            e
        }
    '''

    ast = parse(doc)
    expected = {
        'a': 'Apple',
        'b': 'Banana',
        'x': 'Cookie',
        'd': 'Donut',
        'e': 'Egg',
        'f': 'Fish',
        'pic': 'Pic of size: 100',
        'promise': { 'a': 'Apple' },
        'deep': {
          'a': 'Already Been Done',
          'b': 'Boring',
          'c': [ 'Contrived', None, 'Confusing' ],
          'deeper': [
            { 'a': 'Apple', 'b': 'Banana' },
            None,
            { 'a': 'Apple', 'b': 'Banana' } ] }
    }

    class DataType(GraphQLObjectType):
        name = 'DataType'

        def get_fields(self):
            return {
                'a': GraphQLField(GraphQLString()),
                'b': GraphQLField(GraphQLString()),
                'c': GraphQLField(GraphQLString()),
                'd': GraphQLField(GraphQLString()),
                'e': GraphQLField(GraphQLString()),
                'f': GraphQLField(GraphQLString()),
                'pic': GraphQLField(
                    args={'size': GraphQLArgument(GraphQLInt())},
                    type=GraphQLString(),
                    resolver=lambda obj, args, *_: obj.pic(args['size']),
                ),
                'deep': GraphQLField(DeepDataType()),
                'promise': GraphQLField(DataType()),
            }

    class DeepDataType(GraphQLObjectType):
        name = 'DeepDataType'
        fields = {
            'a': GraphQLField(GraphQLString()),
            'b': GraphQLField(GraphQLString()),
            'c': GraphQLField(GraphQLList(GraphQLString())),
            'deeper': GraphQLField(GraphQLList(DataType())),
        }

    schema = GraphQLSchema(query=DataType())

    assert execute(schema, Data(), ast, 'Example', {'size': 100}).data \
        == expected
