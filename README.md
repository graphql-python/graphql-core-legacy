# GraphQL-core

GraphQL for Python.

*This library is a port of [graphql-js](https://github.com/graphql/graphql-js) to Python and currently is up-to-date with release [0.6.0](https://github.com/graphql/graphql-js/releases/tag/v0.6.0).*


[![PyPI version](https://badge.fury.io/py/graphql-core.svg)](https://badge.fury.io/py/graphql-core)
[![Build Status](https://travis-ci.org/graphql-python/graphql-core.svg?branch=master)](https://travis-ci.org/graphql-python/graphql-core)
[![Coverage Status](https://coveralls.io/repos/graphql-python/graphql-core/badge.svg?branch=master&service=github)](https://coveralls.io/github/graphql-python/graphql-core?branch=master)
[![Public Slack Discussion](https://graphql-slack.herokuapp.com/badge.svg)](https://graphql-slack.herokuapp.com/)

See more complete documentation at http://graphql.org/ and
http://graphql.org/docs/api-reference-graphql/.

For questions, ask [Stack Overflow](http://stackoverflow.com/questions/tagged/graphql).

## Getting Started

An overview of the GraphQL language is available in the 
[README](https://github.com/facebook/graphql/blob/master/README.md) for the
[Specification for GraphQL](https://github.com/facebook/graphql). 

The overview describes a simple set of GraphQL examples that exist as [tests](https://github.com/graphql-python/graphql-core/tree/master/tests/)
in this repository. A good way to get started is to walk through that README and the corresponding tests
in parallel. 

### Using graphql-core

Install from pip:

```sh
pip install graphql-core
```

GraphQL.js provides two important capabilities: building a type schema, and
serving queries against that type schema.

First, build a GraphQL type schema which maps to your code base.

```python
from graphql import (
    graphql,
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString
)

schema = GraphQLSchema(
  query= GraphQLObjectType(
    name='RootQueryType',
    fields={
      'hello': GraphQLField(
        type= GraphQLString,
        resolver=lambda *_: 'world'
      )
    }
  )
)
```

This defines a simple schema with one type and one field, that resolves
to a fixed value. The `resolve` function can return a value, a promise,
or an array of promises. A more complex example is included in the top
level [tests](https://github.com/graphql-python/graphql-core/tree/master/tests/) directory.

Then, serve the result of a query against that type schema.

```python
query = '{ hello }'

result = graphql(schema, query)

# Prints
# {'hello': 'world'} (as OrderedDict)

print result.data
```

This runs a query fetching the one field defined. The `graphql` function will
first ensure the query is syntactically and semantically valid before executing
it, reporting errors otherwise.

```python
query = '{ boyhowdy }'

result = graphql(schema, query)

# Prints
# [GraphQLError('Cannot query field "boyhowdy" on type "RootQueryType".',)]

print result.errors
```

### Executors

The graphql query is executed, by default, synchronously (using `SyncExecutor`).
However the following executors are available if we want to resolve our fields in parallel:

* `graphql.execution.executors.asyncio.AsyncioExecutor`: This executor executes the resolvers in the Python asyncio event loop.
* `graphql.execution.executors.gevent.GeventExecutor`: This executor executes the resolvers in the Gevent event loop.
* `graphql.execution.executors.process.ProcessExecutor`: This executor executes each resolver as a process.
* `graphql.execution.executors.thread.ThreadExecutor`: This executor executes each resolver in a Thread.
* `graphql.execution.executors.sync.SyncExecutor`: This executor executes each resolver synchronusly (default).

#### Usage

You can specify the executor to use via the executor keyword argument in the `grapqhl.execution.execute` function.

```python
from graphql.execution.execute import execute

execute(schema, ast, executor=SyncExecutor())
```

### Development

Install development and test dependencies:

```sh
pip install -e ".[test]"
```

Run test suite:

```sh
pytest
```

## Main Contributors

 * [@syrusakbary](https://github.com/syrusakbary/)
 * [@jhgg](https://github.com/jhgg/)
 * [@dittos](https://github.com/dittos/)

## License

[MIT License](https://github.com/graphql-python/graphql-core/blob/master/LICENSE)
