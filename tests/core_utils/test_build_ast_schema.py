from graphql.core import parse
from graphql.core.utils.build_ast_schema import build_ast_schema
from graphql.core.utils.schema_printer import print_schema
from pytest import raises


def cycle_output(body, query_type, mutation_type=None):
    ast = parse(body)
    schema = build_ast_schema(ast, query_type, mutation_type)
    return '\n' + print_schema(schema)


def test_simple_type():
    body = '''
type HelloScalars {
  str: String
  int: Int
  float: Float
  id: ID
  bool: Boolean
}
'''
    output = cycle_output(body, 'HelloScalars')
    assert output == body


def test_type_modifiers():
    body = '''
type HelloScalars {
  nonNullStr: String!
  listOfStrs: [String]
  listOfNonNullStrs: [String!]
  nonNullListOfStrs: [String]!
  nonNullListOfNonNullStrs: [String!]!
}
'''
    output = cycle_output(body, 'HelloScalars')
    assert output == body


def test_recursive_type():
    body = '''
type Recurse {
  str: String
  recurse: Recurse
}
'''
    output = cycle_output(body, 'Recurse')
    assert output == body


def test_two_types_circular():
    body = '''
type TypeOne {
  str: String
  typeTwo: TypeTwo
}

type TypeTwo {
  str: String
  typeOne: TypeOne
}
'''
    output = cycle_output(body, 'TypeOne')
    assert output == body


def test_single_argument_field():
    body = '''
type Hello {
  str(int: Int): String
  floatToStr(float: Float): String
  idToStr(id: ID): String
  booleanToStr(bool: Boolean): String
  strToStr(bool: String): String
}
'''
    output = cycle_output(body, 'Hello')
    assert output == body


def test_simple_type_with_multiple_arguments():
    body = '''
type Hello {
  str(int: Int, bool: Boolean): String
}
'''
    output = cycle_output(body, 'Hello')
    assert output == body


def test_simple_type_with_interface():
    body = '''
type HelloInterface implements WorldInterface {
  str: String
}

interface WorldInterface {
  str: String
}
'''
    output = cycle_output(body, 'HelloInterface')
    assert output == body


def test_simple_output_enum():
    body = '''
enum Hello {
  WORLD
}

type OutputEnumRoot {
  hello: Hello
}
'''
    output = cycle_output(body, 'OutputEnumRoot')
    assert output == body


def test_simple_input_enum():
    body = '''
enum Hello {
  WORLD
}

type InputEnumRoot {
  str(hello: Hello): String
}
'''
    output = cycle_output(body, 'InputEnumRoot')
    assert output == body


def test_multiple_value_enum():
    body = '''
enum Hello {
  WO
  RLD
}

type OutputEnumRoot {
  hello: Hello
}
'''
    output = cycle_output(body, 'OutputEnumRoot')
    assert output == body


def test_simple_union():
    body = '''
union Hello = World

type Root {
  hello: Hello
}

type World {
  str: String
}
'''
    output = cycle_output(body, 'Root')
    assert output == body


def test_multiple_union():
    body = '''
union Hello = WorldOne | WorldTwo

type Root {
  hello: Hello
}

type WorldOne {
  str: String
}

type WorldTwo {
  str: String
}
'''
    output = cycle_output(body, 'Root')
    assert output == body


def test_custom_scalar():
    body = '''
scalar CustomScalar

type Root {
  customScalar: CustomScalar
}
'''
    output = cycle_output(body, 'Root')
    assert output == body


def test_input_object():
    body = '''
input Input {
  int: Int
}

type Root {
  field(in: Input): String
}
'''
    output = cycle_output(body, 'Root')
    assert output == body


def test_simple_argument_field_with_default():
    body = '''
type Hello {
  str(int: Int = 2): String
}
'''
    output = cycle_output(body, 'Hello')
    assert output == body


def test_simple_type_with_mutation():
    body = '''
type HelloScalars {
  str: String
  int: Int
  bool: Boolean
}

type Mutation {
  addHelloScalars(str: String, int: Int, bool: Boolean): HelloScalars
}
'''
    output = cycle_output(body, 'HelloScalars', 'Mutation')
    assert output == body


def test_unreferenced_type_implementing_referenced_interface():
    body = '''
type Concrete implements Iface {
  key: String
}

interface Iface {
  key: String
}

type Query {
  iface: Iface
}
'''
    output = cycle_output(body, 'Query')
    assert output == body


def test_unreferenced_type_implementing_referenced_union():
    body = '''
type Concrete {
  key: String
}

type Query {
  union: Union
}

union Union = Concrete
'''
    output = cycle_output(body, 'Query')
    assert output == body


def test_unknown_type_referenced():
    body = '''
type Hello {
  bar: Bar
}
'''
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc, 'Hello')

    assert 'Type Bar not found in document' in str(excinfo.value)


def test_unknown_type_in_union_list():
    body = '''
union TestUnion = Bar
type Hello { testUnion: TestUnion }
'''
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc, 'Hello')

    assert 'Type Bar not found in document' in str(excinfo.value)


def test_unknown_query_type():
    body = '''
type Hello {
  str: String
}
'''
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc, 'Wat')

    assert 'Specified query type Wat not found in document' in str(excinfo.value)


def test_unknown_mutation_type():
    body = '''
type Hello {
  str: String
}
'''
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc, 'Hello', 'Wat')

    assert 'Specified mutation type Wat not found in document' in str(excinfo.value)


def test_rejects_query_names():
    body = '''
type Hello {
  str: String
}
'''
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc, 'Foo')

    assert 'Specified query type Foo not found in document' in str(excinfo.value)


def test_rejects_fragment_names():
    body = '''fragment Foo on Type { field } '''
    doc = parse(body)
    with raises(Exception) as excinfo:
        build_ast_schema(doc, 'Foo')

    assert 'Specified query type Foo not found in document' in str(excinfo.value)
