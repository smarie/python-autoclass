from inspect import getmembers, signature
from typing import Type, Any, Tuple, Callable, Union, Optional
from warnings import warn

from decorator import decorate

from autoclass import check_var
from autoclass.validate import validate_decorate
from autoclass.autoargs import get_constructor, _sieve
from autoclass.utils import _create_function_decorator__robust_to_args, _create_class_decorator__robust_to_args

from collections import Mapping


def autodict(include: Union[str, Tuple[str]]=None, exclude: Union[str, Tuple[str]]=None):
    """
    A decorator to automatically generate the appropriate methods so that objects of this class behave like a `dict`.
    The view will be immutable, see collections.Mapping for implementation details.

    :param include: a named tuple of explicit attributes to include (None means all)
    :param exclude: a named tuple of explicit attributes to exclude. In such case, include should be None.
    :return:
    """
    return _create_class_decorator__robust_to_args(autodict_decorate, include, exclude=exclude)


def autodict_decorate(cls: Type[Any], include: Union[str, Tuple[str]] = None,
                      exclude: Union[str, Tuple[str]] = None) -> Type[Any]:
    """
    To automatically generate the appropriate methods so that objects of this class behave like a `dict`,
    manually, without using @autodict decorator. The view will be immutable, see collections.Mapping for implementation
    details.

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a named tuple of explicit attributes to include (None means all)
    :param exclude: a named tuple of explicit attributes to exclude. In such case, include should be None.
    :return:
    """

    # perform the class mod
    _execute_autodict_on_class(cls, include=include, exclude=exclude)

    return cls


def _execute_autodict_on_class(object_type: Type[Any], include: Union[str, Tuple[str]]=None,
                               exclude: Union[str, Tuple[str]]=None):
    """
    This method will generate the appropriate methods so that objects of the class behave like a `dict`. These methods
    are the ones from collections.Mapping

    :param object_type: the class on which to execute.
    :param include: a named tuple of explicit attributes to include (None means all)
    :param exclude: a named tuple of explicit attributes to exclude. In such case, include should be None.
    :return:
    """

    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')
    check_var(include, var_name='include', var_types=[str, tuple], enforce_not_none=False)
    check_var(exclude, var_name='exclude', var_types=[str, tuple], enforce_not_none=False)

    # 1. add the methods from Mapping to the class
    # -- current proposition: add inheritance dynamically
    object_type.__bases__ = (Mapping,) + object_type.__bases__[:]
    # -- alternate way: add methods one by one
    # meths = getmembers(Mapping, predicate=callable)
    # for name, func in meths:
    #     if name != '__getitem__':
    #         # bind method to this class too (we access 'im_func' to get the original method)
    #         setattr(object_type, name, func.im_func)

    # 2. finally implement the abstract method required by Mapping to work
    if hasattr(object_type, '__getitem__'):
        warn('__getitem__ is already defined on this class, it will be overriden with the generated one !')

    def __getitem__(self, key):
        if hasattr(self, key):
            if _sieve(key, include=include, exclude=exclude):
                # we don't return self.__dict__[key] because we allow @autodict to work with nonexistent field names
                return getattr(self, key)
            else:
                raise KeyError('This field has been removed from the dict view generated on top of this object using '
                               '@autodict')
        else:
            raise KeyError('Invalid field name: ' + key)

    object_type.__getitem__ = __getitem__

    return
