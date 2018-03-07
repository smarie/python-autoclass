from collections import Sequence
from inspect import signature
from typing import Tuple, Union, TypeVar  # do not fail on import Type for compatibility with earlier python 3.5

from autoclass.var_checker import check_var
from autoclass.utils_include_exclude import _sieve
from autoclass.utils_reflexion import get_constructor
from autoclass.utils_decoration import _create_class_decorator__robust_to_args, _check_known_decorators


def autohash(include: Union[str, Tuple[str]]=None, exclude: Union[str, Tuple[str]]=None,
             only_constructor_args: bool = False, only_public_fields: bool = False):
    """
    A decorator to makes objects of the class implement __hash__, so that they can be used correctly for example in
    sets.
    
    Parameters allow to customize the list of attributes that are taken into account in the hash.

    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_constructor_args: if False (default), all fields will be included in the hash, even if they are defined
    in the constructor or dynamically. If True, only constructor arguments will be included in the hash, not any other
    field that would be created in the constructor or dynamically. Please note that this behaviour is the opposite from
    @autodict.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
    only_public_fields is set to False (default), all fields are used in the hash. Otherwise, class-private fields will
    not be taken into account in the hash. Please note that this behaviour is the opposite from @autodict.
    :return:
    """
    return _create_class_decorator__robust_to_args(autohash_decorate, include, exclude=exclude,
                                                   only_constructor_args=only_constructor_args,
                                                   only_public_fields=only_public_fields)


T = TypeVar('T')


def autohash_decorate(cls: 'Type[T]', include: Union[str, Tuple[str]] = None, exclude: Union[str, Tuple[str]] = None,
                      only_constructor_args: bool = False, only_public_fields: bool = False) -> 'Type[T]':
    """
    To automatically generate the appropriate methods so that objects of this class are hashable,
    manually, without using @autohash decorator.

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_constructor_args: if False (default), all fields will be included in the hash, even if they are defined
    in the constructor or dynamically. If True, only constructor arguments will be included in the hash, not any other
    field that would be created in the constructor or dynamically. Please note that this behaviour is the opposite from
    @autodict.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
    only_public_fields is set to False (default), all fields are used in the hash. Otherwise, class-private fields will
    not be taken into account in the hash. Please note that this behaviour is the opposite from @autodict.
    :return:
    """

    # first check that we do not conflict with other known decorators
    _check_known_decorators(cls, '@autohash')

    # perform the class mod
    _execute_autohash_on_class(cls, include=include, exclude=exclude, only_constructor_args=only_constructor_args,
                               only_public_fields=only_public_fields)

    return cls


def _execute_autohash_on_class(object_type: 'Type[T]', include: Union[str, Tuple[str]]=None,
                               exclude: Union[str, Tuple[str]]=None, only_constructor_args: bool = False,
                               only_public_fields: bool = False):
    """
    A decorator to make objects of the class implement __hash__, so that they can be used correctly for example in
    sets.

    Parameters allow to customize the list of attributes that are taken into account in the hash.

    :param object_type: the class on which to execute.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_constructor_args: if False (default), all fields will be included in the hash, even if they are defined
    in the constructor or dynamically. If True, only constructor arguments will be included in the hash, not any other
    field that would be created in the constructor or dynamically. Please note that this behaviour is the opposite from
    @autodict.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
    only_public_fields is set to False (default), all fields are used in the hash. Otherwise, class-private fields will
    not be taken into account in the hash. Please note that this behaviour is the opposite from @autodict.
    :return:
    """

    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')
    check_var(include, var_name='include', var_types=[str, Sequence], enforce_not_none=False)
    check_var(exclude, var_name='exclude', var_types=[str, Sequence], enforce_not_none=False)

    # Override hash method if not already implemented
    if not hasattr(object_type, '__hash__') or object_type.__hash__ is None or object_type.__hash__ == object.__hash__:

        if only_constructor_args:
            # a. Find the __init__ constructor signature
            constructor = get_constructor(object_type)
            s = signature(constructor)

            # b. Collect all attributes that are not 'self' and are included and not excluded
            added = []
            # we assume that the order of attributes will always be the same here....
            for attr_name in s.parameters.keys():
                if _sieve(attr_name, include=include, exclude=exclude):
                    added.append(attr_name)

            # c. Finally build the method
            def __hash__(self):
                """
                Generated by @autohash.
                Implements the __hash__ method by hashing a tuple of selected attributes
                :param self:
                :return:
                """
                # note: we prepend a unique hash for the class  > NO, it is more intuitive to not do that.
                # return hash(tuple([type(self)] + [getattr(self, att_name) for att_name in added]))
                return hash(tuple(getattr(self, att_name) for att_name in added))

        else:
            # ** all dynamic fields are allowed
            if include is None and exclude is None and not only_public_fields:

                # easy: all of vars values is included in the hash
                def __hash__(self):
                    """
                    Generated by @autohash.
                    Implements the __hash__ method by hashing vars(self).values()
                    :param self:
                    :return:
                    """
                    # note: we prepend a unique hash for the class  > NO, it is more intuitive to not do that.
                    # return hash(tuple([type(self)] + list(vars(self).values())))
                    return hash(tuple(vars(self).values()))

            else:
                # harder: dynamic filters
                # private_name_prefix = '_' + object_type.__name__ + '_'
                private_name_prefix = '_'

                def __hash__(self):
                    """
                    Generated by @autohash.
                    Implements the __hash__ method by hashing the tuple of included/not excluded field values, possibly
                    not including the private fields if `only_public_fields` was set to True

                    :param self:
                    :return:
                    """
                    # note: we prepend a unique hash for the class > NO, it is more intuitive to not do that.
                    # to_hash = [type(self)]
                    to_hash = []

                    for att_name, att_value in vars(self).items():
                        if _sieve(att_name, include=include, exclude=exclude):
                            if not only_public_fields \
                                    or (only_public_fields and not att_name.startswith(private_name_prefix)):
                                to_hash.append(att_value)

                    return hash(tuple(to_hash))

        # now set the method on the class
        object_type.__hash__ = __hash__

    return
