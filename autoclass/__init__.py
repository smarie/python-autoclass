from autoclass.utils_init import __remove_all_external_symbols, __get_all_submodules_symbols

__PACKAGE_NAME = 'autoclass'
__SUBMODULES_TO_EXPORT = ['autoclass_', 'autoargs_', 'autoprops_', 'autodict_', 'autohash_', 'var_checker']
# TODO we could rather rely on a regexp mechanism

# (1) allow users to do
#     import <package> as p and then p.<symbol>
__all__ = __get_all_submodules_symbols(__PACKAGE_NAME, __SUBMODULES_TO_EXPORT)
# Note: this is one way to do it, but it would be simpler to check the names in globals() at the end of this file.

# (2) allow users to do
#     from <package> import <symbol>
#
# The following works, but unfortunately IDE like pycharm do not understand
from autoclass.autoargs_ import *
from autoclass.autoclass_ import *
from autoclass.autodict_ import *
from autoclass.autohash_ import *
from autoclass.autoprops_ import *
from autoclass.var_checker import *

# remove all symbols that were imported above but do not belong in this package
__remove_all_external_symbols(__PACKAGE_NAME, globals())

# Otherwise exhaustive list would be required, which is sad
# from autoclass.autoargs_ import autoargs, autoargs_decorate
# from autoclass.autoclass_ import autoclass, autoclass_decorate
# from autoclass.autodict_ import autodict, autodict_override, autodict_decorate, autodict_override_decorate, \
#     print_ordered_dict
# from autoclass.autohash_ import autohash, autohash_decorate
# from autoclass.autoprops_ import IllegalGetterSignatureException, IllegalSetterSignatureException, autoprops, \
#     autoprops_decorate, DuplicateOverrideError, getter_override, setter_override, autoprops_override_decorate
# from autoclass.var_checker import check_var, MissingMandatoryParameterException

# print(__all__)
# print(globals().keys())
# print('Done')
