from graphql.pyutils.aplus import Promise


def resolved(value):
    return Promise.fulfilled(value)


def rejected(error):
    return Promise.rejected(error)
