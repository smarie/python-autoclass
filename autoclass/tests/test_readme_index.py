import sys

import pytest

from numbers import Real, Integral
from valid8 import Boolean, validate, validate_arg, instance_of, is_multiple_of, InputValidationError

try:
    from typing import Optional
except ImportError:
    pass

from autoclass import autoargs, autoprops, setter_override, autoclass


def test_readme_index_basic():
    """ First basic example in the doc """

    @autoclass
    class House(object):
        def __init__(self, name, nb_floors=1):
            pass

    a = House('my_house', 3)
    assert str(a) == "House({'name': 'my_house', 'nb_floors': 3})"
    assert [att for att in a.keys()] == ['name', 'nb_floors']
    assert {a, a} == {a}
    assert a == {'name': 'my_house', 'nb_floors': 3}


def test_readme_index_basic2():
    """ Second basic example in the doc: adding setter override """

    global t
    t = ''

    @autoclass
    class House(object):
        def __init__(self, name, nb_floors=1):
            pass

        @setter_override
        def nb_floors(self, nb_floors=1):
            global t
            t = 'Set nb_floors to {}'.format(nb_floors)
            self._nb_floors = nb_floors

    assert t == ''

    obj = House('my_house')
    assert t == 'Set nb_floors to 1'

    obj.nb_floors = 3
    assert t == 'Set nb_floors to 3'


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work correctly under python 3.7+")
def test_readme_enforce_simple():
    """ Example in the doc with enforce """

    from ._tests_pep484 import test_readme_enforce_simple
    test_readme_enforce_simple()


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
def test_readme_index_pytypes_simple():
    """ Example in the doc with pytypes """

    from ._tests_pep484 import test_readme_index_pytypes_simple
    test_readme_index_pytypes_simple()


def test_readme_index_valid8_simple():
    """ Example in the doc with valid8 """

    from mini_lambda import s, x, Len

    # Here we define our 2 validation errors
    class InvalidNameError(InputValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(InputValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @autoclass
    class House(object):

        @validate_arg('name', instance_of(str), Len(s) > 0,
                      error_type=InvalidNameError)
        @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                      error_type=InvalidSurfaceError)
        def __init__(self, name, surface=None):
            pass

    obj = House('sweet home', 200)

    obj.surface = None  # Valid (surface is nonable by signature)
    with pytest.raises(InvalidNameError):
        obj.name = 12  # InvalidNameError
    with pytest.raises(InvalidSurfaceError):
        obj.surface = 10000  # InvalidSurfaceError


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work correctly under python 3.7+")
def test_readme_index_enforce_valid8():
    """ Makes sure that the code in the documentation page is correct for the enforce + valid8 example """

    from ._tests_pep484 import test_readme_index_enforce_valid8
    test_readme_index_enforce_valid8()


def test_readme_pycontracts_simple():
    """ Simple test with pycontracts """

    from contracts import contract, ContractNotRespected

    @autoclass
    class House(object):

        @contract(name='str[>0]',
                  surface='None|(int,>=0,<10000)')
        def __init__(self, name, surface):
            pass

    obj = House('sweet home', 200)

    obj.surface = None  # Valid (surface is nonable by signature)
    with pytest.raises(ContractNotRespected):
        obj.name = ''  # InvalidNameError
    with pytest.raises(ContractNotRespected):
        obj.surface = 10000  # InvalidSurfaceError


def test_readme_old_way():
    """ Makes sure that the code in the documentation page is correct for the 'old way' of writing classes """

    class HouseConfiguration(object):
        def __init__(self,
                     name,               # type: str
                     surface,            # type: Real
                     nb_floors=1,        # type: Optional[Integral]
                     with_windows=False  # type: Boolean
                     ):
            self.name = name
            self.surface = surface
            self.nb_floors = nb_floors
            self.with_windows = with_windows

        # --name
        @property
        def name(self):
            return self._name

        @name.setter
        def name(self,
                 name  # type: str
                 ):
            validate('name', name, instance_of=str)
            self._name = name

        # --surface
        @property
        def surface(self):
            # type: (...) -> Real
            return self._surface

        @surface.setter
        def surface(self,
                    surface  # type: Real
                    ):
            validate('surface', surface, instance_of=Real, min_value=0, min_strict=True)
            self._surface = surface

        # --nb_floors
        @property
        def nb_floors(self):
            # type: (...) -> Optional[Integral]
            return self._nb_floors

        @nb_floors.setter
        def nb_floors(self,
                      nb_floors  # type: Optional[Integral]
                      ):
            validate('nb_floors', nb_floors, instance_of=Integral, enforce_not_none=False)
            self._surface = nb_floors  # !**

        # --with_windows
        @property
        def with_windows(self):
            # type: (...) -> Boolean
            return self._with_windows

        @with_windows.setter
        def with_windows(self,
                         with_windows  # type: Boolean
                         ):
            validate('with_windows', with_windows, instance_of=Boolean)
            self._with_windows = with_windows

    HouseConfiguration('test', 0.1)


def test_readme_pycontracts_complex():
    """ Makes sure that the code in the documentation page is correct for the PyContracts example """

    from contracts import contract, ContractNotRespected

    @autoprops
    class HouseConfiguration(object):
        @autoargs
        @contract(name='str[>0]',
                  surface='(int|float),>=0',
                  nb_floors='None|int',
                  with_windows='bool')
        def __init__(self,
                     name,  # type: str
                     surface,  # type: Real
                     nb_floors=1,  # type: Optional[Integral]
                     with_windows=False  # type: Boolean
                     ):
            pass

        # -- overriden setter for surface - no need to repeat the @contract
        @setter_override
        def surface(self,
                    surface  # type: Real
                    ):
            assert surface > 0
            self._surface = surface

    t = HouseConfiguration('test', 0.1)
    t.nb_floors = None
    with pytest.raises(ContractNotRespected):
        t.nb_floors = 2.2
    with pytest.raises(ContractNotRespected):
        t.surface = -1


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skip(reason="open bug in pytypes https://github.com/Stewori/pytypes/issues/19")
def test_readme_pytypes_validate_complex():
    """ A more complex pytypes + valid8 example """

    from ._tests_pep484 import test_readme_pytypes_validate_complex
    test_readme_pytypes_validate_complex()
