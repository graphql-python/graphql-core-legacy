Introduction
============

`graphql-core`_ is a Python port of `GraphQL.js`_,
the JavaScript reference implementation for GraphQL_,
a query language for APIs created by Facebook.

`GraphQL`_ consists of three parts:

* A type system that you define
* A query language that you use to query the API
* An execution and validation engine

The reference implementation closely follows the `Specification for GraphQL`_
which consists of the following sections:

* Language_
* `Type System`_
* Introspection_
* Validation_
* Execution_
* Response_

This division into subsections is reflected in the :ref:`sub-packages` of
graphql-core. Each of these sub-packages implements the aspects specified in
one of the sections of the specification.


Getting started
---------------

You can install graphql-core using pip_::

    pip install graphql-core

You can also install graphql-core with pipenv_, if you prefer that::

    pipenv install graphql-core

Now you can start using graphql-core by importing from the top-level
:mod:`graphql` package. Nearly everything defined in the sub-packages
can also be imported directly from the top-level package.

For instance, using the types defined in the :mod:`graphql.type` package,
you can define a GraphQL schema, like this simple one::

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

The :mod:`graphql.execution` package implements the mechanism for executing
GraphQL queries. The top-level :func:`graphql` and :func:`graphql_sync`
functions also parse and validate queries using the :mod:`graphql.language`
and :mod:`graphql.validation` modules.

So to validate and execute a query against our simple schema, you can do::

    from graphql import graphql_sync

    query = '{ hello }'

    print(graphql_sync(schema, query))

This will yield the following output::

    ExecutionResult(data={'hello': 'world'}, errors=None)


Reporting Issues and Contributing
---------------------------------

Please visit the `GitHub repository of graphql-core`_ if you're interested
in the current development or want to report issues or send pull requests.

.. _GraphQL: https://graphql.org/
.. _GraphQl.js: https://github.com/graphql/graphql-js
.. _GraphQl-core: https://github.com/graphql-python/graphql-core
.. _GitHub repository of graphql-core: https://github.com/graphql-python/graphql-core
.. _Specification for GraphQL: https://facebook.github.io/graphql/
.. _Language: http://facebook.github.io/graphql/draft/#sec-Language
.. _Type System: http://facebook.github.io/graphql/draft/#sec-Type-System
.. _Introspection: http://facebook.github.io/graphql/draft/#sec-Introspection
.. _Validation: http://facebook.github.io/graphql/draft/#sec-Validation
.. _Execution: http://facebook.github.io/graphql/draft/#sec-Execution
.. _Response: http://facebook.github.io/graphql/draft/#sec-Response
.. _pip: https://pip.pypa.io/
.. _pipenv: https://github.com/pypa/pipenv
