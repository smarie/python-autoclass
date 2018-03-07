from typing import Callable, Union, List, Set

"""
This var checker is only provided here as an example of what you'd like to do when you dont use any contract library
"""


class MissingMandatoryParameterException(Exception):
    """ This is raised whenever a mandatory parameter is missing or null/None"""


def check_var(var, var_types:Union[type, List[type]] =None, var_name=None, enforce_not_none:bool = True,
              allowed_values:Set = None, min_value = None, min_strict:bool = False,
              max_value = None, max_strict:bool = False, min_len:int = None, min_len_strict:bool = False,
              max_len:int = None, max_len_strict:bool = False):
    """
    Helper method to check that an object has certain properties:
    * not none
    * a certain type
    * in some accepted values
    * in some accepted range

    :param var: the object to check
    :param var_types: the type(s) to enforce. If None, type will not be enforced
    :param var_name: the name of the varioable to be used in error messages
    :param enforce_not_none: boolean, default True. Whether to enforce that var is not None.
    :param allowed_values: an optional set of allowed values
    :param min_value: an optional minimum value
    :param min_strict: if True, only values strictly greater than the minimum value will be accepted
    :param max_value: an optional maximum value
    :param max_strict: if True, only values strictly lesser than the minimum value will be accepted
    :return:
    """

    var_name = var_name or 'object'

    if enforce_not_none and (var is None):
        # enforce not none
        raise MissingMandatoryParameterException('Error, ' + var_name + '" is mandatory, it should be non-None')

    if not (var is None) and not (var_types is None):
        # enforce type
        if not isinstance(var_types, list):
            var_types = [var_types]

        match = False
        for var_type in var_types:
            # just in case, even though users should use FunctionType or MethodType which is the true type
            if var_type is Callable:
                if callable(var):
                    match = True
                    break
            else:
                if isinstance(var, var_type):
                    match = True
                    break

        if not match:
            raise TypeError('Error, ' + var_name + '" should be one of type(s) ' + str(var_types) + ', found: ' + str(type(var)))

    if var is not None:
        if allowed_values is not None:
            # enforce allowed values
            if var not in allowed_values:
                raise TypeError('Error, ' + var_name + '" should be one of "' + str(allowed_values) + '", found: ' + str(var))

        if min_value is not None:
            # enforce min value
            if min_strict:
                if not (var > min_value):
                    raise TypeError(
                        'Error, ' + var_name + '" should be strictly greater than "' + str(min_value) + '", found: ' + str(var))
            else:
                if not (var >= min_value):
                    raise TypeError(
                        'Error, ' + var_name + '" should be greater than "' + str(min_value) + '", found: ' + str(var))

        if max_value is not None:
            # enforce max value
            if max_strict:
                if not (var < max_value):
                    raise TypeError(
                        'Error, ' + var_name + '" should be strictly lesser than "' + str(max_value) + '", found: ' + str(var))
            else:
                if not (var <= max_value):
                    raise TypeError(
                        'Error, ' + var_name + '" should be lesser than "' + str(max_value) + '", found: ' + str(var))

        if min_len is not None:
            # enforce min length
            if min_len_strict:
                if not (len(var) > min_len):
                    raise TypeError(
                        'Error, ' + var_name + '" length should be strictly greater than "' + str(min_len) + '", found: ' + str(len(var)))
            else:
                if not (len(var) >= min_len):
                    raise TypeError(
                        'Error, ' + var_name + '" length should be greater than "' + str(min_len) + '", found: ' + str(len(var)))

        if max_len is not None:
            # enforce max length
            if max_len_strict:
                if not (len(var) < max_len):
                    raise TypeError(
                        'Error, ' + var_name + '" length should be strictly lesser than "' + str(max_len) + '", found: ' + str(len(var)))
            else:
                if not (len(var) <= max_len):
                    raise TypeError(
                        'Error, ' + var_name + '" length should be lesser than "' + str(max_len) + '", found: ' + str(len(var)))
