class GraphQLDirective(object):
    pass


class GraphQLIfDirective(GraphQLDirective):
    name = 'if'


class GraphQLUnlessDirective(GraphQLDirective):
    name = 'unless'
