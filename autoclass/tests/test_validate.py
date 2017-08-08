from unittest import TestCase

from autoclass import validate, ValidationError, is_even, gt, not_none


class TestValidate(TestCase):

    def test_validate_simple(self):
        """ Simple test of the @validate annotation, with built-in validators is_even and gt(1) """

        @validate(a=[not_none, is_even, gt(1)],
                  b=is_even)
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(84, 82)
        with self.assertRaises(ValidationError):
            # a is None
            myfunc(None,0)
        with self.assertRaises(ValidationError):
            # a is not even
            myfunc(1,0)
        with self.assertRaises(ValidationError):
            # b is not even
            myfunc(2,1)
        with self.assertRaises(ValidationError):
            # a is not >= 1
            myfunc(0,0)

    def test_validate_custom(self):
        """ Simple test of the @validate annotation, with custom validators of several styles"""

        def is_mod_3(x):
            """ A simple validator with no parameters"""
            return x % 3 == 0

        def is_mod(ref):
            """ A validator generator, with parameters """
            def is_mod_ref(x):
                return x % ref == 0
            return is_mod_ref

        def gt_ex1(x):
            """ A validator raising a custom exception in case of failure """
            if x >= 1:
                return True
            else:
                raise ValidationError('gt_ex1: x >= 1 does not hold for x=' + str(x))

        def gt_assert2(x):
            """ (not recommended) A validator relying on assert and therefore only valid in 'debug' mode """
            assert x >= 2

        @validate(a=[gt_ex1, gt_assert2, is_mod_3],
                  b=is_mod(5))
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(21, 15)
        with self.assertRaises(ValidationError):
            myfunc(4,21)  # ValidationError: a is not a multiple of 3
        with self.assertRaises(ValidationError):
            myfunc(15,1)  # ValidationError: b is not a multiple of 5
        with self.assertRaises(AssertionError):
            myfunc(1,0)  # AssertionError: a is not >= 2
        with self.assertRaises(ValidationError):
            myfunc(0,0)  # ValidationError: a is not >= 1

    def test_validate_enforce(self):
        """ Tests that a None will be catched by enforce: no need for not_none validator """
        from enforce import runtime_validation
        from enforce.exceptions import RuntimeTypeError
        from numbers import Integral

        @runtime_validation
        @validate(a=[is_even, gt(1)], b=is_even)
        def myfunc(a: Integral, b):
            print('hello')

        # -- check that the validation works
        myfunc(84, None)  # OK because b has no type annotation nor not_none validator
        with self.assertRaises(RuntimeTypeError):
            myfunc(None, 0)  # RuntimeTypeError: a is None

    def test_validate_name_error(self):
        """ Checks that wrong attribute names cant be provided to @validate"""
        with self.assertRaises(ValueError):
            @validate(ab=[])
            def myfunc(a, b):
                print('hello')

    def test_validate_none_is_allowed(self):
        @validate(a=is_even)
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(84, 82)
        myfunc(None, 0)
