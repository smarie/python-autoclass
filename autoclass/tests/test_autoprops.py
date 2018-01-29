from typing import List

import pytest
from autoclass import autoargs, autoprops, getter_override, setter_override, \
    IllegalSetterSignatureException, DuplicateOverrideError, autoprops_decorate
from valid8 import Boolean, minlens, gts, between, validate_io, ValidationError


def test_autoprops_no_contract():
    """ Basic @autoprops functionality, no customization - all constructor arguments become properties """

    @autoprops
    class FooConfigA(object):
        @autoargs
        def __init__(self, a: str, b: List[str]):
            pass

    t = FooConfigA('rhubarb', ['pie', 'pie2'])

    # there are no contracts on the generated setters
    t.a = ''
    t.b = ['r', '']
    # check that the generated getters work
    assert t.a == ''
    assert t.b[0] == 'r'


def test_autoprops_pycontracts():
    """
    @autopropsBasic functionality with PyContracts - if a `@contract` annotation exist on the `__init__` method,
    mentioning a contract for a given parameter, the parameter contract will be added on the generated setter method
    """

    from contracts import ContractNotRespected, contract

    @autoprops
    class FooConfigA(object):
        @autoargs
        @contract(a='str[>0]', b='list[>0](str[>0])')
        def __init__(self, a: str, b: List[str]):
            pass

    t = FooConfigA('rhubarb', ['pie', 'pie2'])

    # check that there are contracts on the generated setters
    with pytest.raises(ContractNotRespected):
        t.a = ''
    with pytest.raises(ContractNotRespected):
        t.b = ['r', '']

    # check that the generated getters work
    t.b = ['r']
    assert t.b[0] == 'r'


def test_autoprops_include():
    """ @autoprops With pycontracts and explicit list of attributes to include """

    from contracts import ContractNotRespected, contract

    @autoprops(include='a')
    class FooConfigB(object):
        @autoargs
        @contract(a='str[>0]', b='list[>0](str[>0])')
        def __init__(self, a: str, b: List[str]):
            pass

    t = FooConfigB('rhubarb', ['pie', 'pie2'])

    # check that there is a contract on the generated setter
    with pytest.raises(ContractNotRespected):
        t.a = ''

    # check that no setter was generated for 'b'
    t.b = ['']  # we can because there is no setter, hence no contract
    assert t.b[0] == ''


def test_autoprops_exclude():
    """ @autoprops With pycontracts and explicit list of attributes to exclude """

    from contracts import ContractNotRespected, contract

    @autoprops(exclude='b')
    class FooConfigB(object):
        @autoargs
        @contract(a='str[>0]', b='list[>0](str[>0])')
        def __init__(self, a: str, b: List[str]):
            pass

    t = FooConfigB('rhubarb', ['pie', 'pie2'])

    # check that there is a contract on the generated setter
    with pytest.raises(ContractNotRespected):
        t.a = ''

    # check that no setter was generated for 'b'
    t.b = ['']  # we can because there is no setter, hence no contract
    assert t.b[0] == ''


def test_autoprops_include_exclude():
    """ @autoprops Asserts that include/exclude cant be used at the same time """

    # you can't use both at the same time
    with pytest.raises(ValueError):
        @autoprops(include='', exclude='')
        class Dummy(object):
            pass


def test_autoprops_override():
    """ @autoprops With Pycontracts. Tests that the user may override generated getter and a setter """

    from contracts import ContractNotRespected, contract

    # check that there is a double-contract warning
    with pytest.warns(UserWarning):
        @autoprops
        class FooConfigC(object):
            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass

            @getter_override
            def a(self):
                # in addition to getting the fields we'd like to print something
                print('a is being read. Its value is \'' + str(self._a) + '\'')
                return self._a

            @setter_override(attribute='b')
            @contract(toto='list[>0](str[>0])')
            def another_name(self, toto: List[str]):
                # in addition to setting the fields we'd like to print something
                print('Property \'b\' was set to \'' + str(toto) + '\'')
                self._b = toto

        t = FooConfigC('rhubarb', ['pie', 'pie2'])

        # check that we can still read a's value
        assert t.a == 'rhubarb'

        # check that 'a' still has a contract on its setter
        with pytest.raises(ContractNotRespected):
            t.a = ''

        # check that 'b' still has a contract on its setter
        with pytest.raises(ContractNotRespected):
            t.b = ['']  # we can not

        # check that 'b' still has a getter generated
        t.b = ['eh', 'oh']
        assert t.b == ['eh', 'oh']


def test_autoprops_override_exceptions():
    """ @autoprops Asserts that the user can not override a generated method if the overriden method has a wrong
    signature """

    # -- a getter is overriden while the attribute does not exist in constructor
    with pytest.raises(AttributeError):
        @autoprops
        class FooConfigD(object):
            @autoargs
            def __init__(self, a: str, b: List[str]):
                pass

            @getter_override
            def c(self):
                return 'c'

    # -- a setter is overriden with a wrong signature
    with pytest.raises(IllegalSetterSignatureException):
        @autoprops
        class FooConfigE(object):
            @autoargs
            def __init__(self, a: str, b: List[str]):
                pass

            @setter_override
            def b(self, toto: List[str], extra_arg: bool = False):
                self._b = toto

    # -- a getter is overriden twice
    with pytest.raises(DuplicateOverrideError):
        @autoprops
        class FooConfigF(object):
            @autoargs
            def __init__(self, a: str, b: List[str]):
                pass

            @getter_override
            def b(self):
                return self._b

            @getter_override(attribute='b')
            def another(self):
                return self._b


def test_autoprops_manual():
    """ @autoprops Tests the manual wrapper autoprops() """

    from contracts import ContractNotRespected
    from contracts import contract

    # we don't use @autoprops here
    class FooConfigA(object):
        @autoargs
        @contract(a='str[>0]', b='list[>0](str[>0])')
        def __init__(self, a: str, b: List[str]):
            pass

    # we execute it here
    autoprops_decorate(FooConfigA)

    t = FooConfigA('rhubarb', ['pie', 'pie2'])

    # check that there are contracts on the generated setters
    with pytest.raises(ContractNotRespected):
        t.a = ''
    with pytest.raises(ContractNotRespected):
        t.b = ['r', '']

    # check that the generated getters work
    t.b = ['r']
    assert t.b[0] == 'r'


def test_autoprops_signature_preserving():
    """ @autoprops Advanced: checks that the generated constructor still has the correct signature"""

    @autoprops
    class FooConfigD(object):
        @autoargs
        def __init__(self, a: str, b: List[str]):
            pass

    t = FooConfigD('rhubarb', ['pie', 'pie2'])
    try:
        getattr(FooConfigD, 'a').fset(t)
    except TypeError as e:
        assert e.args[0] == "autoprops_generated_setter() missing 1 required positional argument: 'a'"

    try:
        getattr(FooConfigD, 'a').fget()
    except TypeError as e:
        # yes ; right now it is still a lambda, since using a named method does not seem to work :(
        assert e.args[0] == "<lambda>() missing 1 required positional argument: 'self'"


def test_autoprops_enforce_validate():
    """ Makes sure that autoprops works with enforce AND valid8 """

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
        @validate_io(name=minlens(0),
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
    """ Tests that the default value is also set in the setters if it is provided in the constructor """

    from enforce import runtime_validation

    @runtime_validation
    @autoprops
    class Foo:
        def __init__(self, mandatory_field: str, optional_field: str = None):
            pass

    a = Foo('t')
    a.optional_field = None  # raises RuntimeTypeError: Argument 'val' was not of type <class 'str'>. Actual type was NoneType.
