def __is_defined_in_submodule(submodule_name_prefix, x):
    """
    Utility method to return True if x is not a module and its module name starts with submodule_name_prefix
    e.g. 'autoclass.autohash_'.

    :param submodule_name_prefix:
    :param x:
    :return:
    """
    # if _inspect.ismodule(x):
    #     return False
    # else:
    from inspect import getmodule
    m = getmodule(x)
    if m is None:
        return True
    elif hasattr(m, '__name__') and m.__name__.startswith(submodule_name_prefix):
        return True
    else:
        return False


def __get_all_submodules_symbols(pkg_name, submodules_to_export):
    """
    Generates the list of symbol names that can be used in the `__all__` variable in init.py
    The list is created from a list of submodules.

    All symbols in these submodules that are not private and that are actually defined in there, get in the list.
    The submodules themselves end up in the list.

    Note that this function should only be used if you also actually import those symbols in the init.py, so that they
    are actually visible at package root level.

    :param submodules_to_export: a list of submodule names to export
    :return:
    """
    from inspect import getmembers
    from copy import copy
    from importlib import import_module

    # first create a copy of the submodules list
    all_ = copy(submodules_to_export)

    # then for each submodule add the symbols that are declared in this submodule
    for submodule in submodules_to_export:
        submodule_full_name = pkg_name + '.' + submodule
        imported_module = import_module(submodule_full_name)
        # print(imported_module.__name__)
        for x_name, symbol in getmembers(imported_module):
            if not x_name.startswith('_'):
                if __is_defined_in_submodule(submodule_full_name, symbol):
                    # print('{} is exported'.format(x_name))
                    all_.append(x_name)
    return all_


def __remove_all_external_symbols(pkg_name, globs):
    for x_name in list(globs.keys()):
        if not __is_defined_in_submodule(pkg_name, globs[x_name]):
            del globs[x_name]
