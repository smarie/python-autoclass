from typing import Any, Union, Tuple, TypeVar  # do not import Type for compatibility with earlier python 3.5

from autoclass.autoargs_ import autoargs_decorate
from autoclass.autoprops_ import autoprops_decorate
from autoclass.autodict_ import autodict_decorate
from autoclass.utils_reflexion import get_constructor
from autoclass.utils_decoration import _create_class_decorator__robust_to_args
from autoclass.autohash_ import autohash_decorate


def autoclass(include: Union[str, Tuple[str]]=None, exclude: Union[str, Tuple[str]]=None,
              autoargs: bool=True, autoprops: bool=True, autodict: bool=True, autohash: bool=True):
    """
    A decorator to perform @autoargs, @autoprops and @autodict all at once with the same include/exclude list.

    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param autoargs: a boolean to enable autoargs on the consturctor (default: True)
    :param autoprops: a boolean to enable autoargs on the consturctor (default: True)
    :param autodict: a boolean to enable autoargs on the consturctor (default: True)
    :param autohash: a boolean to enable autohash on the constructor (default: True)
    :return:
    """
    return _create_class_decorator__robust_to_args(autoclass_decorate, include, exclude=exclude, autoargs=autoargs,
                                                   autoprops=autoprops, autodict=autodict, autohash=autohash)


T = TypeVar('T')


def autoclass_decorate(cls: 'Type[T]', include: Union[str, Tuple[str]] = None, exclude: Union[str, Tuple[str]] = None,
                       autoargs: bool=True, autoprops: bool=True, autodict: bool=True, autohash: bool=True) \
        -> 'Type[T]':
    """

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attributes to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param autoargs: a boolean to enable autoargs on the consturctor (default: True)
    :param autoprops: a boolean to enable autoprops on the consturctor (default: True)
    :param autodict: a boolean to enable autodict on the consturctor (default: True)
    :param autohash: a boolean to enable autohash on the constructor (default: True)
    :return:
    """

    # @autoargs
    if autoargs:
        init = get_constructor(cls)
        cls.__init__ = autoargs_decorate(init, include=include, exclude=exclude)

    # @autoprops
    if autoprops:
        autoprops_decorate(cls, include=include, exclude=exclude)

    # @autodict
    if autodict:
        autodict_decorate(cls, include=include, exclude=exclude)

    # @autohash
    if autohash:
        autohash_decorate(cls, include=include, exclude=exclude)

    return cls
