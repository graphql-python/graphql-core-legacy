obj = (dict, list, tuple)


def contain_subset(expected, actual):
    t_actual = type(actual)
    t_expected = type(expected)
    if not(issubclass(t_actual, t_expected) or issubclass(t_expected, t_actual)):
        return False
    if not isinstance(expected, obj) or expected is None:
        return expected == actual
    if expected and not actual:
        return False
    if isinstance(expected, list):
        aa = actual[:]
        return all([any([contain_subset(exp, act) for act in aa]) for exp in expected])
    for key in expected.keys():
        eo = expected[key]
        ao = actual.get(key)
        if isinstance(eo, obj) and eo is not None and ao is not None:
            if not contain_subset(eo, ao):
                return False
            continue
        if ao != eo:
            return False
    return True
