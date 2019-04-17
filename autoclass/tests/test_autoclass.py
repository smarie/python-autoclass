import sys
import pytest

from autoclass import autoclass


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work correctly under python 3.7+")
def test_autoclass_enforce_validate_not_reversed():
    """ Tests that if we reverse the annotations orders, it still works. Currently it fails """

    from ._tests_pep484 import test_autoclass_enforce_validate_not_reversed
    test_autoclass_enforce_validate_not_reversed()


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work correctly under python 3.7+")
def test_autoclass_enforce_validate_reversed():
    """ Tests that if we reverse the annotations orders, it still works. Currently it fails """

    from ._tests_pep484 import test_autoclass_enforce_validate_reversed
    test_autoclass_enforce_validate_reversed()


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
def test_readme_pytypes():
    """ Makes sure that the code in the documentation page is correct for the pytypes example """

    from ._tests_pep484 import test_readme_pytypes
    test_readme_pytypes()


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints do not work in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work correctly under python 3.7+")
def test_readme_enforce():
    """ Makes sure that the code in the documentation page is correct for the enforce example """

    from ._tests_pep484 import test_readme_enforce
    test_readme_enforce()


def test_autoclass_inheritance():

    @autoclass
    class Foo(object):
        def __init__(self, foo1, foo2=0):
            pass

    @autoclass
    class Bar(Foo):
        def __init__(self, bar, foo1, foo2=0):
            # this constructor is not actually needed in this case since all fields are already self-assigned here
            super(Bar, self).__init__(foo1, foo2)
            # pass

    a = Bar(2, 'th')
    assert a == {'bar': 2, 'foo1': 'th', 'foo2': 0}
    assert a['foo1'] == 'th'

    # iteration order is fixed
    assert list(a.keys()) == ['bar', 'foo1', 'foo2']

    # order in prints is fixed
    assert str(a) == "Bar({'bar': 2, 'foo1': 'th', 'foo2': 0})"
