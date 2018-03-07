import pytest
from autoclass import autoargs, autoprops, autodict, autoclass, autohash
from typing import List
from valid8 import Boolean, minlens, validate_io, ValidationError, gt, minlen


def test_readme_usage_autoprops_validate():
    @autoprops
    class FooConfigA(object):
        @autoargs
        @validate_io(a=minlens(0))
        def __init__(self, a: str):
            pass

    t = FooConfigA('rhubarb')

    # check that the generated getters work
    t.a = 'r'
    assert t.a == 'r'

    # check that there are validators on the generated setters
    with pytest.raises(ValidationError):
        t.a = ''  # raises ValidationError


def test_readme_usage_autodict_1():
    """ basic autodict without and with autoargs """

    # ** without autoargs
    @autodict
    class A(object):
        def __init__(self, a: int, b: str):
            self.a = a
            self.b = b

    o = A(1, 'r')
    # o behaves like a read-only dict
    assert o == dict(o)
    assert o == {'a': 1, 'b': 'r'}

    # you can create an object from a dict too thanks to the generated class function
    p = A.from_dict({'a': 1, 'b': 'r'})
    assert p == o

    # str and repr methods show interesting stuff
    str(p)  # "A({'a': 1, 'b': 'r'})"
    repr(p)  # "A({'a': 1, 'b': 'r'})"

    # ** with autoargs
    @autodict
    class B(object):
        @autoargs
        def __init__(self, a: int, b: str):
            pass

    o = B(1, 'r')
    # same results
    assert o == {'a': 1, 'b': 'r'}

    # you can create an object from a dict too thanks to the generated class function
    p = B.from_dict({'a': 1, 'b': 'r'})
    assert p == o


def test_readme_usage_autodict_2():
    """ basic autodict with other and private fields """

    @autodict
    class C(object):
        @autoargs
        def __init__(self, a: str, b: List[str]):
            self.non_constructor_arg = 't'
            self._private = 1
            self.__class_private = 't'

    o = C(1, 'r')
    # only fields corresponding to constructor arguments are visible
    assert o == {'a': 1, 'b': 'r'}


def test_readme_usage_autodict_3():

    @autodict(only_constructor_args=False, only_public_fields=False)
    class D(object):
        @autoargs
        def __init__(self, a: str, b: List[str]):
            self.non_constructor_arg = 'b'
            self._private = 1
            self.__class_private = 't'

    o = D(1, 'r')
    # o behaves like a read-only dict, all fields are now visible
    assert o == dict(o)
    assert o == {'a': 1, 'b': 'r',
                 'non_constructor_arg': 'b',
                 '_private': 1,
                 '_D__class_private': 't'}  # notice the name


def test_readme_usage_autohash_1():
    @autohash
    class A(object):
        def __init__(self, a: int, b: str):
            self.a = a
            self.b = b

    o = A(1, 'r')
    o._test = 2

    # o is hashable
    # the order of vars(self).values() does not seem stable across CPython versions: skipping this test
    # assert hash(o) == hash((1, 'r', 2))

    p = A(1, 'r')
    p._test = 2
    # o and p have identical hash
    assert hash(o) == hash(p)

    # dynamic and private fields are taken into account by default
    p._test = 3
    assert hash(o) != hash(p)


def test_readme_usage_autohash_2():

    from random import random

    @autohash(only_constructor_args=True, only_public_fields=True)
    class D(object):
        @autoargs
        def __init__(self, a: str, _b: str):
            self.non_constructor_arg = random()
            self._private = random()
            self.__class_private = random()

    o = D(1, 'r')
    p = D(1, 'r')

    # o and p have the same hash because only the constructor arguments are taken into account
    assert hash(o) == hash(p)
    assert hash(o) == hash((1, 'r'))


def test_readme_usage_autoclass():

    from numbers import Integral
    from typing import Optional

    # we will use enforce as the runtime checker
    import enforce as en
    from enforce import runtime_validation
    en.config(dict(mode='covariant'))  # allow subclasses when validating types

    # class definition
    @runtime_validation
    @autoclass
    class AllOfTheAbove:
        @validate_io(a=gt(1), c=minlen(1))
        def __init__(self, a: Integral, b: Boolean, c: Optional[List[str]] = None):
            pass

    # instance creation
    o = AllOfTheAbove(a=2, b=True)

    # @autoargs works
    assert o.a == 2

    # @autoprops works, in combination with any runtime checker (here demonstrated with enforce)
    from enforce.exceptions import RuntimeTypeError
    with pytest.raises(RuntimeTypeError):
        o.b = 1  # RuntimeTypeError Argument 'b' was not of type Boolean. Actual type was int.

    # @autodict works
    assert o == {'a': 2, 'b': True, 'c': None}
    assert AllOfTheAbove.from_dict(o) == o
    assert dict(**o) == o


def test_readme_usage_autoclass_custom():

    from numbers import Integral
    from typing import Optional

    # we will use enforce as the runtime checker
    import enforce as en
    from enforce import runtime_validation
    en.config(dict(mode='covariant'))  # allow subclasses when validating types

    # class definition
    @runtime_validation
    @autoclass(autodict=False)
    class PartsOfTheAbove:
        @validate_io(a=gt(1), c=minlen(1))
        def __init__(self, a: Integral, b: Boolean, c: Optional[List[str]] = None):
            pass

    # instance creation
    o = PartsOfTheAbove(a=2, b=True)

    # @autoargs works
    assert o.a == 2

    # @autoprops works, in combination with any runtime checker (here demonstrated with enforce)
    from enforce.exceptions import RuntimeTypeError
    with pytest.raises(RuntimeTypeError):
        o.b = 1  # RuntimeTypeError Argument 'b' was not of type Boolean. Actual type was int.

    # @autodict is disabled
    with pytest.raises(AssertionError):
        assert o == {'a': 2, 'b': True, 'c': None}  # AssertionError
    with pytest.raises(AttributeError):
        assert PartsOfTheAbove.from_dict(o) == o  # AttributeError: type object 'PartsOfTheAbove' has no attribute 'from_dict'
    with pytest.raises(TypeError):
        assert dict(**o) == o  # TypeError: type object argument after ** must be a mapping, not PartsOfTheAbove
