from ..type.definition import (GraphQLInterfaceType, GraphQLList, GraphQLNonNull,
                               GraphQLObjectType, GraphQLUnionType,
                               is_abstract_type)


def is_equal_type(type_a, type_b):
    if type_a is type_b:
        return True

    if isinstance(type_a, GraphQLNonNull) and isinstance(type_b, GraphQLNonNull):
        return is_equal_type(type_a.of_type, type_b.of_type)

    if isinstance(type_a, GraphQLList) and isinstance(type_b, GraphQLList):
        return is_equal_type(type_a.of_type, type_b.of_type)

    return False


def is_type_sub_type_of(maybe_subtype, super_type):
    if maybe_subtype is super_type:
        return True

    if isinstance(super_type, GraphQLNonNull):
        if isinstance(maybe_subtype, GraphQLNonNull):
            return is_type_sub_type_of(maybe_subtype.of_type, super_type.of_type)
        return False
    elif isinstance(maybe_subtype, GraphQLNonNull):
        return is_type_sub_type_of(maybe_subtype.of_type, super_type)

    if isinstance(super_type, GraphQLList):
        if isinstance(maybe_subtype, GraphQLList):
            return is_type_sub_type_of(maybe_subtype.of_type, super_type.of_type)
        return False
    elif isinstance(maybe_subtype, GraphQLList):
        return False

    if is_abstract_type(super_type) and isinstance(maybe_subtype,
                                                   GraphQLObjectType) and super_type.is_possible_type(maybe_subtype):
        return True

    return False


def do_types_overlap(t1, t2):
    if t1 == t2:
        return True
    if isinstance(t1, GraphQLObjectType):
        if isinstance(t2, GraphQLObjectType):
            return False
        return t1 in t2.get_possible_types()
    if isinstance(t1, GraphQLInterfaceType) or isinstance(t1, GraphQLUnionType):
        if isinstance(t2, GraphQLObjectType):
            return t2 in t1.get_possible_types()

        t1_type_names = {possible_type.name: possible_type for possible_type in t1.get_possible_types()}
        return any(t.name in t1_type_names for t in t2.get_possible_types())
