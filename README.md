# GraphQL-core

GraphQL-core is a Python port of [GraphQL.js](https://github.com/graphql/graphql-js),
the JavaScript reference implementation for [GraphQL](https://graphql.org/),
a query language for APIs created by Facebook.

[![PyPI version](https://badge.fury.io/py/graphql-core.svg)](https://badge.fury.io/py/graphql-core)
[![Documentation Status](https://readthedocs.org/projects/graphql-core/badge/)](https://graphql-core.readthedocs.io)
[![Build Status](https://travis-ci.com/graphql-python/graphql-core.svg?branch=master)](https://travis-ci.com/graphql-python/graphql-core)
[![Coverage Status](https://coveralls.io/repos/github/graphql-python/graphql-core/badge.svg?branch=master)](https://coveralls.io/github/graphql-python/graphql-core?branch=master)
[![Dependency Updates](https://pyup.io/repos/github/graphql-python/graphql-core/shield.svg)](https://pyup.io/repos/github/graphql-python/graphql-core/)
[![Python 3 Status](https://pyup.io/repos/github/graphql-python/graphql-core/python-3-shield.svg)](https://pyup.io/repos/github/graphql-python/graphql-core/)

The current version 1.0.1 of graphql-core is up-to-date with GraphQL.js
version 14.0.2. All parts of the API are covered by an extensive test suite of
currently 1600 unit tests.

## Documentation

A more detailed documentation for graphql-core can be found at
[graphql-core.readthedocs.io](https://graphql-core.readthedocs.io/).

There will be also [blog articles](https://cito.github.io/tags/graphql/)
with more usage examples.

## Getting started

An overview of GraphQL in general is available in the
[README](https://github.com/facebook/graphql/blob/master/README.md) for the
[Specification for GraphQL](https://github.com/facebook/graphql). That overview
describes a simple set of GraphQL examples that exist as [tests](tests)
in this repository. A good way to get started with this repository is to walk
through that README and the corresponding tests in parallel.

## Installation

graphql-core can be installed from PyPI using the built-in pip command:

    python -m pip install graphql-core

Alternatively, you can also use [pipenv](https://docs.pipenv.org/) for
installation in a virtual environment:

    pipenv install graphql-core

## Usage

graphql-core provides two important capabilities: building a type schema,
and serving queries against that type schema.

First, build a GraphQL type schema which maps to your code base:

```python
from graphql import (
    GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString)

schema = GraphQLSchema(
    query=GraphQLObjectType(
        name='RootQueryType',
        fields={
            'hello': GraphQLField(
                GraphQLString,
                resolve=lambda obj, info: 'world')
        }))
```

This defines a simple schema with one type and one field, that resolves
to a fixed value. The `resolve` function can return a value, a co-routine
object or a list of these. It takes two positional arguments; the first one
provides the root or the resolved parent field, the second one provides a
`GraphQLResolveInfo` object which contains information about the execution
state of the query, including a `context` attribute holding per-request state
such as authentication information or database session. Any GraphQL arguments
are passed to the `resolve` functions as individual keyword arguments.

Note that the signature of the resolver functions is a bit different in
GraphQL.js, where the context is passed separately and arguments are passed
as a single object. Also note that GraphQL fields must be passed as a
`GraphQLField` object explicitly. Similarly, GraphQL arguments must be
passed as `GraphQLArgument` objects.

A more complex example is included in the top level [tests](tests) directory.

Then, serve the result of a query against that type schema.

```python
from graphql import graphql_sync

query = '{ hello }'

print(graphql_sync(schema, query))
```

This runs a query fetching the one field defined, and then prints the result:

```python
ExecutionResult(data={'hello': 'world'}, errors=None)
```

The `graphql_sync` function will first ensure the query is syntactically
and semantically valid before executing it, reporting errors otherwise.

```python
from graphql import graphql_sync

query = '{ boyhowdy }'

print(graphql_sync(schema, query))
```

Because we queried a non-existing field, we will get the following result:

```python
ExecutionResult(data=None, errors=[GraphQLError(
    "Cannot query field 'boyhowdy' on type 'RootQueryType'.",
    locations=[SourceLocation(line=1, column=3)])])
```

The `graphql_sync` function assumes that all resolvers return values
synchronously. By using coroutines as resolvers, you can also create
results in an Promise-like fashion with the `graphql` function.

```python
from graphql import (
    graphql, GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString)


def resolve_hello(obj, info):
    return Promise.resolve('world')

schema = GraphQLSchema(
    query=GraphQLObjectType(
        name='RootQueryType',
        fields={
            'hello': GraphQLField(
                GraphQLString,
                resolve=resolve_hello)
        }))


def main():
    query = '{ hello }'
    print('Fetching the result...')
    result = graphql(schema, query).get()
    print(result)


main()
```

## Goals and restrictions

graphql-core tries to reproduce the code of the reference implementation
GraphQL.js in Python as closely as possible and to stay up-to-date with
the latest development of GraphQL.js.

It has been created as an alternative and potential successor to
[GraphQL-core](https://github.com/graphql-python/graphql-core),
a prior work by Syrus Akbary, based on an older version of GraphQL.js and
also targeting older Python versions. GraphQL-core also serves as as the
foundation for [Graphene](http://graphene-python.org/), a more high-level
framework for building GraphQL APIs in Python. Some parts of graphql-core
have been inspired by GraphQL-core or directly taken over with only slight
modifications, but most of the code has been re-implemented from scratch,
replicating the latest code in GraphQL.js very closely and adding type hints
for Python. Though GraphQL-core has also been updated and modernized to some
extend, it might be replaced by graphql-core in the future.

Design goals for the graphql-core library are:

-   to be a simple, cruft-free, state-of-the-art implementation of GraphQL using
    current library and language versions
-   to be very close to the GraphQL.js reference implementation, while still
    using a Pythonic API and code style
-   making use of Python type hints, similar to how GraphQL.js makes use of Flow
-   replicate the complete Mocha-based test suite of GraphQL.js using
    [pytest](https://docs.pytest.org/)

Some restrictions (mostly in line with the design goals):

-   does not support some already deprecated methods and options of GraphQL.js
-   supports asynchronous operations only via Promise's
-   the benchmarks have not been ported yet

## Changelog

Changes are tracked as
[GitHub releases](https://github.com/graphql-python/graphql-core/releases).

## Credits

The graphql-core library

-   has been created and is maintained by Syrus Akbary
-   uses ideas and code from GraphQL-core-next, a prior work by Christoph Zwerschke
-   is a Python port of GraphQL.js which has been created and is maintained
    by Facebook, Inc.

## License

graphql-core is
[MIT-licensed](https://github.com/graphql-python/graphql-core/blob/master/LICENSE).
