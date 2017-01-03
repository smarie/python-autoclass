from typing import List
from unittest import TestCase

from classtools_autocode.class_utils import autoargs, autoprops, getter_override, setter_override, \
    IllegalSetterSignatureException, DuplicateOverrideError


class TestAutoArgs(TestCase):

    def test_autoargs_simple(self):

        class A(object):
            @autoargs()
            def __init__(self, foo, path, debug=False):
                pass

        a = A('rhubarb', 'pie', debug=True)
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)


    def test_autoargs_varargs(self):

        class B(object):
            @autoargs()
            def __init__(self, foo, path, debug=False, *args):
                pass

        a = B('rhubarb', 'pie', True, 100, 101)
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)
        self.assertTrue(a.args == (100, 101))

    def test_autoargs_varargs_kwvarargs(self):

        class C(object):
            @autoargs()
            def __init__(self, foo, path, debug=False, *args, **kw):
                pass

        a = C('rhubarb', 'pie', True, 100, 101, verbose=True)
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)
        self.assertTrue(a.verbose == True)
        self.assertTrue(a.args == (100, 101))

    def test_autoargs_noarg(self):
        class O(object):
            @autoargs
            def __init__(self, foo, path, debug=False):
                pass

        a = O('rhubarb', 'pie', debug=True)
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)


    def test_autoargs_names(self):
        class C(object):
            @autoargs(include=('bar', 'baz', 'verbose'))
            def __init__(self, foo, bar, baz, verbose=False):
                pass

        a = C('rhubarb', 'pie', 1)
        self.assertTrue(a.bar == 'pie')
        self.assertTrue(a.baz == 1)
        self.assertTrue(a.verbose == False)
        self.assertRaises(AttributeError, getattr, a, 'foo')


    def test_autoargs_exclude(self):
        class C(object):
            @autoargs(exclude=('bar', 'baz', 'verbose'))
            def __init__(self, foo, bar, baz, verbose=False):
                pass

        a = C('rhubarb', 'pie', 1)
        self.assertTrue(a.foo == 'rhubarb')
        self.assertRaises(AttributeError, getattr, a, 'bar')

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

    def test_autoprops(self):

        from contracts import ContractNotRespected
        from contracts import contract

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

        from contracts import ContractNotRespected
        from contracts import contract

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


    def test_autoprops_override(self):

        from contracts import ContractNotRespected
        from contracts import contract

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