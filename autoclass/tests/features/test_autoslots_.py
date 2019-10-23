#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.
import weakref

import pytest

from autoclass import autoslots, autoprops, autoargs


@pytest.mark.parametrize("use_public_names", [False, True], ids="use_public_names={}".format)
@pytest.mark.parametrize("add_weakref_slot", [False, True], ids="add_weakref_slot={}".format)
@pytest.mark.parametrize("preexisting", [False, True], ids="preexisting={}".format)
def test_autoslots(use_public_names, add_weakref_slot, preexisting):

    if preexisting:
        print()

    @autoslots(use_public_names=use_public_names, add_weakref_slot=add_weakref_slot)
    class Foo(object):
        if preexisting:
            __slots__ = ('foo1' if use_public_names else '_foo1',)

        def __init__(self, foo1, foo2=0):
            if use_public_names:
                self.foo1 = foo1
                self.foo2 = foo2
            else:
                self._foo1 = foo1
                self._foo2 = foo2

    if use_public_names:
        assert set(Foo.__slots__) == set(('foo1', 'foo2') + (('__weakref__',) if add_weakref_slot else ()))
    else:
        assert set(Foo.__slots__) == set(('_foo1', '_foo2') + (('__weakref__',) if add_weakref_slot else ()))

    f = Foo(1)
    assert not hasattr(f, '__dict__')
    if use_public_names:
        assert f.foo1 == 1
        assert f.foo2 == 0
    else:
        assert f._foo1 == 1
        assert f._foo2 == 0

    if add_weakref_slot:
        assert weakref.ref(f)() is f
    else:
        with pytest.raises(TypeError):
            weakref.ref(f)


def test_autoslots_args_props():
    @autoprops
    @autoslots(use_public_names=False)
    class Foo(object):
        @autoargs
        def __init__(self, foo1, foo2=0):
            pass

    f = Foo(1)
    assert not hasattr(f, '__dict__')
    assert f.foo1 == 1
    assert f.foo2 == 0
