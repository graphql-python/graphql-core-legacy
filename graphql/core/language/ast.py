from collections import namedtuple

# Name
Name = namedtuple('Name', 'loc value')

# Document
Document = namedtuple('Document', 'loc definitions')
OperationDefinition = namedtuple('OperationDefinition', 'loc operation name variable_definitions directives selection_set')
VariableDefinition = namedtuple('VariableDefinition', 'loc variable type default_value')
Variable = namedtuple('Variable', 'loc name')
SelectionSet = namedtuple('SelectionSet', 'loc selections')
Field = namedtuple('Field', 'loc alias name arguments directives selection_set')
Argument = namedtuple('Argument', 'loc name value')

# Fragments
FragmentSpread = namedtuple('FragmentSpread', 'loc name directives')
InlineFragment = namedtuple('InlineFragment', 'loc type_condition directives selection_set')
FragmentDefinition = namedtuple('FragmentDefinition', 'loc name type_condition directives selection_set')

# Values
IntValue = namedtuple('IntValue', 'loc value')
FloatValue = namedtuple('FloatValue', 'loc value')
StringValue = namedtuple('StringValue', 'loc value')
BooleanValue = namedtuple('BooleanValue', 'loc value')
EnumValue = namedtuple('EnumValue', 'loc value')
ListValue = namedtuple('ListValue', 'loc values')
ObjectValue = namedtuple('ObjectValue', 'loc fields')
ObjectField = namedtuple('ObjectField', 'loc name value')

# Directives
Directive = namedtuple('Directive', 'loc name arguments')

# Types
NamedType = namedtuple('NamedType', 'loc name')
ListType = namedtuple('ListType', 'loc type')
NonNullType = namedtuple('NonNullType', 'loc type')
