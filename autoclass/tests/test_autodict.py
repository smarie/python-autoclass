import pytest
from typing import List

from autoclass import autodict


@pytest.mark.parametrize('only_public_fields', [True, False], ids=lambda x: 'only_public' if x else 'including class-private dunder fields')
@pytest.mark.parametrize('only_constructor_args', [True, False], ids=lambda x: 'only_constructor_args' if x else 'all_obj_fields')
def test_autodict(only_constructor_args, only_public_fields):
    """ @autodict functionality with various customization options for only_constructor_args/only_public_fields """

    @autodict(only_constructor_args=only_constructor_args, only_public_fields=only_public_fields)
    class FooConfigA(object):

        dummy_class_field = 'just to be sure it does not appear'

        def __init__(self, a: str, b: List[str]):
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

    # check that the dict view works
    # --constructor arguments
    assert t['a'] == t.a
    assert t['b'] == t.b

    # --other 'static' fields
    if only_constructor_args:
        with pytest.raises(KeyError):
            assert t['c'] == t.c
    else:
        assert t['c'] == t.c

    if only_constructor_args or only_public_fields:
        with pytest.raises(KeyError):
            assert t['_weak_private'] == t._weak_private
        with pytest.raises(KeyError):
            assert t['_FooConfigA__class_private'] == t._FooConfigA__class_private
    else:
        assert t['_weak_private'] == t._weak_private
        assert t['_FooConfigA__class_private'] == t._FooConfigA__class_private

    # -- dynamic fields
    if only_constructor_args:
        # new fields should not appear
        with pytest.raises(KeyError):
            assert t['new_field'] == t.new_field
    else:
        # new fields should appear
        assert t['new_field'] == t.new_field

    if only_constructor_args or only_public_fields:
        # new private fields should not appear
        with pytest.raises(KeyError):
            assert t['_new_field_weak_private'] == t._new_field_weak_private
        with pytest.raises(KeyError):
            assert t['__new_field_class_private_incorrect'] == t.__new_field_class_private_incorrect
        with pytest.raises(KeyError):
            assert t['_Dummy__new_field_class_private'] == t._Dummy__new_field_class_private
    else:
        # new private fields should appear
        assert t['_new_field_weak_private'] == t._new_field_weak_private
        assert t['__new_field_class_private_incorrect'] == t.__new_field_class_private_incorrect
        assert t['_Dummy__new_field_class_private'] == t._Dummy__new_field_class_private

    # assert that the dict is read-only
    with pytest.raises(TypeError):
        t['x'] = 5

    # assert that equals works
    assert t == dict(t)

    o = FooConfigA('rhubarb', ['pie', 'pie2'])
    o.new_field = 0
    o._new_field_weak_private = 1
    o.__new_field_class_private_incorrect = 0

    class Dummy:
        o.__new_field_class_private = 1

    assert t == o

    if only_constructor_args:
        # we could use t but we use dict(t) so that the error message in pytest is more readable
        assert dict(t) == {'a': 'rhubarb',  # only the two constructor fields appear
                           'b': ['pie', 'pie2']}
    elif only_public_fields:
        # we could use t but we use dict(t) so that the error message in pytest is more readable
        assert dict(t) == {'a': 'rhubarb',
                           'b': ['pie', 'pie2'],
                           'c': 't',
                           # _FooConfigA__class_private should not appear
                           'new_field': 0,
                           #'_weak_private': 'r',
                           #'_new_field_weak_private': 1,
                           # private fields defined out of the objects class are still visible
                           #'__new_field_class_private_incorrect': 0,
                           #'_Dummy__new_field_class_private': 1
                           }
    else:
        # we could use t but we use dict(t) so that the error message in pytest is more readable
        assert dict(t) == {'a': 'rhubarb',
                           'b': ['pie', 'pie2'],
                           'c': 't',
                           '_FooConfigA__class_private': 't',  # <= this is the one private field that appears now
                           'new_field': 0,
                           '_weak_private': 'r',
                           '_new_field_weak_private': 1,
                           # private fields defined out of the objects class are still visible
                           '__new_field_class_private_incorrect': 0,
                           '_Dummy__new_field_class_private': 1}

    # assert that the generated static method works
    if only_constructor_args:
        assert FooConfigA.from_dict(t) == t
