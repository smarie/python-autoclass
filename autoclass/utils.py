try:  # python 3.5+
    from typing import Union, Tuple
except ImportError:
    pass


def is_attr_selected(attr_name,     # type: str
                     include=None,  # type: Union[str, Tuple[str]]
                     exclude=None   # type: Union[str, Tuple[str]]
                     ):
    """decide whether an action has to be performed on the attribute or not, based on its name"""

    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

    # win time by not doing this
    # check_var(include, var_name='include', var_types=[str, tuple], enforce_not_none=False)
    # check_var(exclude, var_name='exclude', var_types=[str, tuple], enforce_not_none=False)

    if attr_name is 'self':
        return False
    if exclude and attr_name in exclude:
        return False
    if not include or attr_name in include:
        return True
    else:
        return False


def get_constructor(typ,
                    allow_inheritance=False  # type: bool
                    ):
    """
    Utility method to return the unique constructor (__init__) of a type

    :param typ: a type
    :param allow_inheritance: if True, the constructor will be returned even if it is not defined in this class
    (inherited). By default this is set to False: an exception is raised when no constructor is explicitly defined in
    the class
    :return: the found constructor
    """
    if allow_inheritance:
        return typ.__init__
    else:
        # check that the constructor is really defined here
        if '__init__' in typ.__dict__:
            return typ.__init__
        else:
            raise Exception('No explicit constructor was found for class ' + str(typ))


class AutoclassDecorationException(Exception):
    pass


def _check_known_decorators(typ, calling_decorator  # type: str
                            ):
    # type: (...) -> bool
    """
    Checks that a given type is not already decorated by known decorators that may cause trouble.
    If so, it raises an Exception
    :return:
    """
    for member in typ.__dict__.values():
        if hasattr(member, '__enforcer__'):
            raise AutoclassDecorationException('It seems that @runtime_validation decorator was applied to type <'
                                               + str(typ) + '> BEFORE ' + calling_decorator + '. This is not supported '
                                               'as it may lead to counter-intuitive behaviour, please change the order '
                                               'of the decorators on <' + str(typ) + '>')
