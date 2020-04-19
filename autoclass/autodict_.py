try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

from itertools import chain
from warnings import warn

from six import with_metaclass

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

from autoclass.autoprops_ import DuplicateOverrideError
from autoclass.utils import is_attr_selected, method_already_there, possibly_replace_with_property_name, \
    check_known_decorators, AUTO, read_fields, __AUTOCLASS_OVERRIDE_ANNOTATION, iterate_on_vars

from decopatch import class_decorator, DECORATED


__AUTODICT_OVERRIDE_ANNOTATION = __AUTOCLASS_OVERRIDE_ANNOTATION


@class_decorator
def autodict(include=None,                # type: Union[str, Tuple[str]]
             exclude=None,                # type: Union[str, Tuple[str]]
             only_known_fields=True,      # type: bool
             only_public_fields=True,     # type: bool
             legacy_str_repr=False,       # type: bool
             only_constructor_args=AUTO,  # type: bool
             cls=DECORATED
             ):
    """
    A decorator to makes objects of the class behave like a read-only `dict`. It does several things:
    * it adds collections.Mapping to the list of parent classes (i.e. to the class' `__bases__`)
    * it generates `__len__`, `__iter__` and `__getitem__` in order for the appropriate fields to be exposed in the dict
    view.
    * it adds a static from_dict method to build objects from dicts (only if only_constructor_args=True)
    * it overrides eq method if not already implemented
    * it overrides str and repr method if not already implemented
    
    Parameters allow to customize the list of fields that will be visible.

    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_known_fields: if True (default), only known fields (constructor arguments or pyfields fields) will be
        exposed through the dictionary view, not any other field that would be created in the constructor or
        dynamically. If set to False, the dictionary is a direct view of *all* public object fields. This view can be
        filtered with include/exclude and private fields can be made visible by setting only_public_fields to false
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
        only_public_fields is set to False, all fields are visible. Otherwise (default), class-private fields will be
        hidden
    :param legacy_str_repr: turn this to `True` to get the legacy string representation `{%r: %r, ...}` instead of
        the new default one `(%s=%r, ...)`
    :return:
    """
    return autodict_decorate(cls, include=include, exclude=exclude, only_constructor_args=only_constructor_args,
                             only_public_fields=only_public_fields, only_known_fields=only_known_fields,
                             legacy_str_repr=legacy_str_repr)


def autodict_decorate(cls,                         # type: Type[T]
                      include=None,                # type: Union[str, Tuple[str]]
                      exclude=None,                # type: Union[str, Tuple[str]]
                      only_known_fields=True,      # type: bool
                      only_public_fields=True,     # type: bool
                      legacy_str_repr=False,       # type: bool
                      only_constructor_args=AUTO,  # type: bool
                      ):
    # type: (...) -> Type[T]
    """
    To automatically generate the appropriate methods so that objects of this class behave like a `dict`,
    manually, without using @autodict decorator.

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_known_fields: if True (default), only known fields (constructor arguments or pyfields fields) will be
        exposed through the dictionary view, not any other field that would be created in the constructor or
        dynamically. If set to False, the dictionary is a direct view of *all* public object fields. This view can be
        filtered with include/exclude and private fields can be made visible by setting only_public_fields to false
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
        only_public_fields is set to False, all fields are visible. Otherwise (default), class-private fields will be
        hidden
    :param legacy_str_repr: turn this to `True` to get the legacy string representation `{%r: %r, ...}` instead of
        the new default one `(%s=%r, ...)`
    :return:
    """
    if only_constructor_args is not AUTO:
        warn("@autodict: `only_constructor_args` is deprecated and will be removed in a future version, please use "
             "`only_known_fields` instead")
        if only_known_fields is not True:
            raise ValueError("`only_known_fields` is the new name of `only_constructor_args`. Please only set one of "
                             "the two.")
        only_known_fields = only_constructor_args

    # first check that we do not conflict with other known decorators
    check_known_decorators(cls, '@autodict')

    # perform the class mod
    if only_known_fields:
        # retrieve the list of fields from pyfields or constructor signature
        selected_names, source = read_fields(cls, include=include, exclude=exclude, caller="@autodict")

        # add autohash with explicit list
        execute_autodict_on_class(cls, selected_names=selected_names, legacy_str_repr=legacy_str_repr)
    else:
        # no explicit list
        execute_autodict_on_class(cls, include=include, exclude=exclude, public_fields_only=only_public_fields,
                                  legacy_str_repr=legacy_str_repr)

    return cls


def execute_autodict_on_class(cls,                       # type: Type[T]
                              selected_names=None,       # type: Iterable[str]
                              include=None,              # type: Union[str, Tuple[str]]
                              exclude=None,              # type: Union[str, Tuple[str]]
                              public_fields_only=True,   # type: bool
                              legacy_str_repr=False,       # type: bool
                              ):
    """
    This method makes objects of the class behave like a read-only `dict`. It does several things:

     * it adds collections.Mapping to the list of parent classes (i.e. to the class' `__bases__`)
     * it generates `__len__`, `__iter__` and `__getitem__` in order for the appropriate fields to be exposed in the dict
       view.
     * it adds a static from_dict method to build objects from dicts (only if only_constructor_args=True)
     * it overrides eq method if not already implemented
     * it overrides str and repr method if not already implemented

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
        hidden from the exposed dict view.
    :param legacy_str_repr: turn this to `True` to get the legacy string representation `{%r: %r, ...}` instead of
        the new default one `(%s=%r, ...)`
    :return:
    """
    # check if the class is already a dict-like
    super_is_already_a_mapping = issubclass(cls, Mapping)

    # 1. implement the abstract method required by Mapping to work, according to the options
    if selected_names is not None:
        # case (a) hardcoded list - easy: we know the exact list of fields to make visible in the Mapping
        if include is not None or exclude is not None or public_fields_only is not True:
            raise ValueError("`selected_names` can not be used together with `include`, `exclude` or "
                             "`public_fields_only`")

        if not super_is_already_a_mapping:
            # simplest case : use the hardcoded list
            dict_methods = create_dict_methods_for_hardcoded_list(selected_names)

        else:
            # super is a mapping: automatically chain the attributes with the ones in super
            dict_methods = create_dict_methods_for_hardcoded_list_and_super_mapping(cls, selected_names)

    else:
        # case (b) the list of fields is not predetermined, it will depend on vars(self)
        if include is None and exclude is None and not public_fields_only:
            # easy: all vars() are exposed
            if not super_is_already_a_mapping:
                dict_methods = create_dict_facade_for_object_vars()
            else:
                dict_methods = create_dict_facade_for_object_vars_and_mapping(cls)
        else:
            # harder: all fields are allowed, but there are filters on this dynamic list
            # private_name_prefix = '_' + object_type.__name__ + '_'
            private_name_prefix = '_' if public_fields_only else None

            if not super_is_already_a_mapping:
                dict_methods = create_dict_facade_for_object_vars_with_filters(include, exclude, private_name_prefix)
            else:
                dict_methods = create_dict_facade_for_object_vars_and_mapping_with_filters(cls, include, exclude,
                                                                                           private_name_prefix)

    if method_already_there(cls, '__len__', this_class_only=True):
        if not hasattr(cls.__len__, __AUTODICT_OVERRIDE_ANNOTATION):
            warn('__len__ is already defined on class {}, it will be overridden with the one generated by '
                 '@autodict/@autoclass ! If you want to use your version, annotate it with @autodict_override'
                 ''.format(str(cls)))
            cls.__len__ = dict_methods.len
    else:
        cls.__len__ = dict_methods.len

    if method_already_there(cls, '__iter__', this_class_only=True):
        if not hasattr(cls.__iter__, __AUTODICT_OVERRIDE_ANNOTATION):
            warn('__iter__ is already defined on class %s, it will be overridden with the one generated by '
                 '@autodict/@autoclass ! If you want to use your version, annotate it with @autodict_override' % cls)
            cls.__iter__ = dict_methods.iter
    else:
        cls.__iter__ = dict_methods.iter

    if method_already_there(cls, '__getitem__', this_class_only=True):
        if not hasattr(cls.__getitem__, __AUTODICT_OVERRIDE_ANNOTATION):
            warn('__getitem__ is already defined on class %s, it will be overridden with the one generated by '
                 '@autodict/@autoclass ! If you want to use your version, annotate it with @autodict_override' % cls)
            cls.__getitem__ = dict_methods.getitem
    else:
        cls.__getitem__ = dict_methods.getitem

    # 2. add all other methods from Mapping to the class
    # -- current proposition: add inheritance dynamically
    type_bases = cls.__bases__
    if Mapping not in type_bases:
        bazz = tuple(t for t in type_bases if t is not object)
        if len(bazz) == len(type_bases):
            # object was not there
            new_bases = bazz + (Mapping,)
        else:
            # object was there, put it at the end
            new_bases = bazz + (Mapping, object)

        try:
            cls.__bases__ = new_bases
        except TypeError:
            try:
                # maybe a metaclass issue, we can try this
                cls.__bases__ = with_metaclass(type(cls), *new_bases)
            except TypeError:
                # python 2.x and object type is a new-style class directly inheriting from object
                # open bug: https://bugs.python.org/issue672115

                # -- alternate way: add methods one by one
                names = [
                    # no need
                    # '__class__', '__metaclass__', '__subclasshook__', '__init__', '__ne__', '__new__'
                    # no need: object
                    # '__getattribute__','__delattr__','__setattr__','__format__','__reduce__','__reduce_ex__','__sizeof__'
                    # -----
                    # '__getitem__', overridden above
                    # '__iter__', overridden above
                    # '__len__', overridden above
                    # '__eq__', overridden below
                    # '__repr__',  overridden below
                    # '__str__', overridden below
                    '__contains__',
                    'get',
                    'items',
                    'iteritems',
                    'iterkeys',
                    'itervalues',
                    'keys',
                    'values']
                # from inspect import getmembers
                # def is_useful(m):
                #     return m
                # meths = getmembers(Mapping.get(), predicate=is_useful)
                # for name, func in meths:
                for name in names:
                    # bind method to this class too (we access 'im_func' to get the original method)
                    setattr(cls, name, getattr(Mapping, name).im_func)

    # 3. add the static class method to build objects from a dict
    # if only_constructor_args:

    # only do it if there is no existing method on the type
    if not method_already_there(cls, 'from_dict'):
        def from_dict(cls,
                      dct  # type: Dict[str, Any]
                      ):
            """
            Generated by @autodict.
            A class method to construct an object from a dictionary of field values.

            :param cls:
            :param dct:
            :return:
            """
            return cls(**dct)

        cls.from_dict = classmethod(from_dict)

    # 4. override equality method if not already implemented LOCALLY (on this type - we dont care about the super
    # since we'll delegate to them when we can't handle)
    if not method_already_there(cls, '__eq__', this_class_only=True):

        def __eq__(self, other):
            """
            Generated by @autodict.
            In the case the other is of the same type, use the dict comparison. Otherwise, falls back to super.

            :param self:
            :param other:
            :return:
            """
            # in the case the other is of the same type, use the dict comparison, that relies on the appropriate fields
            if isinstance(other, cls):
                return dict(self) == dict(other)
            elif isinstance(other, Mapping):
                return dict(self) == other
            else:
                # else fallback to inherited behaviour, whatever it is
                try:
                    f = super(cls, self).__eq__
                except AttributeError:
                    # can happen in python 2 when adding Mapping inheritance failed
                    return Mapping.__eq__(dict(self), other)
                else:
                    return f(other)

        cls.__eq__ = __eq__

    # 5. override str and repr method if not already implemented
    _1, _2 = "()" if legacy_str_repr else ("", "")
    if not method_already_there(cls, '__str__', this_class_only=True):

        def __str__(self):
            """
            Generated by @autodict. Uses the dict representation and puts the type in front

            :param self:
            :return:
            """
            # python 2 compatibility: use self.__class__ not type()
            return "%s%s%s%s" % (self.__class__.__name__, _1, print_ordered_dict(self, eq_mode=not legacy_str_repr), _2)

        cls.__str__ = __str__

    if not method_already_there(cls, '__repr__', this_class_only=True):
        def __repr__(self):
            """
            Generated by @autodict. Uses the dict representation and puts the type in front.

            :param self:
            :return:
            """
            # python 2 compatibility: use self.__class__ not type()
            return "%s%s%s%s" % (self.__class__.__name__, _1, print_ordered_dict(self, eq_mode=not legacy_str_repr), _2)

        cls.__repr__ = __repr__

    return


def print_ordered_dict(odict,         # type: Mapping
                       eq_mode=False  # type: bool
                       ):
    # type: (...) -> str
    """
    Utility method to get a string representation for an ordered mapping.

    :param odict: an ordered mapping
    :param eq_mode: if `False` (default) the representation will be {%r: %r} whereas otherwise it will be
        `(%s=%r)`
    :return:
    """
    # This destroys the order
    # return str(dict(obj))

    # This follows the order from __iter__
    if eq_mode:
        return '(%s)' % ', '.join('%s=%r' % (k, v) for k, v in odict.items())
    else:
        return '{%s}' % ', '.join('%r: %r' % (k, v) for k, v in odict.items())


def autodict_override_decorate(func  # type: Callable
                               ):
    # type: (...) -> Callable
    """
    Used to decorate a function as an overridden dictionary method (such as __iter__), without using the
    @autodict_override annotation.

    :param func: the function on which to execute. Note that it won't be wrapped but simply annotated.
    :return:
    """

    if func.__name__ not in {'__iter__', '__getitem__', '__len__'}:
        raise ValueError('@autodict_override can only be used on one of the three Mapping methods __iter__,'
                         '__getitem__ and __len__. Found: %s' % func.__name__)

    # Simply annotate the function
    if hasattr(func, __AUTODICT_OVERRIDE_ANNOTATION):
        raise DuplicateOverrideError('Function is overridden twice : %s' % func.__name__)
    else:
        setattr(func, __AUTODICT_OVERRIDE_ANNOTATION, True)

    return func


autodict_override = autodict_override_decorate
"""A decorator to indicate an overridden dictionary method. In this case autodict will not override it and will not 
generate a warning"""


class DictMethods(object):
    """
    Container used in @autodict to exchange the various methods created
    """
    __slots__ = 'iter', 'getitem', 'len'

    def __init__(self, iter, getitem, len=None):
        self.iter = iter
        self.getitem = getitem

        if len is None:
            # Default implementation for dynamic containers: the only way to get the length is to iterate.
            def __len__(self):
                """ Generated by @autodict. Computes the length dynamically based on self.__iter__. """
                return sum(1 for e in self)

            self.len = __len__

        else:
            self.len = len


def create_dict_methods_for_hardcoded_list(selected_names  # type: Union[Sized, Iterable[str]]
                                           ):
    # type: (...) -> DictMethods
    """

    :param selected_names:
    :return:
    """
    def __iter__(self):
        """
        Generated by @autodict. Relies on the hardcoded list of fields to return the iterable of dict keys.
        """
        return iter(selected_names)

    def __getitem__(self, key):
        """
        Generated by @autodict. Relies on the hardcoded list of fields to make sure the key is allowed,
        and then maps the "get" (dict) to "getattr" (object).
        """
        if key not in selected_names:
            raise KeyError('@autodict generated dict view - invalid or hidden field name: %s' % key)

        try:
            # map dict 'get' to object 'getattr'
            return getattr(self, key)
        except AttributeError:
            raise KeyError('@autodict generated dict view - {} is a constructor parameter but is not a '
                           'field (was the constructor called ?)'.format(key))

    selected_len = len(selected_names)

    def __len__(self):
        """
        Generated by @autodict. Relies on hardcoded length of selected_names
        """
        return selected_len

    return DictMethods(iter=__iter__, getitem=__getitem__, len=__len__)


def create_dict_methods_for_hardcoded_list_and_super_mapping(cls,            # type: Type[Mapping]
                                                             selected_names  # type: Union[Sized, Iterable[str]]
                                                             ):
    # type: (...) -> DictMethods
    """

    :param cls:
    :param selected_names:
    :return:
    """
    def __iter__(self):
        """
        Generated by @autodict.
        Relies on the hardcoded list of fields PLUS the super keys to return the iterable of dict keys.
        """
        return chain(selected_names,
                     (o for o in super(cls, self).__iter__() if o not in selected_names))

    def __getitem__(self, key):
        """
        Generated by @autodict. Relies on the hardcoded list of fields to make sure the key is allowed,
        and then maps the "get" (dict) to "getattr" (object) or super "get" (when not found).
        """
        if key in selected_names:
            try:
                # map dict 'get' to object 'getattr'
                return getattr(self, key)
            except AttributeError:
                try:
                    # fallback: super get ?
                    # noinspection PyUnresolvedReferences
                    return super(cls, self).__getitem__(key)
                except Exception as e:
                    raise KeyError('@autodict generated dict view - {key} is a constructor parameter but is not'
                                   ' a field (was the constructor called ?). Delegating to super[{key}] raises '
                                   'an exception: {etyp} {err}'.format(key=key, etyp=type(e).__name__, err=e))
        else:
            try:
                # get on super dict
                # noinspection PyUnresolvedReferences
                return super(cls, self).__getitem__(key)
            except Exception as e:
                raise KeyError('@autodict generated dict view - {key} is not a constructor parameter so not '
                               ' handled by this dict view. Delegating to super[{key}] raised an exception: '
                               '{etyp} {err}'.format(key=key, etyp=type(e).__name__, err=e))

    return DictMethods(iter=__iter__, getitem=__getitem__)


def create_dict_facade_for_object_vars():
    # type: (...) -> DictMethods
    """

    :return:
    """
    def __iter__(self):
        """
        Generated by @autodict. Relies on vars(self) to return the iterable of dict keys.
        """
        return iter(iterate_on_vars(self))

    def __getitem__(self, key):
        """
        Generated by @autodict. Relies on getattr(self, key) to return the items.
        """
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError('@autodict generated dict view - {key} is not a valid field (was the '
                           'constructor called?)'.format(key=key))

    return DictMethods(iter=__iter__, getitem=__getitem__)


def create_dict_facade_for_object_vars_and_mapping(cls  # type: Type[Mapping]
                                                   ):
    # type: (...) -> DictMethods
    """

    :param cls:
    :return:
    """
    def __iter__(self):
        """
        Generated by @autodict.
        Implements the __iter__ method from collections.Iterable by relying on vars(self)
        PLUS the super dictionary
        """
        return chain(iterate_on_vars(self),
                     (o for o in super(cls, self).__iter__() if o not in iterate_on_vars(self)))

    def __getitem__(self, key):
        """
        Generated by @autodict.
        Implements the __getitem__ method from collections.Mapping by relying on getattr(self, key)
        PLUS the super dictionary
        """
        try:
            return getattr(self, key)
        except AttributeError:
            try:
                # noinspection PyUnresolvedReferences
                return super(cls, self).__getitem__(key)
            except Exception as e:
                raise KeyError('@autodict generated dict view - {key} is not a valid field (was the '
                               'constructor called?). Delegating to super[{key}] raises an exception: '
                               '{etyp} {err}'.format(key=key, etyp=type(e).__name__, err=e))

    return DictMethods(iter=__iter__, getitem=__getitem__)


def create_dict_facade_for_object_vars_with_filters(include,                  # type: Union[str, Tuple[str]]
                                                    exclude,                  # type: Union[str, Tuple[str]]
                                                    private_name_prefix=None  # type: str
                                                    ):
    # type: (...) -> DictMethods
    """

    :param include:
    :param exclude:
    :param private_name_prefix: if provided, only the fields not starting with this prefix will be exposed. Otherwise
        all will be exposed
    :return:
    """
    public_fields_only = private_name_prefix is not None

    def __iter__(self):
        """
        Generated by @autodict. Relying on a filtered vars(self) for the keys iterable
        """
        for att_name in iterate_on_vars(self):
            # filter based on the name (include/exclude + private/public)
            if is_attr_selected(att_name, include=include, exclude=exclude) and \
                    (not public_fields_only or not att_name.startswith(private_name_prefix)):
                # use that name
                yield att_name

    def __getitem__(self, key):
        """
        Generated by @autodict.
        Implements the __getitem__ method from collections.Mapping by relying on a filtered getattr(self, key)
        :param self:
        :param key:
        :return:
        """
        if hasattr(self, key):
            key = possibly_replace_with_property_name(self.__class__, key)
            if is_attr_selected(key, include=include, exclude=exclude) and \
                    (not public_fields_only or not key.startswith(private_name_prefix)):
                return getattr(self, key)
            else:
                raise KeyError('@autodict generated dict view - hidden field name: ' + key)
        else:
            raise KeyError('@autodict generated dict view - {key} is an invalid field name (was the '
                           'constructor called? are the constructor arg names identical to the field '
                           'names ?)'.format(key=key))

    return DictMethods(iter=__iter__, getitem=__getitem__)


def create_dict_facade_for_object_vars_and_mapping_with_filters(cls,                      # type: Type[Mapping]
                                                                include,                  # type: Union[str, Tuple[str]]
                                                                exclude,                  # type: Union[str, Tuple[str]]
                                                                private_name_prefix=None  # type: str
                                                                ):
    # type: (...) -> DictMethods
    """

    :param cls:
    :param include:
    :param exclude:
    :param private_name_prefix: if provided, only the fields not starting with this prefix will be exposed. Otherwise
        all will be exposed
    :return:
    """
    public_fields_only = private_name_prefix is not None

    def __iter__(self):
        """
        Generated by @autodict.
        Implements the __iter__ method from collections.Iterable by relying on a filtered vars(self)
        :param self:
        :return:
        """
        myattrs = tuple(att_name for att_name in iterate_on_vars(self))
        for att_name in chain(myattrs, (o for o in super(cls, self).__iter__() if o not in myattrs)):
            # filter based on the name (include/exclude + private/public)
            if is_attr_selected(att_name, include=include, exclude=exclude) and \
                    (not public_fields_only or not att_name.startswith(private_name_prefix)):
                # use that name
                yield att_name

    def __getitem__(self, key):
        """
        Generated by @autodict.
        Implements the __getitem__ method from collections.Mapping by relying on a filtered getattr(self, key)
        """
        if hasattr(self, key):
            key = possibly_replace_with_property_name(self.__class__, key)
            if is_attr_selected(key, include=include, exclude=exclude) and \
                    (not public_fields_only or not key.startswith(private_name_prefix)):
                return getattr(self, key)
            else:
                try:
                    # noinspection PyUnresolvedReferences
                    return super(cls, self).__getitem__(key)
                except Exception as e:
                    raise KeyError('@autodict generated dict view - {key} is a '
                                   'hidden field and super[{key}] raises an exception: {etyp} {err}'
                                   ''.format(key=key, etyp=type(e).__name__, err=e))
        else:
            try:
                # noinspection PyUnresolvedReferences
                return super(cls, self).__getitem__(key)
            except Exception as e:
                raise KeyError('@autodict generated dict view - {key} is an '
                               'invalid field name (was the constructor called?). Delegating to '
                               'super[{key}] raises an exception: {etyp} {err}'
                               ''.format(key=key, etyp=type(e).__name__, err=e))

    return DictMethods(iter=__iter__, getitem=__getitem__)
