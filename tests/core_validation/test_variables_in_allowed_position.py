from graphql.core.language.location import SourceLocation
from graphql.core.validation.rules import VariablesInAllowedPosition
from utils import expect_passes_rule, expect_fails_rule

def test_boolean_boolean():
    expect_passes_rule(VariablesInAllowedPosition, '''
      query Query($booleanArg: Boolean)
      {
        complicatedArgs {
          booleanArgField(booleanArg: $booleanArg)
        }
      }
    ''')
def test_boolean_boolean_in_fragment():
    expect_passes_rule(VariablesInAllowedPosition, '''
      fragment booleanArgFrag on ComplicatedArgs {
        booleanArgField(booleanArg: $booleanArg)
      }
      query Query($booleanArg: Boolean)
      {
        complicatedArgs {
          ...booleanArgFrag
        }
      }
    ''')
