#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.
import sys

import pytest


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
