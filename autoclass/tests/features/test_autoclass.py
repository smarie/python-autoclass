#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.

import sys
import pytest
import pickle

from autoclass import autoclass


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work correctly under python 3.7+")
def test_autoclass_enforce_validate_not_reversed():
    """ Tests that if we reverse the annotations orders, it still works. Currently it fails """

    from ._tests_pep484 import test_autoclass_enforce_validate_not_reversed
    test_autoclass_enforce_validate_not_reversed()


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work correctly under python 3.7+")
def test_autoclass_enforce_validate_reversed():
    """ Tests that if we reverse the annotations orders, it still works. Currently it fails """

    from ._tests_pep484 import test_autoclass_enforce_validate_reversed
    test_autoclass_enforce_validate_reversed()


def test_autoclass_inheritance():
    """Tests that autoclass works also in an inheritance context """

    @autoclass
    class Foo(object):
        def __init__(self, foo1, foo2=0):
            pass

    @autoclass
    class Bar(Foo):
        def __init__(self, bar, foo1, foo2=0):
            # in this case super init call is not actually needed since all fields are again self-assigned here
            super(Bar, self).__init__(foo1, foo2)
            # pass

    a = Bar(2, 'th')
    assert a == {'bar': 2, 'foo1': 'th', 'foo2': 0}
    assert a['foo1'] == 'th'

    # iteration order is same than in init
    assert list(a.keys()) == ['bar', 'foo1', 'foo2']

    # order in prints is same than in init
    assert str(a) == "Bar(bar=2, foo1='th', foo2=0)"


def test_autoclass_pickle_inheritance():
    """Tests that pickle can work with autoclass-ed classes"""

    from ._test_autoclass_pickle import Bar

    a = Bar(2, 'th')
    assert a == {'bar': 2, 'foo1': 'th', 'foo2': 0}
    assert a['foo1'] == 'th'

    # iteration order is fixed
    assert list(a.keys()) == ['bar', 'foo1', 'foo2']

    # order in prints is fixed
    assert str(a) == "Bar(bar=2, foo1='th', foo2=0)"

    # pickle
    pik = pickle.dumps(a)
    aa = pickle.loads(pik)
    assert aa == a


def test_autoclass_slots():
    """Tests that autoclass works also when classes have slots """

    @autoclass(autoslots=True)
    class Foo(object):
        def __init__(self, foo1, foo2=0):
            pass

    @autoclass(autoslots=True)
    class Bar(Foo):
        def __init__(self, bar, foo1, foo2=0):
            # this constructor is not actually needed in this case since all fields are already self-assigned here
            super(Bar, self).__init__(foo1, foo2)
            # pass

    assert set(Bar.__slots__) == {'_bar'}

    a = Bar(2, 'th')
    assert a == {'bar': 2, 'foo1': 'th', 'foo2': 0}
    assert a['foo1'] == 'th'

    # iteration order is fixed
    assert list(a.keys()) == ['bar', 'foo1', 'foo2']

    # order in prints is fixed
    assert str(a) == "Bar(bar=2, foo1='th', foo2=0)"


def test_autoclass_pyfields():
    """tests that @autoclass works with pyfields"""
    from pyfields import field

    @autoclass(autodict=False)
    class Foo(object):
        foo1 = field()
        foo2 = field(default=0)

    @autoclass
    class Bar(Foo):
        bar = field()

    # order in init is ancestor+mandatories first
    a = Bar('th', 2)
    assert a == {'bar': 2, 'foo1': 'th', 'foo2': 0}

    # dict view works
    assert a['foo1'] == 'th'

    # iteration order is the same than in init
    assert list(a.keys()) == ['foo1', 'foo2', 'bar']

    # order in prints is the same than in init
    assert str(a) == "Bar(foo1='th', foo2=0, bar=2)"

    # test autorepr
    f = Foo('a')
    assert str(f) == "Foo(foo1='a', foo2=0)"

    # test autoeq
    assert f == Foo('a', foo2=0)

    # autodict was really disabled
    with pytest.raises(AttributeError):
        f.items()
