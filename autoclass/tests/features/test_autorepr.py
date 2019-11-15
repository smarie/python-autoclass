#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.
import sys

import pytest

from autoclass import autorepr


@pytest.mark.skipif(sys.version_info < (3, 6), reason="class vars order is not preserved")
@pytest.mark.parametrize('only_public_fields', [True, False], ids=lambda x: 'only_public' if x else 'including class-private dunder fields')
@pytest.mark.parametrize('only_known_fields', [True, False], ids=lambda x: 'only_constructor_args' if x else 'all_obj_fields')
@pytest.mark.parametrize("curly_mode", [False, True], ids="curly_mode={}".format)
def test_autorepr(only_known_fields, only_public_fields, curly_mode):
    """ @autorepr functionality with various customization options for only_constructor_args/only_public_fields """

    if curly_mode:
        def format_pairs(cls, pairs):
            return "%s(**{%s})" % (cls.__name__, ", ".join(["%r: %r" % pair for pair in pairs]))
    else:
        def format_pairs(cls, pairs):
            return "%s(%s)" % (cls.__name__, ", ".join(["%s=%r" % pair for pair in pairs]))

    @autorepr(only_known_fields=only_known_fields, only_public_fields=only_public_fields, curly_string_repr=curly_mode)
    class FooConfigA(object):

        dummy_class_field = 'just to be sure it does not appear'

        def __init__(self,
                     a,  # type: str,
                     b   # type: List[str]
                     ):
            self.a = a
            self.b = b
            self.c = 't'
            self._weak_private = 'r'
            self.__class_private = 't'

        def dummy_func(self):
            """ we create this just to be sure the function is not in the dict view """
            pass

    t = FooConfigA('rhubarb', ['pie', 'pie2'])
    t.new_field = 0
    t._new_field_weak_private = 1
    t.__new_field_class_private_incorrect = 0

    class Dummy:
        t.__new_field_class_private = 1

    # check the str/repr
    assert str(t) == repr(t)

    if only_known_fields:
        pairs = [('a', 'rhubarb'),  # only the two constructor fields appear
                 ('b', ['pie', 'pie2'])]
    elif only_public_fields:
        pairs = [('a', 'rhubarb'),
                 ('b', ['pie', 'pie2']),
                 ('c', 't'),
                 # _FooConfigA__class_private should not appear
                 ('new_field', 0)
                 #'_weak_private': 'r',
                 #'_new_field_weak_private': 1,
                 # private fields defined out of the objects class are still visible
                 #'__new_field_class_private_incorrect': 0,
                 #'_Dummy__new_field_class_private': 1
                 ]
    else:
        pairs = [('a', 'rhubarb'),
                 ('b', ['pie', 'pie2']),
                 ('c', 't'),
                 ('_weak_private', 'r'),
                 ('_FooConfigA__class_private', 't'),  # <= this is the one private field that appears now
                 ('new_field', 0),
                 ('_new_field_weak_private', 1),
                 # private fields defined out of the objects class are still visible
                 ('__new_field_class_private_incorrect', 0),
                 ('_Dummy__new_field_class_private', 1)]

    assert str(t) == format_pairs(FooConfigA, pairs)


@pytest.mark.parametrize("curly_mode", [False, True], ids="curly_mode={}".format)
def test_autorepr_pyfields(curly_mode):
    """tests that @autorepr works with pyfields"""

    from pyfields import field

    @autorepr
    class Foo(object):
        foo1 = field()
        foo2 = field(default=0)

    @autorepr(curly_string_repr=curly_mode)
    class Bar(Foo):
        bar = field()

    # create an object manually
    a = Bar()
    a.bar = 2
    a.foo1 = 'th'

    # order in prints is correct in legacy str mode
    if curly_mode:
        assert str(a) == "Bar(**{'foo1': 'th', 'foo2': 0, 'bar': 2})"
    else:
        assert str(a) == "Bar(foo1='th', foo2=0, bar=2)"
