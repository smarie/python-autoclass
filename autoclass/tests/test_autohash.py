from random import random

import pytest
from typing import List, Tuple, Dict

from autoclass import autohash, autoclass


@pytest.mark.parametrize('only_public_fields', [True, False], ids=lambda x: 'only_public' if x else 'including class-private dunder fields')
@pytest.mark.parametrize('only_constructor_args', [True, False], ids=lambda x: 'only_constructor_args' if x else 'all_obj_fields')
def test_autohash(only_constructor_args, only_public_fields):
    """ @autohash functionality with various customization options for only_constructor_args/only_public_fields """

    @autohash(only_constructor_args=only_constructor_args, only_public_fields=only_public_fields)
    class FooConfigA(object):

        dummy_class_field = 'just to be sure it does not appear'

        def __init__(self, a: str, b: Tuple[str, str]):
            self.a = a
            self.b = b
            self.c = 1
            self._weak_private = 2
            self.__class_private = 3

        def dummy_func(self):
            """ we create this just to be sure the function is not in the hash """
            pass

    # *** first object 'a'
    a = FooConfigA('rhubarb', ('pie', 'pie2'))
    a.new_field = 1
    a._new_field_weak_private = 2
    a.__new_field_class_private_incorrect = 3

    class Dummy:
        a.__new_field_class_private = 4

    # *** b is fully identical to a (constructor args + static/dynamic public/private fields)
    b = FooConfigA('rhubarb', ('pie', 'pie2'))
    b.new_field = 1
    b._new_field_weak_private = 2
    b.__new_field_class_private_incorrect = 3

    class Dummy:
        b.__new_field_class_private = 4

    # *** d is identical to a but only for constructor args + public fields
    d = FooConfigA('rhubarb', ('pie', 'pie2'))
    d._weak_private = random()
    d.__class_private = random()
    d.new_field = 1
    d._new_field_weak_private = random()
    d.__new_field_class_private_incorrect = random()

    class Dummy2:
        d.__new_field_class_private = random()

    # *** d is identical to a but only for constructor args
    e = FooConfigA('rhubarb', ('pie', 'pie2'))

    # *** e is different from a
    f = FooConfigA('rhubarb', ('pie3', ''))

    # check that the hash works
    assert hash(a) == hash(b)

    if only_constructor_args:
        assert hash(a) == hash(d)
        assert hash(a) == hash(e)
    elif only_public_fields:
        assert hash(a) == hash(d)
        assert hash(a) != hash(e)
    else:
        assert hash(a) != hash(d)
        assert hash(a) != hash(e)

    assert hash(a) != hash(f)


@pytest.mark.skip('Currently the test does not work, see https://github.com/smarie/python-autoclass/issues/21')
def test_autohash_exclude():
    """ Tests that exclusion works correctly with autohash """

    # Currently the test does not work, see https://github.com/smarie/python-autoclass/issues/21
    @autoclass(autohash=False)
    @autohash(exclude='bar')
    class Foo:
        def __init__(self, foo: str, bar: Dict[str, str]):
            pass

    a = Foo('hello', dict())
    hash(a)
