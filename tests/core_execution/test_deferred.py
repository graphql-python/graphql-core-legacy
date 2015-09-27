from pytest import raises
from graphql.core.defer import Deferred, DeferredException, succeed, fail, DeferredList, DeferredDict, \
    AlreadyCalledDeferred


def test_succeed():
    d = succeed("123")
    assert d.result == "123"
    assert d.called
    assert not d.callbacks


def test_fail_none():
    d = fail()
    assert isinstance(d.result, DeferredException)
    assert d.called
    assert not d.callbacks


def test_fail_none_catches_exception():
    e = Exception('will be raised')
    try:
        raise e
    except:
        d = fail()
        assert d.called
        assert isinstance(d.result, DeferredException)
        assert d.result.value == e


def test_fail():
    e = Exception('failed')
    d = fail(e)
    assert isinstance(d.result, DeferredException)
    assert d.result.value == e
    assert d.called
    assert not d.callbacks


def test_nested_succeed():
    d = succeed(succeed('123'))
    assert d.result == "123"
    assert d.called
    assert not d.callbacks

    d = succeed(succeed(succeed('123')))
    assert d.result == "123"
    assert d.called
    assert not d.callbacks


def test_callback_result_transformation():
    d = succeed(5)
    d.add_callback(lambda r: r + 5)
    assert d.result == 10

    d.add_callback(lambda r: succeed(r + 5))

    assert d.result == 15


def test_deferred_list():
    d = Deferred()

    dl = DeferredList([
        1,
        d
    ])

    assert not dl.called
    d.callback(2)

    assert dl.called
    assert dl.result == [1, 2]


def test_deferred_list_with_already_resolved_deferred_values():
    dl = DeferredList([
        1,
        succeed(2),
        succeed(3)
    ])

    assert dl.called
    assert dl.result == [1, 2, 3]


def test_deferred_dict():
    d = Deferred()

    dd = DeferredDict({
        'a': 1,
        'b': d
    })

    assert not dd.called
    d.callback(2)

    assert dd.called
    assert dd.result == {'a': 1, 'b': 2}


def test_deferred_list_of_no_defers():
    dl = DeferredList([
        {'ab': 1},
        2,
        [1, 2, 3],
        "345"
    ])

    assert dl.called
    assert dl.result == [
        {'ab': 1},
        2,
        [1, 2, 3],
        "345"
    ]


def test_callback_resolution():
    d = Deferred()
    d.add_callback(lambda r: fail(Exception(r + "b")))
    d.add_errback(lambda e: e.value.args[0] + "c")
    d.add_callbacks(lambda r: r + "d", lambda e: e.value.args[0] + 'f')

    d.callback("a")

    assert d.result == "abcd"


def test_callback_resolution_weaving():
    d = Deferred()
    d.add_callbacks(lambda r: fail(Exception(r + "b")), lambda e: e.value.args[0] + 'w')
    d.add_callbacks(lambda e: Exception(e + "x"), lambda e: e.value.args[0] + "c")
    d.add_callbacks(lambda r: Exception(r + "d"), lambda e: e.value.args[0] + 'y')
    d.add_callbacks(lambda r: r + "z", lambda e: e.value.args[0] + 'e')

    d.callback("a")

    assert d.result == "abcde"


def test_callback_resolution_weaving_2():
    d = Deferred()
    d.add_callbacks(lambda r: fail(Exception(r + "b")), lambda e: e.value.args[0] + 'w')
    d.add_callbacks(lambda e: Exception(e + "x"), lambda e: e.value.args[0] + "c")
    d.add_callbacks(lambda r: Exception(r + "d"), lambda e: e.value.args[0] + 'y')
    d.add_callbacks(lambda r: fail(ValueError(r + "z")), lambda e: e.value.args[0] + 'e')

    d.errback(Exception('v'))

    assert isinstance(d.result, DeferredException)
    assert isinstance(d.result.value, ValueError)
    assert d.result.value.args[0] == "vwxyz"


def test_callback_raises_exception():
    def callback(val):
        raise AttributeError(val)

    d = Deferred()
    d.add_callback(callback)
    d.callback('test')

    assert isinstance(d.result, DeferredException)
    assert isinstance(d.result.value, AttributeError)
    assert d.result.value.args[0] == "test"


def test_errback():
    holder = []
    d = Deferred()
    e = Exception('errback test')
    d.add_errback(lambda e: holder.append(e))
    d.errback(e)

    assert isinstance(holder[0], DeferredException)
    assert holder[0].value == e


def test_errback_chain():
    holder = []
    d = Deferred()
    e = Exception('a')
    d.add_callbacks(holder.append, lambda e: Exception(e.value.args[0] + 'b'))
    d.add_callbacks(holder.append, lambda e: Exception(e.value.args[0] + 'c'))

    d.errback(e)

    assert d.result.value.args[0] == 'abc'
    assert len(holder) == 0


def test_deferred_list_fails():
    d1 = Deferred()
    d2 = Deferred()
    d3 = Deferred()

    dl = DeferredList([
        1,
        succeed(2),
        d1,
        d2,
        d3
    ])

    assert not dl.called

    e1 = Exception('d1 failed')
    d1.errback(e1)
    d2.errback(Exception('d2 failed'))
    d3.callback('hello')

    assert dl.called
    assert isinstance(dl.result, DeferredException)
    assert dl.result.value == e1


def test_cant_callback_twice():
    d1 = Deferred()
    d1.callback('hello')

    with raises(AlreadyCalledDeferred):
        d1.callback('world')


def test_cant_errback_twice():
    d1 = Deferred()
    d1.errback(Exception('hello'))

    with raises(AlreadyCalledDeferred):
        d1.errback(Exception('world'))


def test_callbacks_and_errbacks_return_original_deferred():
    d = Deferred()
    assert d.add_callback(lambda a: None) is d
    assert d.add_errback(lambda a: None) is d
    assert d.add_callbacks(lambda a: None, lambda a: None) is d


def test_callback_var_args():
    holder = []
    d = Deferred()
    d.add_callback(lambda *args, **kwargs: holder.append((args, kwargs)), 2, 3, a=4, b=5)
    d.callback(1)

    assert holder[0] == ((1, 2, 3), {'a': 4, 'b': 5})


def test_deferred_callback_returns_another_deferred():
    d = Deferred()
    d2 = Deferred()

    d.add_callback(lambda r: succeed(r + 5).add_callback(lambda v: v + 5))
    d.add_callback(lambda r: d2)
    d.callback(5)

    assert d.result is d2
    assert d.paused
    assert d.called

    d2.callback(7)
    assert d.result == 7
    assert d2.result == 7


def test_deferred_exception_catch():
    def dummy_errback(deferred_exception):
        deferred_exception.catch(OSError)
        return "caught"

    deferred = Deferred()
    deferred.add_errback(dummy_errback)
    deferred.errback(OSError())
    assert deferred.result == 'caught'