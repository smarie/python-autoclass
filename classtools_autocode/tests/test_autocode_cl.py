from typing import List
from unittest import TestCase

from classtools_autocode import autoargs, autoprops, getter_override, setter_override, \
    IllegalSetterSignatureException, DuplicateOverrideError, check_var, autoprops_decorate


class TestAutoArgs(TestCase):

    def test_autoargs_simple(self):

        # Basic functionality, no customization - all constructor arguments are auto-assigned
        class A(object):
            @autoargs
            def __init__(self, foo, path, debug=False):
                pass

        # Test :
        # -- create an instance
        a = A('rhubarb', 'pie', debug=True)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)

    def test_autoargs_signature_preserving(self):
        # -- Advanced: check that the constructor still has the correct signature
        class A(object):
            @autoargs
            def __init__(self, foo, path, debug=False):
                pass
        try:
            A()
        except TypeError as e:
            self.assertTrue(e.args[0] == "__init__() missing 2 required positional arguments: 'foo' and 'path'")

    def test_autoargs_varargs(self):

        # Basic functionality, with special case of variable arguments *args.
        # -- note that the variable arguments are stored in a single attribute
        class B(object):
            @autoargs
            def __init__(self, foo, path, debug=False, *args):
                pass

        # Test :
        # -- create an instance
        a = B('rhubarb', 'pie', True, 100, 101)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)
        # -- *args is in a single attribute
        self.assertTrue(a.args == (100, 101))

    def test_autoargs_varargs_kwvarargs(self):

        # Basic functionality, with special case of variable arguments *args and keyword arguments **kw
        # -- note that *args are stored in a single attribute while **kw are stored in several attributes
        class C(object):
            @autoargs
            def __init__(self, foo, path, debug=False, *args, **kw):
                pass

        # Test :
        # -- create an instance
        a = C('rhubarb', 'pie', True, 100, 101, verbose=True, bar='bar')
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)
        # -- *args is in a single attribute
        self.assertTrue(a.args == (100, 101))
        # -- **kw is dispatched in several attributes
        self.assertTrue(a.verbose == True)
        self.assertTrue(a.bar == 'bar')

    def test_autoargs_noarg(self):

        # Same than test_autoargs_simple but with empty arguments list in autoargs
        class O(object):
            @autoargs()
            def __init__(self, foo, path, debug=False):
                pass

        # Test :
        # -- create an instance
        a = O('rhubarb', 'pie', debug=True)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)

    def test_autoargs_include(self):

        # Explicit list of names to include
        class C(object):
            @autoargs(include=('bar', 'baz', 'verbose'))
            def __init__(self, foo, bar, baz, verbose=False):
                pass

        # Test :
        # -- create an instance
        a = C('rhubarb', 'pie', 1)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.bar == 'pie')
        self.assertTrue(a.baz == 1)
        self.assertTrue(a.verbose == False)
        # -- check that a non-included field does not exist
        self.assertRaises(AttributeError, getattr, a, 'foo')

    def test_autoargs_exclude(self):

        # Explicit list of names to exclude
        class C(object):
            @autoargs(exclude=('bar', 'baz', 'verbose'))
            def __init__(self, foo, bar, baz, verbose=False):
                pass

        # Test :
        # -- create an instance
        a = C('rhubarb', 'pie', 1)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        # -- check that the non-included fields do not exist
        self.assertRaises(AttributeError, getattr, a, 'bar')
        self.assertRaises(AttributeError, getattr, a, 'baz')
        self.assertRaises(AttributeError, getattr, a, 'verbose')

    def test_autoargs_include_exclude(self):
        # you can't use both at the same time
        with self.assertRaises(ValueError):
            class Dummy(object):
                @autoargs(exclude='', include='')
                def __init__(self, foo, bar, baz, verbose=False):
                    pass

    # def test_autoargs_exclude_lock(self):
    #     class C(object):
    #         @autoargs(exclude=('bar', 'baz', 'verbose'), lock_class_fields=True)
    #         def __init__(self, foo, bar, baz, verbose=False):
    #             pass
    #
    #     a = C('rhubarb', 'pie', 1)
    #     self.assertTrue(a.foo == 'rhubarb')
    #     self.assertRaises(AttributeError, getattr, a, 'bar')
    #     self.assertRaises(AttributeError, setattr, a, 'newa',0)


class TestAutoProps(TestCase):

    def test_autoprops_no_contract(self):

        # Basic functionality, no customization - all constructor arguments become properties
        @autoprops
        class FooConfigA(object):

            @autoargs
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfigA('rhubarb', ['pie', 'pie2'])

        # there are no contracts on the generated setters
        t.a=''
        t.b=['r','']
        # check that the generated getters work
        self.assertTrue(t.a == '')
        self.assertTrue(t.b[0] == 'r')

    def test_autoprops(self):

        # Basic functionality with PyContracts - if a `@contract` annotation exist on the `__init__` method, mentioning
        # a contract for a given parameter, the parameter contract will be added on the generated setter method
        from contracts import ContractNotRespected, contract

        @autoprops
        class FooConfigA(object):

            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfigA('rhubarb', ['pie', 'pie2'])

        # check that there are contracts on the generated setters
        self.assertRaises(ContractNotRespected, setattr, t, 'a', '')
        self.assertRaises(ContractNotRespected, setattr, t, 'b', ['r',''])

        # check that the generated getters work
        t.b=['r']
        self.assertTrue(t.b[0] == 'r')


    def test_autoprops_include(self):

        from contracts import ContractNotRespected, contract

        @autoprops(include='a')
        class FooConfigB(object):

            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfigB('rhubarb', ['pie', 'pie2'])

        # check that there is a contract on the generated setter
        self.assertRaises(ContractNotRespected, setattr, t, 'a', '')

        # check that no setter was generated for 'b'
        t.b=[''] # we can because there is no setter, hence no contract
        self.assertTrue(t.b[0] == '')


    def test_autoprops_exclude(self):

        from contracts import ContractNotRespected, contract

        @autoprops(exclude='b')
        class FooConfigB(object):

            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfigB('rhubarb', ['pie', 'pie2'])

        # check that there is a contract on the generated setter
        self.assertRaises(ContractNotRespected, setattr, t, 'a', '')

        # check that no setter was generated for 'b'
        t.b=[''] # we can because there is no setter, hence no contract
        self.assertTrue(t.b[0] == '')

    def test_autoprops_include_exclude(self):
        # you can't use both at the same time
        with self.assertRaises(ValueError):
            @autoprops(include='', exclude='')
            class Dummy(object):
                pass

    def test_autoprops_override(self):

        from contracts import ContractNotRespected, contract

        # check that there is a double-contract warning
        with self.assertWarns(UserWarning):
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
                @contract()
                def another_name(self, toto: List[str]):
                    # in addition to setting the fields we'd like to print something
                    print('Property \'b\' was set to \'' + str(toto) + '\'')
                    self._b = toto


            t = FooConfigC('rhubarb', ['pie', 'pie2'])

            # check that we can still read a's value
            self.assertTrue(t.a == 'rhubarb')

            # check that 'a' still has a contract on its setter
            with self.assertRaises(ContractNotRespected):
                t.a = ''

            # check that 'b' still has a contract on its setter
            with self.assertRaises(ContractNotRespected):
                t.b=[''] # we can not

            # check that 'b' still has a getter generated
            t.b = ['eh', 'oh']
            self.assertTrue(t.b == ['eh', 'oh'])


    def test_autoprops_override_exceptions(self):

        # -- a getter is overriden while the attribute does not exist in constructor
        with self.assertRaises(AttributeError):
            @autoprops
            class FooConfigD(object):
                @autoargs
                def __init__(self, a: str, b: List[str]):
                    pass

                @getter_override
                def c(self):
                    return 'c'

        # -- a setter is overriden with a wrong signature
        with self.assertRaises(IllegalSetterSignatureException):
            @autoprops
            class FooConfigE(object):
                @autoargs
                def __init__(self, a: str, b: List[str]):
                    pass

                @setter_override
                def b(self, toto: List[str], extra_arg:bool = False):
                    self._b = toto

        # -- a getter is overriden twice
        with self.assertRaises(DuplicateOverrideError):
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

    def test_autoprops_manual(self):

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
        self.assertRaises(ContractNotRespected, setattr, t, 'a', '')
        self.assertRaises(ContractNotRespected, setattr, t, 'b', ['r', ''])

        # check that the generated getters work
        t.b = ['r']
        self.assertTrue(t.b[0] == 'r')

    def test_autoprops_signature_preserving(self):
        # -- Advanced: check that the constructor still has the correct signature
        @autoprops
        class FooConfigD(object):
            @autoargs
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfigD('rhubarb', ['pie', 'pie2'])
        try:
            getattr(FooConfigD, 'a').fset(t)
        except TypeError as e:
            self.assertTrue(e.args[0] == "generated_setter_fun() missing 1 required positional argument: 'val'")

        try:
            getattr(FooConfigD, 'a').fget()
        except TypeError as e:
            # yes ; right now it is still a lambda, since using a named method does not seem to work :(
            self.assertTrue(e.args[0] == "<lambda>() missing 1 required positional argument: 'self'")

class TestReadMe(TestCase):
    """
    just to test that what is written in the readme actually works :)
    """

    def test_readme(self):

        from warnings import warn

        class HouseConfiguration(object):
            def __init__(self, name: str, surface: float, nb_floors: int, with_windows: bool = False):
                self.name = name
                self.surface = surface
                self.nb_floors = nb_floors
                self.with_windows = with_windows

            # --name
            @property
            def name(self):
                return self._name

            @name.setter
            def name(self, name):
                check_var(name, var_name='name', var_types=str)
                self._name = name

            # --surface
            @property
            def surface(self):
                return self._surface

            @surface.setter
            def surface(self, surface):
                check_var(surface, var_name='surface', var_types=[int, float], min_value=0)
                warn('You should really not do that..')
                self._surface = surface

            # --nb_floors
            @property
            def nb_floors(self):
                return self._nb_floors

            @nb_floors.setter
            def nb_floors(self, nb_floors):
                check_var(nb_floors, var_name='nb_floors', var_types=int, min_value=0)
                self._surface = nb_floors  # explicit error here :)

            # --with_windows
            @property
            def with_windows(self):
                return self._with_windows

            @with_windows.setter
            def with_windows(self, with_windows):
                check_var(with_windows, var_name='with_windows', var_types=bool)
                self._with_windows = with_windows

        HouseConfiguration('test', 0, 0)


        from contracts import contract, ContractNotRespected
        @autoprops
        class HouseConfiguration(object):
            @autoargs
            @contract(name='str[>0]',
                      surface='(int|float),>=0',
                      nb_floors='int,>=0',
                      with_windows='bool')
            def __init__(self,
                         name: str,
                         surface: float,
                         nb_floors: int,
                         with_windows: bool = False):
                pass

            # --overriden setter for surface
            @setter_override
            def surface(self, surface):
                warn('You should really not do that..')
                self._surface = surface

        t = HouseConfiguration('test', 0, 0)
        with self.assertRaises(ContractNotRespected):
            t.surface = -1
