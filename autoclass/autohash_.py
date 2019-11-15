from warnings import warn

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature

try:
    from typing import Tuple, Union, TypeVar, Iterable
    try:
        from typing import Type
    except ImportError:
        pass
    T = TypeVar('T')

except ImportError:
    pass

from decopatch import class_decorator, DECORATED

from autoclass.utils import is_attr_selected, method_already_there, possibly_replace_with_property_name, read_fields, \
    AUTO
from autoclass.utils import check_known_decorators


@class_decorator
def autohash(include=None,                 # type: Union[str, Tuple[str]]
             exclude=None,                 # type: Union[str, Tuple[str]]
             only_known_fields=False,      # type: bool
             only_public_fields=False,     # type: bool
             only_constructor_args=AUTO,   # type: bool
             cls=DECORATED
             ):
    """
    A decorator to makes objects of the class implement __hash__, so that they can be used correctly for example in
    sets.
    
    Parameters allow to customize the list of attributes that are taken into account in the hash.

    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_known_fields: if False (default), all fields will be included in the hash, whether they are known fields
        (pyfields, constructor arguments) or dynamically added. If True, only known fields (pyfields or constructor
        arguments) will be included in the hash, not any other field that would be created dynamically.
        Please note that this behaviour is the opposite from @autodict.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
        only_public_fields is set to False (default), all fields are used in the hash. Otherwise, class-private fields
        will not be taken into account in the hash. Please note that this behaviour is the opposite from @autodict.
    :return:
    """
    return autohash_decorate(cls, include=include, exclude=exclude, only_constructor_args=only_constructor_args,
                             only_public_fields=only_public_fields, only_known_fields=only_known_fields)


def autohash_decorate(cls,                          # type: Type[T]
                      include=None,                 # type: Union[str, Tuple[str]]
                      exclude=None,                 # type: Union[str, Tuple[str]]
                      only_known_fields=False,      # type: bool
                      only_public_fields=False,     # type: bool
                      only_constructor_args=AUTO,   # type: bool
                      ):
    # type: (...) -> Type[T]
    """
    To automatically generate the appropriate methods so that objects of this class are hashable,
    manually, without using @autohash decorator.

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_known_fields: if False (default), all fields will be included in the hash, whether they are known fields
        (pyfields, constructor arguments) or dynamically added. If True, only known fields (pyfields or constructor
        arguments) will be included in the hash, not any other field that would be created dynamically.
        Please note that this behaviour is the opposite from @autodict.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
        only_public_fields is set to False (default), all fields are used in the hash. Otherwise, class-private fields
        will not be taken into account in the hash. Please note that the default behaviour is `False` because hash needs
        to be "complete" by default (= to see all fields even the private ones), whereas `@autodict` has a default
        behaviour of `public_fields_only=True` because dict view does not wish to expose private fields by default.
        So both behaviours are intuitive but since the parameter name is the same, it might be misleading.
    :return:
    """
    if only_constructor_args is not AUTO:
        warn("@autohash: `only_constructor_args` is deprecated and will be removed in a future version, please use "
             "`only_known_fields` instead")
        if only_known_fields is not False:
            raise ValueError("`only_known_fields` is the new name of `only_constructor_args`. Please only set one of "
                             "the two.")
        only_known_fields = only_constructor_args

    # first check that we do not conflict with other known decorators
    check_known_decorators(cls, '@autohash')

    # perform the class mod
    if only_known_fields:
        # retrieve the list of fields from pyfields or constructor signature
        selected_names, source = read_fields(cls, include=include, exclude=exclude, caller="@autohash")

        # add autohash with explicit list
        execute_autohash_on_class(cls, selected_names=selected_names)
    else:
        # no explicit list
        execute_autohash_on_class(cls, include=include, exclude=exclude, public_fields_only=only_public_fields)

    return cls


def execute_autohash_on_class(cls,                       # type: Type[T]
                              selected_names=None,       # type: Iterable[str]
                              include=None,              # type: Union[str, Tuple[str]]
                              exclude=None,              # type: Union[str, Tuple[str]]
                              public_fields_only=False,  # type: bool
                              ):
    """
    A decorator to make objects of the class implement __hash__, so that they can be used correctly for example in
    sets.

    Parameters allow to customize the list of attributes that are taken into account in the hash.

    :param cls: the class on which to execute.
    :param selected_names: an explicit list of attribute names that should be used in the hash. If this is provided,
        `include`, `exclude` and `public_fields_only` should be left as default as they are not used.
    :param include: a tuple of explicit attribute names to include (None means all). This parameter is only used when
        `selected_names` is not provided.
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None. This
        parameter is only used when `selected_names` is not provided.
    :param public_fields_only: this parameter is only used when `selected_names` is not provided. If
        public_fields_only is set to False (default), all fields are used in the hash. Otherwise, class-private fields
        will not be taken into account in the hash. Please note that the default behaviour is `False` because hash needs
        to be "complete" by default (= to see all fields even the private ones), whereas `@autodict` has a default
        behaviour of `public_fields_only=True` because dict view does not wish to expose private fields by default.
        So both behaviours are intuitive but since the parameter name is the same, it might be misleading.
    :return:
    """
    # Override hash method if not already implemented
    if not method_already_there(cls, '__hash__'):
        if selected_names is not None:
            # case (a) hardcoded list of attribute names
            if include is not None or exclude is not None or public_fields_only is not False:
                raise ValueError("`selected_names` can not be used together with `include`, `exclude` or "
                                 "`public_fields_only`")

            def __hash__(self):
                """
                Generated by @autohash.
                Implements the __hash__ method by hashing a tuple of selected attributes

                :param self:
                :return:
                """
                # note: we prepend a unique hash for the class  > NO, it is more intuitive to not do that.
                # return hash(tuple([type(self)] + [getattr(self, att_name) for att_name in added]))
                return hash(tuple(getattr(self, att_name) for att_name in selected_names))
        else:
            # case (b) the list of fields is not predetermined, it will depend on vars(self)
            if include is None and exclude is None and not public_fields_only:

                # easy: all attributes are included in the hash
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
                # harder: dynamic filter
                private_name_prefix = '_'

                def __hash__(self):
                    """
                    Generated by @autohash.
                    Implements the __hash__ method by hashing the tuple of included/not excluded field values, possibly
                    not including the private fields if `only_public_fields` was set to True

                    :param self:
                    :return:
                    """
                    # Should we prepend a unique hash for the class ? > NO, not very intuitive
                    # to_hash = [type(self)]

                    to_hash = []

                    for att_name, att_value in vars(self).items():
                        # replace private names with property names if needed, so that the filter can apply correctly
                        att_name = possibly_replace_with_property_name(self.__class__, att_name)

                        # filter based on the name (include/exclude + private/public)
                        if is_attr_selected(att_name, include=include, exclude=exclude) and \
                                (not public_fields_only or not att_name.startswith(private_name_prefix)):

                            # accepted: use in the final hash
                            to_hash.append(att_value)

                    return hash(tuple(to_hash))

        # Finally set the method on the class
        cls.__hash__ = __hash__
