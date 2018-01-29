import pytest
from autoclass import autoargs, autoprops, setter_override
from valid8 import Boolean, ValidationError


def test_readme_index_basic():
    """ First basic example in the doc """

    from autoclass import autoclass

    @autoclass
    class House:
        def __init__(self, name, nb_floors=1):
            pass

    a = House('my_house', 3)
    assert str(a) == "House({'name': 'my_house', 'nb_floors': 3})"
    assert [att for att in a.keys()] == ['name', 'nb_floors']
    assert {a, a} == {a}
    assert a == {'name': 'my_house', 'nb_floors': 3}


def test_readme_index_basic2():
    """ Second basic example in the doc: adding setter override """

    from autoclass import autoclass, setter_override

    global t
    t = ''

    @autoclass
    class House:
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


def test_readme_enforce_simple():
    """ Example in the doc with enforce """

    from autoclass import autoclass

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
    """ Example in the doc with pytypes """

    from autoclass import autoclass
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
    assert exc_info.value.args[0] == "\n  autoclass.tests.test_readme_index." \
                                     "test_readme_index_pytypes_simple.<locals>.House.nb_floors/setter" \
                                     "\n  called with incompatible types:\nExpected: Tuple[int]\nReceived: Tuple[str]"


def test_readme_index_valid8_simple():
    """ Example in the doc with valid8 """

    from autoclass import autoclass
    from mini_lambda import s, x, l, Len
    from valid8 import validate_arg, instance_of, is_multiple_of, InputValidationError

    # Here we define our 2 validation errors
    class InvalidNameError(InputValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(InputValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @autoclass
    class House:

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


def test_readme_index_enforce_valid8():
    """ Makes sure that the code in the documentation page is correct for the enforce + valid8 example """

    from autoclass import autoclass

    # Imports - for type validation
    from numbers import Integral
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # type validation will accept subclasses too

    # Imports - for value validation
    from mini_lambda import s, x, Len
    from valid8 import validate_arg, is_multiple_of, InputValidationError

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


def test_readme_pycontracts_simple():
    """ Simple test with pycontracts """

    from autoclass import autoclass
    from contracts import contract, ContractNotRespected

    @autoclass
    class House:

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

    from autoclass import check_var
    from numbers import Real, Integral
    from typing import Optional, Union
    from valid8 import Boolean

    class HouseConfiguration(object):
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            self.name = name
            self.surface = surface
            self.nb_floors = nb_floors
            self.with_windows = with_windows

        # --name
        @property
        def name(self):
            return self._name

        @name.setter
        def name(self, name: str):
            check_var(name, var_name='name', var_types=str)
            self._name = name

        # --surface
        @property
        def surface(self) -> Real:
            return self._surface

        @surface.setter
        def surface(self, surface: Real):
            check_var(surface, var_name='surface', var_types=Real, min_value=0, min_strict=True)
            self._surface = surface

        # --nb_floors
        @property
        def nb_floors(self) -> Optional[Integral]:
            return self._nb_floors

        @nb_floors.setter
        def nb_floors(self, nb_floors: Optional[Integral]):
            check_var(nb_floors, var_name='nb_floors', var_types=Integral, enforce_not_none=False)
            self._surface = nb_floors  # !**

        # --with_windows
        @property
        def with_windows(self) -> Boolean:
            return self._with_windows

        @with_windows.setter
        def with_windows(self, with_windows: Boolean):
            check_var(with_windows, var_name='with_windows', var_types=Boolean)
            self._with_windows = with_windows

    HouseConfiguration('test', 0.1)


def test_readme_pycontracts_complex():
    """ Makes sure that the code in the documentation page is correct for the PyContracts example """

    from contracts import contract, ContractNotRespected
    from numbers import Real, Integral
    from typing import Optional

    @autoprops
    class HouseConfiguration(object):
        @autoargs
        @contract(name='str[>0]',
                  surface='(int|float),>=0',
                  nb_floors='None|int',
                  with_windows='bool')
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            pass

        # -- overriden setter for surface - no need to repeat the @contract
        @setter_override
        def surface(self, surface: Real):
            assert surface > 0
            self._surface = surface

    t = HouseConfiguration('test', 0.1)
    t.nb_floors = None
    with pytest.raises(ContractNotRespected):
        t.nb_floors = 2.2
    with pytest.raises(ContractNotRespected):
        t.surface = -1


@pytest.mark.skip(reason="open bug in pytypes https://github.com/Stewori/pytypes/issues/19")
def test_readme_pytypes_validate_complex():
    """ A more complex pytypes + valid8 example """

    from autoclass import autoclass, setter_override
    from valid8 import Boolean, validate_io, minlens, gt
    from numbers import Real, Integral
    from typing import Optional

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
