from autoclass.utils_init import __remove_all_external_symbols, __get_all_submodules_symbols

__PACKAGE_NAME = 'autoclass'
__SUBMODULES_TO_EXPORT = ['autoclass_', 'autoargs_', 'autoprops_', 'autodict_', 'autohash_', 'var_checker']


# ------------------------------------------------------------


# ------------------------------------------------------------

# (1) allow users to do
#     import <package> as p and then p.<symbol>
__all__ = __get_all_submodules_symbols(__PACKAGE_NAME, __SUBMODULES_TO_EXPORT)


# (2) allow users to do
#     from <package> import <symbol>
from autoclass.autoclass_ import *
from autoclass.autoargs_ import *
from autoclass.autoclass_ import *
from autoclass.autoprops_ import *
from autoclass.autodict_ import *
from autoclass.var_checker import *
from autoclass.autohash_ import *

# remove all symbols that were imported above but do not belong in this package
__remove_all_external_symbols(__PACKAGE_NAME, globals())

# print(__all__)
# print(globals().keys())
# print('Done')
