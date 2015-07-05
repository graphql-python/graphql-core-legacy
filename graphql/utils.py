from graphql.language.kinds import NAME, LIST_TYPE, NON_NULL_TYPE
from graphql.type.definition import GraphQLList, GraphQLNonNull

def type_from_ast(schema, input_type_ast):
    if input_type_ast['kind'] == LIST_TYPE:
        inner_type = type_from_ast(schema, input_type_ast['type'])
        if inner_type:
            return GraphQLList(inner_type)
        else:
            return None
    if input_type_ast['kind'] == NON_NULL_TYPE:
        inner_type = type_from_ast(schema, input_type_ast['type'])
        if inner_type:
            return GraphQLNonNull(inner_type)
        else:
            return None
    assert input_type_ast['kind'] == NAME, 'Must be a type name.'
    return schema.get_type(input_type_ast['value'])


def is_nullish(value):
    return value is None or value != value
