try:  # python 3.5+
    from typing import Union, Tuple, TypeVar
    try:  # python 3.5.3+
        from typing import Type
    except ImportError:
        pass
    T = TypeVar('T')
except ImportError:
    pass

from autoclass.autoargs_ import autoargs_decorate
from autoclass.autoprops_ import autoprops_decorate
from autoclass.autodict_ import autodict_decorate
from autoclass.utils import get_constructor
from autoclass.autohash_ import autohash_decorate


from decopatch import class_decorator, DECORATED


@class_decorator
def autoclass(include=None,    # type: Union[str, Tuple[str]]
              exclude=None,    # type: Union[str, Tuple[str]]
              autoargs=True,   # type: bool
              autoprops=True,  # type: bool
              autodict=True,   # type: bool
              autohash=True,   # type: bool
              cls=DECORATED
              ):
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
    return autoclass_decorate(cls, include=include, exclude=exclude, autoargs=autoargs, autoprops=autoprops,
                              autodict=autodict, autohash=autohash)


def autoclass_decorate(cls,             # type: Type[T]
                       include=None,    # type: Union[str, Tuple[str]]
                       exclude=None,    # type: Union[str, Tuple[str]]
                       autoargs=True,   # type: bool
                       autoprops=True,  # type: bool
                       autodict=True,   # type: bool
                       autohash=True    # type: bool
                       ):
    # type: (...) -> Type[T]
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
