from enum import Enum

try:  # python 3.5+
    from typing import Union, Tuple, Type, Callable, Iterable
except ImportError:
    pass

try:  # python 3+
    from inspect import signature, Signature
except ImportError:
    from funcsigs import signature, Signature


class DuplicateOverrideError(Exception):
    """ This is raised whenever a function is declared as overridden twice"""


__AUTOCLASS_OVERRIDE_ANNOTATION = '__autoclass_override__'


def autoclass_override(func  # type: Callable
                       ):
    # type: (...) -> Callable
    """
    Used to decorate a function as an explcitly overridden method (such as __iter__, __str__), so as to prevent
    @autoclass to override it.

    :param func: the function on which to execute. Note that it won't be wrapped but simply annotated.
    :return:
    """
    # Simply annotate the function
    if hasattr(func, __AUTOCLASS_OVERRIDE_ANNOTATION):
        raise DuplicateOverrideError('Function is overridden twice : %s' % func.__name__)
    else:
        setattr(func, __AUTOCLASS_OVERRIDE_ANNOTATION, True)

    return func


class Symbols(Enum):
    """ A few symbols used in function signatures of the `autoclass` library """
    AUTO = 0

    def __repr__(self):
        return self.name


AUTO = Symbols.AUTO


class Source(Enum):
    """represents the source used by `read_fields`"""
    PYFIELDS = 0
    INIT_ARGS = 1


try:
    from pyfields import get_fields
    WITH_PYFIELDS = True

    def read_fields(cls,
                    include=None,  # type: Union[str, Tuple[str]]
                    exclude=None,  # type: Union[str, Tuple[str]]
                    caller=""      # type: str
                    ):
        # type: (...) -> Tuple[Iterable[str], Source]
        """
        Reads and filters the fields from the given class. If that class has pyfields fields, they will be used.
        Otherwise constructor args will be used.

        :param cls:
        :param include:
        :param exclude:
        :param caller:
        :return:
        """
        # Check for pyfields fields
        all_pyfields = get_fields(cls)
        has_pyfields = len(all_pyfields) > 0

        if has_pyfields:
            # source = pyfields
            all_names = tuple(f.name for f in all_pyfields)
            selected_names = filter_names(all_names, include=include, exclude=exclude, caller=caller)
            return selected_names, Source.PYFIELDS
        else:
            # source = init signature
            selected_names, init_fun_sig = read_fields_from_init(cls.__init__, include=include, exclude=exclude,
                                                                 caller=caller)
            return selected_names, Source.INIT_ARGS

except ImportError:
    WITH_PYFIELDS = False

    def read_fields(cls,
                    include=None,  # type: Union[str, Tuple[str]]
                    exclude=None,  # type: Union[str, Tuple[str]]
                    caller=""      # type: str
                    ):
        # type: (...) -> Iterable[str]
        """
        Reads and filters the fields from the given class. Since pyfields is not available, only the constructor is
        used

        :param cls:
        :param exclude:
        :param include:
        :param caller:
        :return:
        """
        selected_names, init_fun_sig = read_fields_from_init(cls.__init__, include=include, exclude=exclude,
                                                             caller=caller)
        return selected_names, Source.INIT_ARGS


def read_fields_from_init(init_fun,
                          include=None,  # type: Union[str, Tuple[str]]
                          exclude=None,  # type: Union[str, Tuple[str]]
                          caller=""      # type: str
                          ):
    # type: (...) -> Tuple[Iterable[str], Signature]
    """
    Retrieves init function signature and filters its parameters according to include/exclude

    :param init_fun:
    :param include:
    :param exclude:
    :param caller:
    :return: a tuple (selected_names, init_fun_sig)
    """
    # get signature and all of its parameters
    init_fun_sig = signature(init_fun)
    all_names = tuple(n for n in init_fun_sig.parameters.keys() if n != 'self')

    # filter the names
    selected_names = filter_names(all_names, include=include, exclude=exclude, caller=caller)

    return selected_names, init_fun_sig


def filter_names(all_names,
                 include=None,  # type: Union[str, Tuple[str]]
                 exclude=None,  # type: Union[str, Tuple[str]]
                 caller=""      # type: str
                 ):
    # type: (...) -> Iterable[str]
    """
    Common validator for include and exclude arguments

    :param all_names:
    :param include:
    :param exclude:
    :param caller:
    :return:
    """
    if include is not None and exclude is not None:
        raise ValueError("Only one of 'include' or 'exclude' argument should be provided.")

    # check that include/exclude don't contain names that are incorrect
    selected_names = all_names
    if include is not None:
        if exclude is not None:
            raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

        # get the selected names and check that all names in 'include' are actually valid names
        included = (include,) if isinstance(include, str) else tuple(include)
        incorrect = set(included) - set(all_names)
        if len(incorrect) > 0:
            raise ValueError("`%s` definition exception: `include` contains %r that is/are "
                             "not part of %r" % (caller, incorrect, all_names))
        selected_names = included

    elif exclude is not None:
        excluded_set = {exclude} if isinstance(exclude, str) else set(exclude)
        incorrect = excluded_set - set(all_names)
        if len(incorrect) > 0:
            raise ValueError("`%s` definition exception: exclude contains %r that is/are "
                             "not part of %r" % (caller, incorrect, all_names))
        selected_names = tuple(n for n in all_names if n not in excluded_set)

    return selected_names


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


def get_constructor(cls  # type: Type
                    ):
    # type: (...) -> Tuple[Callable, bool]
    """

    :param cls:
    :return: a tuple
    """
    try:
        init = cls.__dict__['__init__']
        is_init_inherited = False
    except KeyError:
        init = cls.__init__
        is_init_inherited = True

    return init, is_init_inherited


class AutoclassDecorationException(Exception):
    pass


def check_known_decorators(cls,
                           calling_decorator  # type: str
                           ):
    """
    Checks that a given type is not already decorated by known decorators that may cause trouble.
    If so, it raises an Exception
    :return:
    """
    for member in cls.__dict__.values():
        if hasattr(member, '__enforcer__'):
            raise AutoclassDecorationException('It seems that @runtime_validation decorator was applied to type <%s> '
                                               'BEFORE %s. This is not supported as it may lead to counter-intuitive '
                                               'behaviour, please change the order of the decorators on <%s>'
                                               % (cls, calling_decorator, cls))


def method_already_there(cls,
                         method_name,           # type: str
                         this_class_only=False  # type: bool
                         ):
    # type: (...) -> bool
    """
    Returns True if method `method_name` is already implemented by object_type, that is, its implementation differs from
    the one in `object`.

    :param cls:
    :param method_name:
    :param this_class_only:
    :return:
    """
    if this_class_only:
        return method_name in vars(cls)  # or cls.__dict__
    else:
        method = getattr(cls, method_name, None)
        return method is not None and method is not getattr(object, method_name, None)


def iterate_on_vars(self):
    """ yields all vars names, replacing them with their public property name if it exists """
    for att_name in vars(self):
        yield possibly_replace_with_property_name(self.__class__, att_name)


def possibly_replace_with_property_name(cls,
                                        att_name  # type: str
                                        ):
    # type: (...) -> str
    """
    Returns the attribute name or the corresponding property name if there is one

    :param cls:
    :param att_name:
    :return:
    """
    return att_name[1:] if is_property_related_attr(cls, att_name) else att_name


def is_property_related_attr(cls,
                             att_name  # type: str
                             ):
    # type: (...) -> bool
    """
    Returns True if the attribute name without a leading underscore corresponds to a property name in that class
    TODO we should extend this to all descriptors

    :param cls:
    :param att_name:
    :return:
    """
    return att_name[0] == '_' and isinstance(getattr(cls, att_name[1:], None), property)
