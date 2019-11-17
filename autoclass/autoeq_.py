#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.

#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
from warnings import warn

try:  # python 3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

try:
    from typing import Any, Tuple, Union, Dict, TypeVar, Callable, Iterable, Sized
    try:
        from typing import Type
    except ImportError:
        pass
    T = TypeVar('T')
except ImportError:
    pass

from autoclass.utils import is_attr_selected, method_already_there, check_known_decorators, read_fields, \
    __AUTOCLASS_OVERRIDE_ANNOTATION, iterate_on_vars

from decopatch import class_decorator, DECORATED


@class_decorator
def autoeq(include=None,                # type: Union[str, Tuple[str]]
             exclude=None,                # type: Union[str, Tuple[str]]
             only_known_fields=True,      # type: bool
             only_public_fields=True,     # type: bool
             cls=DECORATED
             ):
    """
    A decorator to generate eq method for class cls if not already implemented
    Parameters allow to customize the list of fields that will be used in the comparison.

    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_known_fields: if True (default), only known fields (constructor arguments or pyfields fields) will be
        used in the eq comparison, not any other field that would be created in the constructor or
        dynamically. If set to False, *all* public object fields will be used. The list can be
        filtered with include/exclude and private fields can be included by setting only_public_fields to false
    :param only_public_fields: this parameter is only used when only_known_fields is set to False. If
        only_public_fields is set to False, all fields are used in the comparison. Otherwise (default), class-private
        fields will not be used
    :return:
    """
    return autoeq_decorate(cls, include=include, exclude=exclude,
                             only_public_fields=only_public_fields, only_known_fields=only_known_fields)


def autoeq_decorate(cls,                      # type: Type[T]
                      include=None,             # type: Union[str, Tuple[str]]
                      exclude=None,             # type: Union[str, Tuple[str]]
                      only_known_fields=True,   # type: bool
                      only_public_fields=True,  # type: bool
                      ):
    # type: (...) -> Type[T]
    """
    To automatically generate the appropriate eq methods, without using @autoeq decorator.

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_known_fields: if True (default), only known fields (constructor arguments or pyfields fields) will be
        used in the eq comparison, not any other field that would be created in the constructor or
        dynamically. If set to False, *all* public object fields will be used. The list can be
        filtered with include/exclude and private fields can be included by setting only_public_fields to false
    :param only_public_fields: this parameter is only used when only_known_fields is set to False. If
        only_public_fields is set to False, all fields are used in the comparison. Otherwise (default), class-private
        fields will not be used
    :return:
    """
    # first check that we do not conflict with other known decorators
    check_known_decorators(cls, '@autoeq')

    # perform the class mod
    if only_known_fields:
        # retrieve the list of fields from pyfields or constructor signature
        selected_names, source = read_fields(cls, include=include, exclude=exclude, caller="@autoeq")

        # add autohash with explicit list
        execute_autoeq_on_class(cls, selected_names=selected_names)
    else:
        # no explicit list
        execute_autoeq_on_class(cls, include=include, exclude=exclude, public_fields_only=only_public_fields)

    return cls


def execute_autoeq_on_class(cls,                      # type: Type[T]
                              selected_names=None,      # type: Iterable[str]
                              include=None,             # type: Union[str, Tuple[str]]
                              exclude=None,             # type: Union[str, Tuple[str]]
                              public_fields_only=True,  # type: bool
                              ):
    """
    This method overrides eq method if not already implemented

    Parameters allow to customize the list of fields that will be visible.

    :param cls: the class on which to execute.
    :param selected_names: an explicit list of attribute names that should be used in the dict. If this is provided,
        `include`, `exclude` and `public_fields_only` should be left as default as they are not used.
    :param include: a tuple of explicit attribute names to include (None means all). This parameter is only used when
        `selected_names` is not provided.
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None. This
        parameter is only used when `selected_names` is not provided.
    :param public_fields_only: this parameter is only used when `selected_names` is not provided. If
        public_fields_only is set to False, all fields are visible. Otherwise (default), class-private fields will be
        hidden from the comparison.
    :return:
    """
    if selected_names is not None:
        # case (a) hardcoded list - easy: we know the exact list of fields to make visible
        if include is not None or exclude is not None or public_fields_only is not True:
            raise ValueError("`selected_names` can not be used together with `include`, `exclude` or "
                             "`public_fields_only`")

        eq_method = create_eq_method_for_hardcoded_list(selected_names)

    else:
        # case (b) the list of fields is not predetermined, it will depend on vars(self)
        if include is None and exclude is None and not public_fields_only:
            # easy: all vars() are exposed
            eq_method = create_eq_method_for_object_vars()
        else:
            # harder: all fields are allowed, but there are filters on this dynamic list
            # private_name_prefix = '_' + object_type.__name__ + '_'
            private_name_prefix = '_' if public_fields_only else None
            eq_method = create_eq_method_for_object_vars_with_filters(include=include, exclude=exclude,
                                                                      private_name_prefix=private_name_prefix)

    if method_already_there(cls, '__eq__', this_class_only=True):
        if not hasattr(cls.__eq__, __AUTOCLASS_OVERRIDE_ANNOTATION):
            warn('__eq__ is already defined on class %s, it will be overridden with the one generated by '
                 '@autoeq/@autoclass ! If you want to use your version, annotate it with @autoclass_override'
                 % cls)
            cls.__eq__ = eq_method
    else:
        cls.__eq__ = eq_method


def create_eq_method_for_hardcoded_list(selected_names,  # type: Union[Sized, Iterable[str]]
                                         ):
    # type: (...) -> Callable
    """

    :param selected_names:
    :return:
    """
    def __eq__(self, other):
        """
        Generated by @autoeq. Relies on the hardcoded list of field names and "getattr" (object) for the value.
        """
        try:
            for att_name in selected_names:
                if getattr(self, att_name) != getattr(other, att_name):
                    return False
        except AttributeError:
            return False
        else:
            return True

    return __eq__


def create_eq_method_for_object_vars():
    # type: (...) -> Callable
    """

    :return:
    """
    def __eq__(self, other):
        """
        Generated by @autoeq. Relies on the list of vars()  and "getattr" (object) for the value.
        """
        for att_name in iterate_on_vars(self):
            if getattr(self, att_name) != getattr(other, att_name):
                return False
        return True

    return __eq__


def create_eq_method_for_object_vars_with_filters(include,                  # type: Union[str, Tuple[str]]
                                                  exclude,                  # type: Union[str, Tuple[str]]
                                                  private_name_prefix=None  # type: str
                                                  ):
    # type: (...) -> Callable
    """

    :param include:
    :param exclude:
    :param private_name_prefix:
    :return:
    """
    public_fields_only = private_name_prefix is not None

    def _vars_iterator(self):
        """
        Filters the vars(self) according to include/exclude/public_fields_only

        :param self:
        :return:
        """
        for att_name in iterate_on_vars(self):
            # filter based on the name (include/exclude + private/public)
            if is_attr_selected(att_name, include=include, exclude=exclude) and \
                    (not public_fields_only or not att_name.startswith(private_name_prefix)):
                # use it
                yield att_name

    def __eq__(self, other):
        """
        Generated by @autoeq. Relies on the filtered list of vars() and "getattr" (object) for the value.
        """
        for att_name, att_value in _vars_iterator(self):
            if getattr(self, att_name) != getattr(other, att_name):
                return False
        return True

    return __eq__
