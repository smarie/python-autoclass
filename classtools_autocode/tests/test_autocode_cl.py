from typing import List
from unittest import TestCase

from classtools_autocode.class_utils import autoargs, autoprops


class TestAutoCode(TestCase):

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

    def test_autoprops(self):

        from contracts import ContractNotRespected
        from contracts import contract

        @autoprops
        class FooConfig(object):

            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfig('rhubarb', ['pie', 'pie2'])
        self.assertRaises(ContractNotRespected, setattr, t, 'a', '')
        self.assertRaises(ContractNotRespected, setattr, t, 'b', ['r',''])
        t.b=['r']
        self.assertTrue(t.b[0] == 'r')


    def test_autoprops_include(self):

        from contracts import ContractNotRespected
        from contracts import contract

        @autoprops(include='a')
        class FooConfig(object):

            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfig('rhubarb', ['pie', 'pie2'])
        self.assertRaises(ContractNotRespected, setattr, t, 'a', '')
        t.b=[''] # we can because there is no property
        self.assertTrue(t.b[0] == '')