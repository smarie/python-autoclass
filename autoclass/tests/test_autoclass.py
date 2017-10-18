import pytest

from autoclass.utils_decoration import AutoclassDecorationException


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
