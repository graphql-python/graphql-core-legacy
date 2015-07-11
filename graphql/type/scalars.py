from graphql.type.definition import GraphQLScalarType
from graphql.language import Kind

# Integers are only safe when between -(2^53 - 1) and 2^53 - 1 due to being
# encoded in JavaScript and represented in JSON as double-precision floating
# point numbers, as specified by IEEE 754.
MAX_INT = 9007199254740991
MIN_INT = -9007199254740991

class GraphQLInt(GraphQLScalarType):
    name = 'Int'
    
    def coerce(self, value):
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

    def coerce_literal(self, ast):
        if ast['kind'] == Kind.INT:
            num = int(ast['value'])
            if MIN_INT <= num <= MAX_INT:
                return num


class GraphQLFloat(GraphQLScalarType):
    name = 'Float'
    
    def coerce(self, value):
        try:
            num = float(value)
        except ValueError:
            return None
        if num == num: # is NaN?
            return num
        return None

    def coerce_literal(self, ast):
        if ast['kind'] == Kind.FLOAT or ast['kind'] == Kind.INT:
            return float(ast['value'])
        return None


class GraphQLString(GraphQLScalarType):
    name = 'String'

    def coerce(self, value):
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

    def coerce_literal(self, ast):
        if ast['kind'] == Kind.STRING:
            return ast['value']
        return None


class GraphQLBoolean(GraphQLScalarType):
    name = 'Boolean'

    def coerce(self, value):
        return bool(value)

    def coerce_literal(self, ast):
        if ast['kind'] == Kind.BOOLEAN:
            return ast['value']
        return None


class GraphQLID(GraphQLScalarType):
    name = 'ID'

    def coerce(self, value):
        return str(value)

    def coerce_literal(self, ast):
        if ast['kind'] == Kind.STRING or ast['kind'] == Kind.INT:
            return ast['value']
        return None
