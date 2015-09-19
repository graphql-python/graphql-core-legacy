from .definition import GraphQLScalarType
from ..language.ast import (
    IntValue,
    FloatValue,
    StringValue,
    BooleanValue,
)

# Integers are only safe when between -(2^53 - 1) and 2^53 - 1 due to being
# encoded in JavaScript and represented in JSON as double-precision floating
# point numbers, as specified by IEEE 754.
MAX_INT = 9007199254740991
MIN_INT = -9007199254740991


def coerce_int(value):
    try:
        num = int(value)
    except ValueError:
        try:
            num = int(float(value))
        except ValueError:
            return None
    if MIN_INT <= num <= MAX_INT:
        return num
    return None


def parse_int_literal(ast):
    if isinstance(ast, IntValue):
        num = int(ast.value)
        if MIN_INT <= num <= MAX_INT:
            return num

GraphQLInt = GraphQLScalarType(name='Int',
                               serialize=coerce_int,
                               parse_value=coerce_int,
                               parse_literal=parse_int_literal)


def coerce_float(value):
    try:
        num = float(value)
    except ValueError:
        return None
    if num == num:  # is NaN?
        return num
    return None


def parse_float_literal(ast):
    if isinstance(ast, (FloatValue, IntValue)):
        return float(ast.value)
    return None

GraphQLFloat = GraphQLScalarType(name='Float',
                                 serialize=coerce_float,
                                 parse_value=coerce_float,
                                 parse_literal=parse_float_literal)


def coerce_string(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def parse_string_literal(ast):
    if isinstance(ast, StringValue):
        return ast.value
    return None

GraphQLString = GraphQLScalarType(name='String',
                                  serialize=coerce_string,
                                  parse_value=coerce_string,
                                  parse_literal=parse_string_literal)


def parse_boolean_literal(ast):
    if isinstance(ast, BooleanValue):
        return ast.value
    return None

GraphQLBoolean = GraphQLScalarType(name='Boolean',
                                   serialize=bool,
                                   parse_value=bool,
                                   parse_literal=parse_boolean_literal)


def parse_id_literal(ast):
    if isinstance(ast, (StringValue, IntValue)):
        return ast.value
    return None

GraphQLID = GraphQLScalarType(name='ID',
                              serialize=str,
                              parse_value=str,
                              parse_literal=parse_id_literal)
