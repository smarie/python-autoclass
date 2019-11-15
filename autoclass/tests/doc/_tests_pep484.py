#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.

from numbers import Real, Integral
from typing import Optional, List

import pytest

from autoclass import setter_override, autoclass, AutoclassDecorationException, autoprops, autoargs
from valid8 import Boolean, ValidationError, validate_io
from valid8.validation_lib import gts, between, minlen, gt


def test_readme_pytypes():
    from pytypes import typechecked

    @typechecked
    @autoclass
    class HouseConfiguration(object):
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            pass

        # -- overriden setter for surface for custom validation
        @setter_override
        def surface(self, surface):
            assert surface > 0
            self._surface = surface

    t = HouseConfiguration('test', 12, 2)

    # 'Optional' works
    t.nb_floors = None

    # Type validation works
    from pytypes import InputTypeError
    with pytest.raises(InputTypeError):
        t.nb_floors = 2.2

    # Custom validation works
    with pytest.raises(AssertionError):
        t.surface = 0


def test_readme_enforce():
    import enforce as en
    from enforce import runtime_validation

    en.config(dict(mode='covariant'))  # allow subclasses when validating types

    @runtime_validation
    @autoprops
    class HouseConfiguration(object):
        @autoargs
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            pass

        # -- overriden setter for surface for custom validation
        @setter_override
        def surface(self, surface):
            assert surface > 0
            self._surface = surface

    t = HouseConfiguration('test', 12, 2)

    # 'Optional' works
    t.nb_floors = None

    # Type validation works
    from enforce.exceptions import RuntimeTypeError
    with pytest.raises(RuntimeTypeError):
        t.nb_floors = 2.2

    # Custom validation works
    with pytest.raises(AssertionError):
        t.surface = 0


def test_readme_enforce_simple():
    # we use enforce runtime checker for this example
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # to accept subclasses in validation

    @runtime_validation
    @autoclass
    class House:
        def __init__(self, name: str, nb_floors: int = 1):
            pass

    obj = House('my_house')

    from enforce.exceptions import RuntimeTypeError
    with pytest.raises(RuntimeTypeError) as exc_info:
        obj.nb_floors = 'red'
    assert exc_info.value.args[0] == "\n  The following runtime type errors were encountered:\n" \
                                     "       Argument 'nb_floors' was not of type <class 'int'>. " \
                                     "Actual type was str."


def test_readme_index_pytypes_simple():
    from pytypes import typechecked

    @typechecked
    @autoclass
    class House:
        # the constructor below is decorated with PEP484 type hints
        def __init__(self, name: str, nb_floors: int = 1):
            pass

    obj = House('my_house')

    from pytypes import InputTypeError
    with pytest.raises(InputTypeError) as exc_info:
        obj.nb_floors = 'red'
    assert exc_info.value.args[0] == "\n  autoclass.tests.doc._tests_pep484." \
                                     "test_readme_index_pytypes_simple.<locals>.House.nb_floors/setter" \
                                     "\n  called with incompatible types:\nExpected: Tuple[int]\nReceived: Tuple[str]"


def test_readme_index_enforce_valid8():
    # Imports - for type validation
    from numbers import Integral
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # type validation will accept subclasses too

    # Imports - for value validation
    from mini_lambda import s, x, Len
    from valid8 import validate_arg, InputValidationError
    from valid8.validation_lib import is_multiple_of

    # 2 custom validation errors for valid8
    class InvalidName(InputValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurface(InputValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @runtime_validation
    @autoclass
    class House:
        @validate_arg('name', Len(s) > 0,
                      error_type=InvalidName)
        @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                      error_type=InvalidSurface)
        def __init__(self, name: str, surface: Integral = None):
            pass

    obj = House('sweet home', 200)

    obj.surface = None  # Valid (surface is nonable by signature)
    with pytest.raises(InvalidName):
        obj.name = ''  # InvalidNameError
    with pytest.raises(InvalidSurface):
        obj.surface = 10000  # InvalidSurfaceError


def test_readme_pytypes_validate_complex():
    # we use pytypes for this example
    from pytypes import typechecked

    @typechecked
    @autoclass
    class HouseConfiguration(object):

        @validate_io(name=minlens(0),
                     surface=gt(0))
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            pass

        # -- overriden setter for surface for custom validation or other things
        @setter_override
        def surface(self, surface):
            print('Set surface to {}'.format(surface))
            self._surface = surface

    t = HouseConfiguration('test', 12, 2)

    # 'Optional' works
    t.nb_floors = None

    # Type validation works
    from pytypes import InputTypeError
    with pytest.raises(InputTypeError):
        t.nb_floors = 2.2

    # Value validation works
    with pytest.raises(ValidationError):
        t.surface = -1

    # Value validation works in constructor
    with pytest.raises(ValidationError):
        HouseConfiguration('', 12, 2)

    # str and repr work
    assert str(t) == repr(t)
    # "HouseConfiguration({'nb_floors': None, 'with_windows': False, 'surface': 12, 'name': 'test'})"
    # assert eval(repr(t)) == t does not work !

    # dict work
    assert t == {'name': 'test', 'nb_floors': None, 'surface': 12, 'with_windows': False}
    assert t == dict(name='test', nb_floors=None, surface=12, with_windows=False)
    t.keys()
    for k, v in t.items():
        print(str(k) + ': ' + str(v))

    # TODO this is an open bug in pytypes https://github.com/Stewori/pytypes/issues/19
    HouseConfiguration.from_dict({'name': 'test2', 'surface': 1})


def test_readme_usage_autoclass():
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
        assert PartsOfTheAbove.from_dict(
            o) == o  # AttributeError: type object 'PartsOfTheAbove' has no attribute 'from_dict'
    with pytest.raises(TypeError):
        assert dict(**o) == o  # TypeError: type object argument after ** must be a mapping, not PartsOfTheAbove
