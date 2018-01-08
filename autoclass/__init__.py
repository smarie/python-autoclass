# allow users to do
#     from autoclass import xxx
from autoclass.autoargs import *
from autoclass.autoclass import *
from autoclass.autoprops import *
from autoclass.autodict import *
from autoclass.var_checker import *
from autoclass.autohash import *

# allow users to do
#     import autoclass as ac
__all__ = ['autoclass', 'autoargs', 'autoprops', 'autodict', 'autohash', 'var_checker']
