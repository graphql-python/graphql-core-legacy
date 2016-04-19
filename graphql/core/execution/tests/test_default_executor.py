from graphql.core.execution import (Executor, get_default_executor,
                                    set_default_executor)


def test_get_and_set_default_executor():
    e1 = get_default_executor()
    e2 = get_default_executor()
    assert e1 is e2

    new_executor = Executor()

    set_default_executor(new_executor)
    assert get_default_executor() is new_executor

    set_default_executor(None)
    assert get_default_executor() is not e1
    assert get_default_executor() is not new_executor
