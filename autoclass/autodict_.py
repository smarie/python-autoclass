from collections import Mapping
from warnings import warn

from six import with_metaclass

try:  # python 3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

try:
    from typing import Any, Tuple, Union, Dict, TypeVar, Callable
    try:
        from typing import Type
    except ImportError:
        pass
    T = TypeVar('T')
except ImportError:
    pass

from autoclass.autoprops_ import DuplicateOverrideError
from autoclass.utils import is_attr_selected, method_already_there, possibly_replace_with_property_name, \
    validate_include_exclude
from autoclass.utils import get_constructor
from autoclass.utils import _check_known_decorators

from decopatch import class_decorator, DECORATED


__AUTODICT_OVERRIDE_ANNOTATION = '__autodict_override__'


@class_decorator
def autodict(include=None,                # type: Union[str, Tuple[str]]
             exclude=None,                # type: Union[str, Tuple[str]]
             only_constructor_args=True,  # type: bool
             only_public_fields=True,     # type: bool
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
    :param only_constructor_args: if True (default), only constructor arguments will be exposed through the dictionary
        view, not any other field that would be created in the constructor or dynamically. This makes it very convenient
        to use in combination with @autoargs. If set to False, the dictionary is a direct view of public object fields.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
        only_public_fields is set to False, all fields are visible. Otherwise (default), class-private fields will be
        hidden
    :return:
    """
    return autodict_decorate(cls, include=include, exclude=exclude, only_constructor_args=only_constructor_args,
                             only_public_fields=only_public_fields)


def autodict_decorate(cls,                         # type: Type[T]
                      include=None,                # type: Union[str, Tuple[str]]
                      exclude=None,                # type: Union[str, Tuple[str]]
                      only_constructor_args=True,  # type: bool
                      only_public_fields=True      # type: bool
                      ):
    # type: (...) -> Type[T]
    """
    To automatically generate the appropriate methods so that objects of this class behave like a `dict`,
    manually, without using @autodict decorator.

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_constructor_args: if True (default), only constructor arguments will be exposed through the dictionary
    view, not any other field that would be created in the constructor or dynamically. This makes it very convenient
    to use in combination with @autoargs. If set to False, the dictionary is a direct view of public object fields.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
    only_public_fields is set to False, all fields are visible. Otherwise (default), class-private fields will be hidden
    :return:
    """

    # first check that we do not conflict with other known decorators
    _check_known_decorators(cls, '@autodict')

    # perform the class mod
    _execute_autodict_on_class(cls, include=include, exclude=exclude, only_constructor_args=only_constructor_args,
                               only_public_fields=only_public_fields)

    return cls


def _execute_autodict_on_class(object_type,                 # type: Type[T]
                               include=None,                # type: Union[str, Tuple[str]]
                               exclude=None,                # type: Union[str, Tuple[str]]
                               only_constructor_args=True,  # type: bool
                               only_public_fields=True      # type: bool
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

    :param object_type: the class on which to execute.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param only_constructor_args: if True (default), only constructor arguments will be exposed through the dictionary
        view, not any other field that would be created in the constructor or dynamically. This makes it very convenient
        to use in combination with @autoargs. If set to False, the dictionary is a direct view of public object fields.
    :param only_public_fields: this parameter is only used when only_constructor_args is set to False. If
        only_public_fields is set to False, all fields are visible. Otherwise (default), class-private fields will be
        hidden
    :return:
    """
    # 0. first check parameters
    validate_include_exclude(include, exclude)

    # if issubclass(object_type, Mapping):
    #     raise ValueError('@autodict can not be set on classes that are already subclasses of Mapping, and therefore '
    #                      'already behave like dict')
    super_is_already_a_mapping = issubclass(object_type, Mapping)

    # 1. implement the abstract method required by Mapping to work, according to the options
    if only_constructor_args:
        # ** easy: we know the exact list of fields to make visible in the Mapping
        # a. Find the __init__ constructor signature
        constructor = get_constructor(object_type, allow_inheritance=True)
        s = signature(constructor)

        # b. Collect all attributes that are not 'self' and are included and not excluded
        added = []
        for attr_name in s.parameters.keys():
            if is_attr_selected(attr_name, include=include, exclude=exclude):
                added.append(attr_name)

        # c. Finally build the methods
        def __iter__(self):
            """
            Generated by @autodict.
            Implements the __iter__ method from collections.Iterable by relying on a hardcoded list of fields
            PLUS the super dictionary if relevant
            :param self:
            :return:
            """
            if super_is_already_a_mapping:
                return iter(added + [o for o in super(object_type, self).__iter__() if o not in added])
            else:
                return iter(added)

        # def __len__(self):
        #     """
        #     Generated by @autodict.
        #     Implements the __len__ method from collections.Sized by relying on a hardcoded list of fields
        #     PLUS the super dictionary if relevant
        #     :param self:
        #     :return:
        #     """
        #     if super_is_already_a_mapping:
        #         return len(added) + super(object_type, self).__len__()
        #     else:
        #         return len(added)

        if super_is_already_a_mapping:
            def __getitem__(self, key):
                """
                Generated by @autodict.
                Implements the __getitem__ method from collections.Mapping by relying on a hardcoded list of fields
                PLUS the parent dictionary when not found in self
                :param self:
                :param key:
                :return:
                """
                if key in added:
                    try:
                        return getattr(self, key)
                    except AttributeError:
                        try:
                            return super(object_type, self).__getitem__(key)
                        except Exception as e:
                            raise KeyError('@autodict generated dict view - {key} is a constructor parameter but is not'
                                           ' a field (was the constructor called ?). Delegating to super[{key}] raises '
                                           'an exception: {etyp} {err}'.format(key=key, etyp=type(e).__name__, err=e))
                else:
                    try:
                        return super(object_type, self).__getitem__(key)
                    except Exception as e:
                        raise KeyError('@autodict generated dict view - {key} is not a constructor parameter so not '
                                       ' handled by this dict view. Delegating to super[{key}] raised an exception: '
                                       '{etyp} {err}'.format(key=key, etyp=type(e).__name__, err=e))
        else:
            def __getitem__(self, key):
                """
                Generated by @autodict.
                Implements the __getitem__ method from collections.Mapping by relying on a hardcoded list of fields
                :param self:
                :param key:
                :return:
                """
                if key in added:
                    try:
                        return getattr(self, key)
                    except AttributeError:
                        raise KeyError('@autodict generated dict view - {} is a constructor parameter but is not a '
                                       'field (was the constructor called ?)'.format(key))
                else:
                    raise KeyError('@autodict generated dict view - invalid or hidden field name: %s' % key)

    else:
        # ** all dynamic fields are allowed
        if include is None and exclude is None and not only_public_fields:
            # easy: all of vars is exposed
            def __iter__(self):
                """
                Generated by @autodict.
                Implements the __iter__ method from collections.Iterable by relying on vars(self)
                PLUS the super dictionary if relevant
                :param self:
                :return:
                """
                if super_is_already_a_mapping:
                    return iter(list(vars(self)) + [o for o in super(object_type, self).__iter__()
                                                    if o not in vars(self)])
                else:
                    return iter(vars(self))

            # def __len__(self):
            #     """
            #     Generated by @autodict.
            #     Implements the __len__ method from collections.Sized by relying on vars(self)
            #     PLUS the super dictionary if relevant
            #     :param self:
            #     :return:
            #     """
            #     if super_is_already_a_mapping:
            #         return len(list(vars(self)) + [o for o in super(object_type, self).__iter__()
            #                                        if o not in vars(self)])
            #     else:
            #         return len(vars(self))

            if super_is_already_a_mapping:
                def __getitem__(self, key):
                    """
                    Generated by @autodict.
                    Implements the __getitem__ method from collections.Mapping by relying on getattr(self, key)
                    PLUS the super dictionary
                    :param self:
                    :param key:
                    :return:
                    """
                    try:
                        return getattr(self, key)
                    except AttributeError:
                        try:
                            return super(object_type, self).__getitem__(key)
                        except Exception as e:
                            raise KeyError('@autodict generated dict view - {key} is not a valid field (was the '
                                           'constructor called?). Delegating to super[{key}] raises an exception: '
                                           '{etyp} {err}'.format(key=key, etyp=type(e).__name__, err=e))
            else:
                def __getitem__(self, key):
                    """
                    Generated by @autodict.
                    Implements the __getitem__ method from collections.Mapping by relying on getattr(self, key)
                    :param self:
                    :param key:
                    :return:
                    """
                    try:
                        return getattr(self, key)
                    except AttributeError:
                        raise KeyError('@autodict generated dict view - {key} is not a valid field (was the '
                                       'constructor called?)'.format(key=key))
        else:
            # harder: all fields are allowed, but there are filters on this dynamic list
            # private_name_prefix = '_' + object_type.__name__ + '_'
            private_name_prefix = '_'

            if super_is_already_a_mapping:
                def __iter__(self):
                    """
                    Generated by @autodict.
                    Implements the __iter__ method from collections.Iterable by relying on a filtered vars(self)
                    :param self:
                    :return:
                    """
                    myattrs = [possibly_replace_with_property_name(self.__class__, att_name) for att_name in vars(self)]
                    for att_name in myattrs + [o for o in super(object_type, self).__iter__() if o not in vars(self)]:
                        if is_attr_selected(att_name, include=include, exclude=exclude):
                            if not only_public_fields \
                                    or (only_public_fields and not att_name.startswith(private_name_prefix)):
                                yield att_name
            else:
                def __iter__(self):
                    """
                    Generated by @autodict.
                    Implements the __iter__ method from collections.Iterable by relying on a filtered vars(self)
                    :param self:
                    :return:
                    """
                    for att_name in [possibly_replace_with_property_name(self.__class__, att_name)
                                     for att_name in vars(self)]:
                        if is_attr_selected(att_name, include=include, exclude=exclude):
                            if not only_public_fields \
                                    or (only_public_fields and not att_name.startswith(private_name_prefix)):
                                yield att_name

            # def __len__(self):
            #     """
            #     Generated by @autodict.
            #     Implements the __len__ method from collections.Sized by relying on a filtered vars(self)
            #     :param self:
            #     :return:
            #     """
            #     # rely on iter()
            #     return sum(1 for e in self)

            if super_is_already_a_mapping:
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
                                (not only_public_fields or
                                 (only_public_fields and not key.startswith(private_name_prefix))):
                            return getattr(self, key)
                        else:
                            try:
                                return super(object_type, self).__getitem__(key)
                            except Exception as e:
                                raise KeyError('@autodict generated dict view - {key} is a '
                                               'hidden field and super[{key}] raises an exception: {etyp} {err}'
                                               ''.format(key=key, etyp=type(e).__name__, err=e))
                    else:
                        try:
                            return super(object_type, self).__getitem__(key)
                        except Exception as e:
                            raise KeyError('@autodict generated dict view - {key} is an '
                                           'invalid field name (was the constructor called?). Delegating to '
                                           'super[{key}] raises an exception: {etyp} {err}'
                                           ''.format(key=key, etyp=type(e).__name__, err=e))
            else:
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
                                (not only_public_fields or
                                 (only_public_fields and not key.startswith(private_name_prefix))):
                            return getattr(self, key)
                        else:
                            raise KeyError('@autodict generated dict view - hidden field name: ' + key)
                    else:
                        raise KeyError('@autodict generated dict view - {key} is an invalid field name (was the '
                                       'constructor called? are the constructor arg names identical to the field '
                                       'names ?)'.format(key=key))

    def __len__(self):
        """
        Generated by @autodict.
        Implements the __len__ method from collections.Sized by relying on self.__iter__, so that the length will always
        match the true length.

        :param self:
        :return:
        """
        return sum(1 for e in self)

    if method_already_there(object_type, '__len__', this_class_only=True):
        if not hasattr(object_type.__len__, __AUTODICT_OVERRIDE_ANNOTATION):
            warn('__len__ is already defined on class {}, it will be overridden with the one generated by '
                 '@autodict/@autoclass ! If you want to use your version, annotate it with @autodict_override'
                 ''.format(str(object_type)))
            object_type.__len__ = __len__
    else:
        object_type.__len__ = __len__

    if method_already_there(object_type, '__iter__', this_class_only=True):
        if not hasattr(object_type.__iter__, __AUTODICT_OVERRIDE_ANNOTATION):
            warn('__iter__ is already defined on class {}, it will be overridden with the one generated by '
                 '@autodict/@autoclass ! If you want to use your version, annotate it with @autodict_override'
                 ''.format(str(object_type)))
            object_type.__iter__ = __iter__
    else:
        object_type.__iter__ = __iter__

    if method_already_there(object_type, '__getitem__', this_class_only=True):
        if not hasattr(object_type.__getitem__, __AUTODICT_OVERRIDE_ANNOTATION):
            warn('__getitem__ is already defined on class {}, it will be overridden with the one generated by '
                 '@autodict/@autoclass ! If you want to use your version, annotate it with @autodict_override'
                 ''.format(str(object_type)))
        else:
            object_type.__getitem__ = __getitem__
    else:
        object_type.__getitem__ = __getitem__

    # 2. add the methods from Mapping to the class
    # -- current proposition: add inheritance dynamically
    type_bases = object_type.__bases__
    if Mapping not in type_bases:
        bazz = tuple(t for t in type_bases if t is not object)
        if len(bazz) == len(type_bases):
            # object was not there
            new_bases = bazz + (Mapping,)
        else:
            # object was there, put it at the end
            new_bases = bazz + (Mapping, object)

        try:
            object_type.__bases__ = new_bases
        except TypeError:
            try:
                # maybe a metaclass issue, we can try this
                object_type.__bases__ = with_metaclass(type(object_type), *new_bases)
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
                    setattr(object_type, name, getattr(Mapping, name).im_func)

    # 3. add the static class method to build objects from a dict
    # if only_constructor_args:

    # only do it if there is no existing method on the type
    if not method_already_there(object_type, 'from_dict'):
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

        object_type.from_dict = classmethod(from_dict)

    # 4. override equality method if not already implemented LOCALLY (on this type - we dont care about the super
    # since we'll delegate to them when we can't handle)
    if not method_already_there(object_type, '__eq__', this_class_only=True):

        def __eq__(self, other):
            """
            Generated by @autodict.
            In the case the other is of the same type, use the dict comparison. Otherwise, falls back to super.

            :param self:
            :param other:
            :return:
            """
            # in the case the other is of the same type, use the dict comparison, that relies on the appropriate fields
            if isinstance(other, object_type):
                return dict(self) == dict(other)
            else:
                # else fallback to inherited behaviour, whatever it is
                try:
                    f = super(object_type, self).__eq__
                except AttributeError:
                    # can happen in python 2 when adding Mapping inheritance failed
                    return Mapping.__eq__(dict(self), other)
                else:
                    return f(other)

        object_type.__eq__ = __eq__

    # 5. override str and repr method if not already implemented
    if not method_already_there(object_type, '__str__', this_class_only=True):

        def __str__(self):
            """
            Generated by @autodict.
            Uses the dict representation and puts the type in front

            :param self:
            :return:
            """
            # python 2 compatibility: use self.__class__ not type()
            return self.__class__.__name__ + '(' + print_ordered_dict(self) + ')'

        object_type.__str__ = __str__

    if not method_already_there(object_type, '__repr__', this_class_only=True):
        def __repr__(self):
            """
            Generated by @autodict.
            Uses the dict representation and puts the type in front
            maybe?

            :param self:
            :return:
            """
            # python 2 compatibility: use self.__class__ not type()
            return self.__class__.__name__ + '(' + print_ordered_dict(self) + ')'

        object_type.__repr__ = __repr__

    return


def print_ordered_dict(obj):
    # This destroys the order
    # return str(dict(obj))

    # This follows the order from __iter__
    return '{' + ', '.join('{}: {}'.format(repr(k), repr(v)) for k, v in obj.items()) + '}'


def autodict_override_decorate(func  # type: Callable
                               ):
    # type: (...) -> Callable
    """
    Used to decorate a function as an overridden dictionary method (such as __iter__), without using the
    @autodict_override annotation.

    :param func: the function on which to execute. Note that it won't be wrapped but simply annotated.
    :return:
    """

    if func.__name__ not in {Mapping.__iter__.__name__, Mapping.__getitem__.__name__, Mapping.__len__.__name__}:
        raise ValueError('@autodict_override can only be used on one of the three Mapping methods __iter__,'
                         '__getitem__ and __len__. Found: ' + func.__name__)

    # Simply annotate the function
    if hasattr(func, __AUTODICT_OVERRIDE_ANNOTATION):
        raise DuplicateOverrideError('Function is overridden twice : ' + func.__name__)
    else:
        setattr(func, __AUTODICT_OVERRIDE_ANNOTATION, True)

    return func


autodict_override = autodict_override_decorate
"""A decorator to indicate an overridden dictionary method. In this case autodict will not override it and will not 
generate a warning"""
