from .definition import GraphQLScalarType
from ..language import Kind

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


def coerce_int_literal(ast):
    if ast['kind'] == Kind.INT:
        num = int(ast['value'])
        if MIN_INT <= num <= MAX_INT:
            return num

GraphQLInt = GraphQLScalarType(name='Int',
                               coerce=coerce_int,
                               coerce_literal=coerce_int_literal)


def coerce_float(value):
    try:
        num = float(value)
    except ValueError:
        return None
    if num == num:  # is NaN?
        return num
    return None


def coerce_float_literal(ast):
    if ast['kind'] == Kind.FLOAT or ast['kind'] == Kind.INT:
        return float(ast['value'])
    return None

GraphQLFloat = GraphQLScalarType(name='Float',
                                 coerce=coerce_float,
                                 coerce_literal=coerce_float_literal)


def coerce_string(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def coerce_string_literal(ast):
    if ast['kind'] == Kind.STRING:
        return ast['value']
    return None

GraphQLString = GraphQLScalarType(name='String',
                                  coerce=coerce_string,
                                  coerce_literal=coerce_string_literal)


def coerce_boolean_literal(ast):
    if ast['kind'] == Kind.BOOLEAN:
        return ast['value']
    return None

GraphQLBoolean = GraphQLScalarType(name='Boolean',
                                   coerce=bool,
                                   coerce_literal=coerce_boolean_literal)


def coerce_id_literal(ast):
    if ast['kind'] == Kind.STRING or ast['kind'] == Kind.INT:
        return ast['value']
    return None

GraphQLID = GraphQLScalarType(name='ID',
                              coerce=str,
                              coerce_literal=coerce_id_literal)
