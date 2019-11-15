from numbers import Real, Integral
from typing import Optional, List

import pytest

from autoclass import setter_override, autoclass, AutoclassDecorationException, autoprops, autoargs
from valid8 import Boolean, ValidationError, validate_io
from valid8.validation_lib import gts, between, minlen, gt


def test_autoclass_enforce_validate_not_reversed():
    """"""

    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # to accept subclasses in validation

    @runtime_validation
    @autoclass
    class HouseConfiguration(object):
        def __init__(self, surface: Real):
            pass

        # -- overriden setter for surface
        @setter_override
        def surface(self, surface):
            print('Set surface to {}'.format(surface))
            self._surface = surface

    t = HouseConfiguration(12)


def test_autoclass_enforce_validate_reversed():
    """"""

    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # to accept subclasses in validation

    with pytest.raises(AutoclassDecorationException):
        @autoclass
        @runtime_validation
        class HouseConfiguration(object):
            def __init__(self, surface: Real):
                pass

            # -- overriden setter for surface
            @setter_override
            def surface(self, surface):
                print('Set surface to {}'.format(surface))
                self._surface = surface

        t = HouseConfiguration(12)


def test_autoprops_enforce_validate():

    import enforce as en
    from enforce import runtime_validation

    en.config(dict(mode='covariant'))  # allow subclasses when validating types

    @runtime_validation
    @autoprops
    class HouseConfiguration(object):
        @autoargs
        @validate_io(name=minlen(1),
                     surface=gts(0),
                     nb_floors=between(1, 100, open_right=True))
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
            self.toto = 'done'
            self._surface = surface

    t = HouseConfiguration('test', 12, 2)

    # 'Optional' works
    t.nb_floors = None

    # Custom print works
    t.surface = 0.1
    assert t.toto == 'done'

    # Type validation works
    from enforce.exceptions import RuntimeTypeError
    with pytest.raises(RuntimeTypeError):
        t.nb_floors = 2.2

    # Custom validation works
    with pytest.raises(ValidationError):
        t.surface = 0


def test_autoprops_enforce_default():
    from enforce import runtime_validation

    @runtime_validation
    @autoprops
    class Foo:
        def __init__(self,
                     mandatory_field: str,
                     optional_field: str = None):
            pass

    a = Foo('t')
    a.optional_field = None  # raises RuntimeTypeError: Argument 'val' was not of type <class 'str'>. Actual type was NoneType.
