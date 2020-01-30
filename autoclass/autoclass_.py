try:  # python 3.5+
    from typing import Union, Tuple, TypeVar
    try:  # python 3.5.3+
        from typing import Type
    except ImportError:
        pass
    T = TypeVar('T')
except ImportError:
    pass

try:  # python 3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

try:
    from pyfields import get_fields, make_init
    WITH_PYFIELDS = True
except ImportError:
    WITH_PYFIELDS = False

from autoclass.utils import get_constructor, AUTO, filter_names, check_known_decorators, read_fields_from_init
from autoclass.autoargs_ import _autoargs_decorate
from autoclass.autoprops_ import execute_autoprops_on_class
from autoclass.autodict_ import execute_autodict_on_class
from autoclass.autorepr_ import execute_autorepr_on_class
from autoclass.autoeq_ import execute_autoeq_on_class
from autoclass.autohash_ import execute_autohash_on_class
from autoclass.autoslots_ import autoslots_decorate

from decopatch import class_decorator, DECORATED


@class_decorator
def autoclass(include=None,     # type: Union[str, Tuple[str]]
              exclude=None,     # type: Union[str, Tuple[str]]
              autoargs=AUTO,    # type: bool
              autoprops=AUTO,   # type: bool
              autodict=True,    # type: bool
              autorepr=AUTO,    # type: bool
              autoeq=AUTO,      # type: bool
              autohash=True,    # type: bool
              autoslots=False,  # type: bool
              autoinit=AUTO,    # type: bool
              cls=DECORATED
              ):
    """
    A decorator to perform @autoargs, @autoprops and @autodict all at once with the same include/exclude list.

    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param autoargs: a boolean to enable autoargs on the constructor. By default it is `AUTO` and means "automatic
        configuration". In that case, the behaviour will depend on the class: it will be equivalent to `True` if the
        class defines an `__init__` method and has no `pyfields` fields ; and `False` otherwise.
    :param autoprops: a boolean to enable autoprops on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, the behaviour will depend on the class: it will be equivalent to `True` if the
        class defines an `__init__` method and has no `pyfields` fields ; and `False` otherwise.
    :param autoinit: a boolean to enable autoinit on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, the behaviour will depend on the class: it will be equivalent to `True` if the
        class has `pyfields` fields and does not define an `__init__` method ; and `False` otherwise.
    :param autodict: a boolean to enable autodict on the class (default: True). By default it will be executed with
        `only_known_fields=True`.
    :param autorepr: a boolean to enable autorepr on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, it will be defined as `not autodict`.
    :param autoeq: a boolean to enable autoeq on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, it will be defined as `not autodict`.
    :param autohash: a boolean to enable autohash on the class (default: True). By default it will be executed with
        `only_known_fields=True`.
    :param autoslots: a boolean to enable autoslots on the class (default: False).
    :return:
    """
    return autoclass_decorate(cls, include=include, exclude=exclude, autoargs=autoargs, autoprops=autoprops,
                              autodict=autodict, autohash=autohash, autoslots=autoslots, autoinit=autoinit,
                              autorepr=autorepr, autoeq=autoeq)


class NoCustomInitError(Exception):
    """
    Raised by `autoclass` when there is no custom __init__ defined on a class but `autoargs` is `True`
    """
    __slots__ = 'cls',

    def __init__(self, cls):
        self.cls = cls

    def __str__(self):
        return "Error applying @autoclass on class %s:  `autoargs=True` can only be used if the class defines a " \
               "custom `__init__`"


def autoclass_decorate(cls,              # type: Type[T]
                       include=None,     # type: Union[str, Tuple[str]]
                       exclude=None,     # type: Union[str, Tuple[str]]
                       autoargs=AUTO,    # type: bool
                       autoprops=AUTO,   # type: bool
                       autoinit=AUTO,    # type: bool
                       autodict=True,    # type: bool
                       autorepr=AUTO,    # type: bool
                       autoeq=AUTO,      # type: bool
                       autohash=True,    # type: bool
                       autoslots=False,  # type: bool
                       ):
    # type: (...) -> Type[T]
    """

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attributes to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param autoargs: a boolean to enable autoargs on the constructor. By default it is `AUTO` and means "automatic
        configuration". In that case, the behaviour will depend on the class: it will be equivalent to `True` if the
        class defines an `__init__` method and has no `pyfields` fields ; and `False` otherwise.
    :param autoprops: a boolean to enable autoprops on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, the behaviour will depend on the class: it will be equivalent to `True` if the
        class defines an `__init__` method and has no `pyfields` fields ; and `False` otherwise.
    :param autoinit: a boolean to enable autoinit on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, the behaviour will depend on the class: it will be equivalent to `True` if the
        class has `pyfields` fields and does not define an `__init__` method ; and `False` otherwise.
    :param autodict: a boolean to enable autodict on the class (default: True). By default it will be executed with
        `only_known_fields=True`.
    :param autorepr: a boolean to enable autorepr on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, it will be defined as `not autodict`.
    :param autoeq: a boolean to enable autoeq on the class. By default it is `AUTO` and means "automatic
        configuration". In that case, it will be defined as `not autodict`.
    :param autohash: a boolean to enable autohash on the class (default: True). By default it will be executed with
        `only_known_fields=True`.
    :param autoslots: a boolean to enable autoslots on the class (default: False).
    :return:
    """
    # first check that we do not conflict with other known decorators
    check_known_decorators(cls, '@autoclass')

    # Get constructor
    init_fun, is_init_inherited = get_constructor(cls)

    # Check for pyfields fields
    if WITH_PYFIELDS:
        all_pyfields = get_fields(cls)
        has_pyfields = len(all_pyfields) > 0
    else:
        has_pyfields = False

    # variable and function used below to get the reference list of attributes
    selected_names, init_fun_sig = None, None

    # ------- @autoslots - this replaces the class so do it first
    if autoslots:
        if has_pyfields:
            raise ValueError("autoslots is not available for classes using `pyfields`")
        cls = autoslots_decorate(cls, include=include, exclude=exclude, use_public_names=not autoprops)

    # ------- @autoargs and @autoprops
    if autoargs is AUTO:
        # apply if the init is defined in the class AND if there are no pyfields
        autoargs = (not is_init_inherited) and (not has_pyfields)
    if autoprops is AUTO:
        # apply if there are no pyfields
        autoprops = not has_pyfields

    # a few common variables
    if autoargs or autoprops:
        # retrieve init function signature and filter its parameters according to include/exclude
        # note: pyfields *can* be present, but for explicit @autoargs and @autoprops we do not use it as a reference
        selected_names, init_fun_sig = read_fields_from_init(init_fun, include=include, exclude=exclude,
                                                             caller="@autoclass")

    # apply them
    if autoargs:
        if is_init_inherited:  # no init explicitly defined in the class > error
            raise NoCustomInitError(cls)
        cls.__init__ = _autoargs_decorate(func=init_fun, func_sig=init_fun_sig, att_names=selected_names)
    if autoprops:
        # noinspection PyUnboundLocalVariable
        execute_autoprops_on_class(cls, init_fun=init_fun, init_fun_sig=init_fun_sig, prop_names=selected_names)

    # create a reference list of attribute names and type hints for all subsequent decorators
    if has_pyfields:
        # Use reference list from pyfields now (even if autoargs was executed, it did not use the correct list)
        # noinspection PyUnboundLocalVariable
        all_names = tuple(f.name for f in all_pyfields)
        selected_names = filter_names(all_names, include=include, exclude=exclude, caller="@autoclass")
        selected_fields = tuple(f for f in all_pyfields if f.name in selected_names)

    elif selected_names is None:
        # Create reference list - autoargs was not executed and there are no pyfields: we need something
        selected_names, init_fun_sig = read_fields_from_init(init_fun, include=include, exclude=exclude,
                                                             caller="@autoclass")

    # autoinit
    if autoinit is AUTO:
        # apply if no init is defined in the class AND if there are pyfields
        autoinit = is_init_inherited and has_pyfields

    if autoinit:
        if not has_pyfields:
            raise ValueError("`autoinit` is only available if you class contains `pyfields` fields.")
        # noinspection PyUnboundLocalVariable
        cls.__init__ = make_init(*selected_fields)

    # @autodict or @autorepr
    if autodict:
        if autorepr is not AUTO and autorepr:
            raise ValueError("`autorepr` can not be set to `True` simultaneously with `autodict`. Please set "
                             "`autodict=False`.")
        if autoeq is not AUTO and autoeq:
            raise ValueError("`autoeq` can not be set to `True` simultaneously with `autodict`. Please set "
                             "`autodict=False`.")
        # By default execute with the known list of fields, so equivalent of `only_known_fields=True`.
        execute_autodict_on_class(cls, selected_names=selected_names)
    else:
        if autorepr is AUTO or autorepr:
            # By default execute with the known list of fields, so equivalent of `only_known_fields=True`.
            execute_autorepr_on_class(cls, selected_names=selected_names)
        if autoeq is AUTO or autoeq:
            # By default execute with the known list of fields, so equivalent of `only_known_fields=True`.
            execute_autoeq_on_class(cls, selected_names=selected_names)

    # @autohash
    if autohash:
        # By default execute with the known list of fields, so equivalent of `only_known_fields=True`.
        execute_autohash_on_class(cls, selected_names=selected_names)

    return cls
