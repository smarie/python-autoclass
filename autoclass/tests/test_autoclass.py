import pytest
from autoclass import autoclass, setter_override, autoprops, autoargs

from autoclass.utils_decoration import AutoclassDecorationException
from valid8 import Boolean


def test_autoclass_enforce_validate_not_reversed():
    """ Tests that if we reverse the annotations orders, it still works. Currently it fails """

    from autoclass import autoclass, setter_override
    from numbers import Real
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
    """ Tests that if we reverse the annotations orders, it still works. Currently it fails """

    from autoclass import autoclass, setter_override
    from numbers import Real
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


def test_readme_pytypes():
    """ Makes sure that the code in the documentation page is correct for the pytypes example """

    # from autoclass import autoargs, autoprops, Boolean
    from pytypes import typechecked
    from numbers import Real, Integral
    from typing import Optional

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
    """ Makes sure that the code in the documentation page is correct for the enforce example """

    # from autoclass import autoargs, autoprops, Boolean
    import enforce as en
    from enforce import runtime_validation
    from numbers import Real, Integral
    from typing import Optional

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


def test_autoclass_inheritance():
    from autoclass import autoclass

    @autoclass
    class Foo:
        def __init__(self, foo1, foo2=0):
            pass

    @autoclass
    class Bar(Foo):
        def __init__(self, bar, foo1, foo2=0):
            # this constructor is not actually needed in this case since all fields are already self-assigned here
            super(Bar, self).__init__(foo1, foo2)
            # pass

    a = Bar(2, 'th')
    assert a == {'bar': 2, 'foo1': 'th', 'foo2': 0}
    assert a['foo1'] == 'th'

    # iteration order is fixed
    assert list(a.keys()) == ['bar', 'foo1', 'foo2']

    # order in prints is fixed
    assert str(a) == "Bar({'bar': 2, 'foo1': 'th', 'foo2': 0})"
