import pytest
from autoclass import autoargs


def test_autoargs_simple():
    """ @autoargs Basic functionality, no customization - all constructor arguments are auto-assigned """

    class A(object):
        @autoargs
        def __init__(self, foo, path, debug=False):
            pass

    # Test :
    # -- create an instance
    a = A('rhubarb', 'pie', debug=True)
    # -- check that the fields exist and have the correct value
    assert a.foo == 'rhubarb'
    assert a.path == 'pie'
    assert a.debug == True


def test_autoargs_signature_preserving():
    """ @autoargs Advanced: check that the constructor still has the correct signature """

    class A(object):
        @autoargs
        def __init__(self, foo, path, debug=False):
            pass

    try:
        A()
    except TypeError as e:
        assert e.args[0] == "__init__() missing 2 required positional arguments: 'foo' and 'path'"


def test_autoargs_varargs():
    """
    @autoargs Basic functionality, with special case of variable arguments *args.
    -- note that the variable arguments are stored in a single attribute
    """

    class B(object):
        @autoargs
        def __init__(self, foo, path, debug=False, *args):
            pass

    # Test :
    # -- create an instance
    a = B('rhubarb', 'pie', True, 100, 101)
    # -- check that the fields exist and have the correct value
    assert a.foo == 'rhubarb'
    assert a.path == 'pie'
    assert a.debug == True
    # -- *args is in a single attribute
    assert a.args == (100, 101)


def test_autoargs_varargs_kwvarargs():
    """
    @autoargs Basic functionality, with special case of variable arguments *args and keyword arguments **kw
    -- note that *args are stored in a single attribute while **kw are stored in several attributes
    """

    class C(object):
        @autoargs
        def __init__(self, foo, path, debug=False, *args, **kw):
            pass

    # Test :
    # -- create an instance
    a = C('rhubarb', 'pie', True, 100, 101, verbose=True, bar='bar')
    # -- check that the fields exist and have the correct value
    assert a.foo == 'rhubarb'
    assert a.path == 'pie'
    assert a.debug == True
    # -- *args is in a single attribute
    assert a.args == (100, 101)
    # -- **kw is dispatched in several attributes > NOT ANY MORE
    # assert a.verbose == True
    # assert a.bar == 'bar'
    assert a.kw == dict(verbose=True, bar='bar')


def test_autoargs_noarg():
    """ Same than test_autoargs_simple but with empty arguments list in autoargs """

    class O(object):
        @autoargs()
        def __init__(self, foo, path, debug=False):
            pass

    # Test :
    # -- create an instance
    a = O('rhubarb', 'pie', debug=True)
    # -- check that the fields exist and have the correct value
    assert a.foo == 'rhubarb'
    assert a.path == 'pie'
    assert a.debug == True


def test_autoargs_include():
    """ @autoargs With explicit list of names to include """

    class C(object):
        @autoargs(include=['bar', 'baz', 'verbose'])
        def __init__(self, foo, bar, baz, verbose=False):
            pass

    # Test :
    # -- create an instance
    a = C('rhubarb', 'pie', 1)
    # -- check that the fields exist and have the correct value
    assert a.bar == 'pie'
    assert a.baz == 1
    assert a.verbose == False
    # -- check that a non-included field does not exist
    with pytest.raises(AttributeError):
        print(a.foo)


def test_autoargs_exclude():
    """ @autoargs With explicit list of names to exclude """

    class C(object):
        @autoargs(exclude=('bar', 'baz', 'verbose'))
        def __init__(self, foo, bar, baz, verbose=False):
            pass

    # Test :
    # -- create an instance
    a = C('rhubarb', 'pie', 1)
    # -- check that the fields exist and have the correct value
    assert a.foo == 'rhubarb'
    # -- check that the non-included fields do not exist
    with pytest.raises(AttributeError):
        print(a.bar)
    with pytest.raises(AttributeError):
        print(a.baz)
    with pytest.raises(AttributeError):
        print(a.verbose)


def test_autoargs_include_exclude():
    """ @autoargs assert that you can't use both include/exclude at the same time"""
    with pytest.raises(ValueError):
        class Dummy(object):
            @autoargs(exclude='', include='')
            def __init__(self, foo, bar, baz, verbose=False):
                pass


def test_autoargs_include_exclude_typos():
    """ @autoargs Asserts that errors are correctly raised in case of a nonexistent attribute name in
    include/exclude """

    with pytest.raises(ValueError):
        class Dummy(object):
            @autoargs(exclude='fo')
            def __init__(self, foo, bar, baz, verbose=False):
                pass

    with pytest.raises(ValueError):
        class Dummy(object):
            @autoargs(include='fo')
            def __init__(self, foo, bar, baz, verbose=False):
                pass

# def test_autoargs_exclude_lock():
#     class C(object):
#         @autoargs(exclude=('bar', 'baz', 'verbose'), lock_class_fields=True)
#         def __init__(self, foo, bar, baz, verbose=False):
#             pass
#
#     a = C('rhubarb', 'pie', 1)
#     assert a.foo == 'rhubarb')
#     pytest.raises(AttributeError, getattr, a, 'bar')
#     pytest.raises(AttributeError, setattr, a, 'newa',0)


def test_autoargs_no_double_set_default():
    """ This test ensures that autoargs does not double-set the arguments with default values once with the default
    value, and once with the provided value. This was a bug in older versions of autoclass """

    global counter
    counter = 0

    class Home(object):
        @autoargs
        def __init__(self, foo, bar=False):
            pass

        @property
        def bar(self):
            return self._bar

        @bar.setter
        def bar(self, value):
            global counter
            counter += 1
            self._bar = value

    Home(None, bar=True)
    assert counter == 1
