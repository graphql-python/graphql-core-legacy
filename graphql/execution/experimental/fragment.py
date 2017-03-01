import functools

from promise import Promise, promise_for_dict

from ...pyutils.cached_property import cached_property
from ...pyutils.default_ordered_dict import DefaultOrderedDict
from ...pyutils.ordereddict import OrderedDict
from ...type import (GraphQLInterfaceType, GraphQLList, GraphQLNonNull,
                     GraphQLObjectType, GraphQLUnionType)
from ..base import ResolveInfo, Undefined, collect_fields, get_field_def
from ..values import get_argument_values
from ...error import GraphQLError


def is_promise(obj):
    return isinstance(obj, Promise)


def get_base_type(type):
    if isinstance(type, (GraphQLList, GraphQLNonNull)):
        return get_base_type(type.of_type)
    return type


def get_resolvers(context, type, selection_set):
    from .resolver import field_resolver
    subfield_asts = DefaultOrderedDict(list)
    visited_fragment_names = set()
    if selection_set:
        subfield_asts = collect_fields(
            context, type, selection_set,
            subfield_asts, visited_fragment_names
        )

    resolvers = []
    for response_name, field_asts in subfield_asts.items():
        field_ast = field_asts[0]
        field_name = field_ast.name.value
        field_def = get_field_def(context and context.schema, type, field_name)
        if not field_def:
            continue
        field_base_type = get_base_type(field_def.type)
        field_fragment = None
        info = ResolveInfo(
            field_name,
            field_asts,
            field_base_type,
            parent_type=type,
            schema=context and context.schema,
            fragments=context and context.fragments,
            root_value=context and context.root_value,
            operation=context and context.operation,
            variable_values=context and context.variable_values,
        )
        if isinstance(field_base_type, GraphQLObjectType):
            field_fragment = Fragment(
                type=field_base_type,
                selection_set=field_ast.selection_set,
                info=info,
                context=context
            )
        elif isinstance(field_base_type, (GraphQLInterfaceType, GraphQLUnionType)):
            field_fragment = AbstractFragment(
                abstract_type=field_base_type,
                selection_set=field_ast.selection_set,
                info=info,
                context=context
            )
        resolver = field_resolver(field_def, exe_context=context, info=info, fragment=field_fragment)
        args = get_argument_values(
            field_def.args,
            field_ast.arguments,
            context and context.variable_values
        )
        resolvers.append((response_name, resolver, args, context and context.context_value, info))
    return resolvers


class Fragment(object):

    def __init__(self, type, selection_set, context=None, info=None):
        self.type = type
        self.selection_set = selection_set
        self.context = context
        self.info = info

    @cached_property
    def partial_resolvers(self):
        return get_resolvers(
            self.context,
            self.type,
            self.selection_set
        )

    def have_type(self, root):
        return not self.type.is_type_of or self.type.is_type_of(root, self.context.context_value, self.info)

    def resolve(self, root):
        if root and not self.have_type(root):
            raise GraphQLError(
                u'Expected value of type "{}" but got: {}.'.format(self.type, type(root).__name__),
                self.info.field_asts
            )

        contains_promise = False

        final_results = OrderedDict()
        # return OrderedDict(
        #     ((field_name, field_resolver(root, field_args, context, info))
        #         for field_name, field_resolver, field_args, context, info in self.partial_resolvers)
        # )
        for response_name, field_resolver, field_args, context, info in self.partial_resolvers:

            result = field_resolver(root, field_args, context, info)
            if result is Undefined:
                continue

            if not contains_promise and is_promise(result):
                contains_promise = True

            final_results[response_name] = result

        if not contains_promise:
            return final_results

        return promise_for_dict(final_results)
        # return {
        #     field_name: field_resolver(root, field_args, context, info)
        #     for field_name, field_resolver, field_args, context, info in self.partial_resolvers
        # }

    def resolve_serially(self, root):
        def execute_field_callback(results, resolver):
            response_name, field_resolver, field_args, context, info = resolver

            result = field_resolver(root, field_args, context, info)

            if result is Undefined:
                return results

            if is_promise(result):
                def collect_result(resolved_result):
                    results[response_name] = resolved_result
                    return results

                return result.then(collect_result)

            results[response_name] = result
            return results

        def execute_field(prev_promise, resolver):
            return prev_promise.then(lambda results: execute_field_callback(results, resolver))

        return functools.reduce(execute_field, self.partial_resolvers, Promise.resolve(OrderedDict()))

    def __eq__(self, other):
        return isinstance(other, Fragment) and (
            other.type == self.type and
            other.selection_set == self.selection_set and
            other.context == self.context and
            other.info == self.info
        )


class AbstractFragment(object):

    def __init__(self, abstract_type, selection_set, context=None, info=None):
        self.abstract_type = abstract_type
        self.selection_set = selection_set
        self.context = context
        self.info = info
        self._fragments = {}

    @cached_property
    def possible_types(self):
        return self.context.schema.get_possible_types(self.abstract_type)

    def get_fragment(self, type):
        if isinstance(type, str):
            type = self.context.schema.get_type(type)

        if type not in self._fragments:
            assert type in self.possible_types, (
                'Runtime Object type "{}" is not a possible type for "{}".'
            ).format(type, self.abstract_type)
            self._fragments[type] = Fragment(type, self.selection_set, self.context, self.info)
        return self._fragments[type]

    def resolve_type(self, result):
        return_type = self.abstract_type
        context = self.context.context_value

        if return_type.resolve_type:
            return return_type.resolve_type(result, context, self.info)
        else:
            for type in self.possible_types:
                if callable(type.is_type_of) and type.is_type_of(result, context, self.info):
                    return type

    def resolve(self, root):
        _type = self.resolve_type(root)
        fragment = self.get_fragment(_type)
        return fragment.resolve(root)
