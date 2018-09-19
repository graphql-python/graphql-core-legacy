from textwrap import dedent

__all__ = ["get_introspection_query"]


def get_introspection_query(descriptions=True):
    """Get a query for introspection, optionally without descriptions."""
    return dedent(
        """
        query IntrospectionQuery {{
          __schema {{
            queryType {{ name }}
            mutationType {{ name }}
            subscriptionType {{ name }}
            types {{
              ...FullType
            }}
            directives {{
              name
              {}
              locations
              args {{
                ...InputValue
              }}
            }}
          }}
        }}

        fragment FullType on __Type {{
          kind
          name
          {}
          fields(includeDeprecated: true) {{
            name
            {}
            args {{
              ...InputValue
            }}
            type {{
              ...TypeRef
            }}
            isDeprecated
            deprecationReason
          }}
          inputFields {{
            ...InputValue
          }}
          interfaces {{
            ...TypeRef
          }}
          enumValues(includeDeprecated: true) {{
            name
            {}
            isDeprecated
            deprecationReason
          }}
          possibleTypes {{
            ...TypeRef
          }}
        }}

        fragment InputValue on __InputValue {{
          name
          {}
          type {{ ...TypeRef }}
          defaultValue
        }}

        fragment TypeRef on __Type {{
          kind
          name
          ofType {{
            kind
            name
            ofType {{
              kind
              name
              ofType {{
                kind
                name
                ofType {{
                  kind
                  name
                  ofType {{
                    kind
                    name
                    ofType {{
                      kind
                      name
                      ofType {{
                        kind
                        name
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """.format('description' if descriptions else '', 'description' if descriptions else '', 'description' if descriptions else '', 'description' if descriptions else '', 'description' if descriptions else '')
    )
