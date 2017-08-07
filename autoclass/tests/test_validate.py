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
        """ Simple test of the @validate annotation, with custom validator is_mod_3"""

        def is_mod_3(x):
            return x % 3 == 0

        @validate(a=[is_mod_3, gt(1)],
                  b=is_mod_3)
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(21, 15)
        with self.assertRaises(ValidationError):
            # a is not a multiple of 3
            myfunc(1,21)
        with self.assertRaises(ValidationError):
            # b is not a multiple of 3
            myfunc(15,1)
        with self.assertRaises(ValidationError):
            # a is not >= 1
            myfunc(0,0)

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
