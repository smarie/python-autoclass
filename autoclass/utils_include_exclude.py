from typing import Union, Tuple


def _sieve(attr, include:Union[str, Tuple[str]]=None, exclude:Union[str, Tuple[str]]=None):
    """decide whether an action has to be performed on the attribute or not, based on its name"""

    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

    # win time by not doing this
    # check_var(include, var_name='include', var_types=[str, tuple], enforce_not_none=False)
    # check_var(exclude, var_name='exclude', var_types=[str, tuple], enforce_not_none=False)

    if attr is 'self':
        return False
    if exclude and attr in exclude:
        return False
    if not include or attr in include:
        return True
    else:
        return False