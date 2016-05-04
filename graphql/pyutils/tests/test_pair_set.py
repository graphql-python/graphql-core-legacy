from graphql.pyutils.pair_set import PairSet


def test_pair_set():
    ps = PairSet()

    ps.add(1, 2)
    ps.add(2, 4)

    assert ps.has(1, 2)
    assert ps.has(2, 1)
    assert (1, 2) in ps
    assert (2, 1) in ps
    assert ps.has(4, 2)
    assert ps.has(2, 4)

    assert not ps.has(2, 3)
    assert not ps.has(1, 3)

    ps.remove(1, 2)
    assert not ps.has(1, 2)
    assert not ps.has(2, 1)
    assert (1, 2) not in ps
    assert (2, 1) not in ps

    assert ps.has(4, 2)
    assert ps.has(2, 4)
