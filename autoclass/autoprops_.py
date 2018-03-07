import hashlib
import linecache
from collections import Sequence
from inspect import getmembers, signature, Parameter
from typing import Any, Tuple, Callable, Union, TypeVar  # do not import Type for compatibility with earlier python 3.5
from warnings import warn

from decorator import decorate

from autoclass.var_checker import check_var
from autoclass.utils_include_exclude import _sieve
from autoclass.utils_reflexion import get_constructor
from autoclass.utils_decoration import _create_function_decorator__robust_to_args, \
    _create_class_decorator__robust_to_args, _check_known_decorators

__GETTER_OVERRIDE_ANNOTATION = '__getter_override__'
__SETTER_OVERRIDE_ANNOTATION = '__setter_override__'


class IllegalGetterSignatureException(Exception):
    """ This is raised whenever an overridden getter has an illegal signature"""


class IllegalSetterSignatureException(Exception):
    """ This is raised whenever an overridden setter has an illegal signature"""


class DuplicateOverrideError(Exception):
    """ This is raised whenever a getter or setter is overridden twice for the same attribute"""


def autoprops(include: Union[str, Tuple[str]]=None, exclude: Union[str, Tuple[str]]=None):
    """
    A decorator to automatically generate all properties getters and setters from the class constructor.
    * if a @contract annotation exist on the __init__ method, mentioning a contract for a given parameter, the
    parameter contract will be added on the generated setter method
    * The user may override the generated getter and/or setter by creating them explicitly in the class and annotating
    them with @getter_override or @setter_override. Note that the contract will still be dynamically added on the
    setter, even if the setter already has one (in such case a `UserWarning` will be issued)

    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :return:
    """
    return _create_class_decorator__robust_to_args(autoprops_decorate, include, exclude=exclude)


T = TypeVar('T')


def autoprops_decorate(cls: 'Type[T]', include: Union[str, Tuple[str]] = None,
                       exclude: Union[str, Tuple[str]] = None) -> 'Type[T]':
    """
    To automatically generate all properties getters and setters from the class constructor manually, without using
    @autoprops decorator.
    * if a @contract annotation exist on the __init__ method, mentioning a contract for a given parameter, the
    parameter contract will be added on the generated setter method
    * The user may override the generated getter and/or setter by creating them explicitly in the class and annotating
    them with @getter_override or @setter_override. Note that the contract will still be dynamically added on the
    setter, even if the setter already has one (in such case a `UserWarning` will be issued)

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :return:
    """

    # first check that we do not conflict with other known decorators
    _check_known_decorators(cls, '@autoprops')

    # perform the class mod
    _execute_autoprops_on_class(cls, include=include, exclude=exclude)

    # TODO better create a wrapper than modify the class? Probably not
    # class Autoprops_Wrapper(object):
    #     def __init__(self, *args, **kwargs):
    #         self.wrapped = cls(*args, **kwargs)
    #
    # return Autoprops_Wrapper

    return cls


def _execute_autoprops_on_class(object_type: 'Type[T]', include: Union[str, Tuple[str]]=None,
                                exclude: Union[str, Tuple[str]]=None):
    """
    This method will automatically add one getter and one setter for each constructor argument, except for those
    overridden using autoprops_override_decorate(), @getter_override or @setter_override.
    It will add a @contract on top of all setters (generated or overridden, if they don't already have one)

    :param object_type: the class on which to execute.
    :param include: a tuple of explicit attribute names to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :return:
    """

    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')
    check_var(include, var_name='include', var_types=[str, Sequence], enforce_not_none=False)
    check_var(exclude, var_name='exclude', var_types=[str, Sequence], enforce_not_none=False)

    # 1. Find the __init__ constructor signature and possible pycontracts @contract
    constructor = get_constructor(object_type)
    s = signature(constructor)

    # option a) pycontracts
    contracts_dict = constructor.__contracts__ if hasattr(constructor, '__contracts__') else {}
    # option b) valid8
    validators_dict = constructor.__validators__ if hasattr(constructor, '__validators__') else {}

    # 2. For each attribute that is not 'self' and is included and not excluded, add the property
    added = []
    for attr_name in s.parameters.keys():
        if _sieve(attr_name, include=include, exclude=exclude):
            added.append(attr_name)
            _add_property(object_type, s.parameters[attr_name],
                          pycontract=(contracts_dict[attr_name] if attr_name in contracts_dict.keys() else None),
                          validators=(validators_dict[attr_name] if attr_name in validators_dict.keys() else None))

    # 3. Finally check that there is no overridden setter or getter that does not correspond to an attribute
    extra_overrides = getmembers(object_type, predicate=(lambda fun: callable(fun) and
                                                                     (hasattr(fun, __GETTER_OVERRIDE_ANNOTATION)
                                                                      and getattr(fun, __GETTER_OVERRIDE_ANNOTATION) not in added)
                                                                      or
                                                                     (hasattr(fun, __SETTER_OVERRIDE_ANNOTATION))
                                                                      and getattr(fun, __SETTER_OVERRIDE_ANNOTATION) not in added)
                                 )
    if len(extra_overrides) > 0:
        raise AttributeError('Attribute named \'' + extra_overrides[0][0] + '\' was not found in constructor signature.'
                             'Therefore its getter/setter can not be overridden by function '
                             + extra_overrides[0][1].__qualname__)


def _add_property(object_type: 'Type[T]', parameter: Parameter, pycontract: Any = None, validators: Any = None):
    """
    A method to dynamically add a property to a class with the optional given pycontract or validators.
    If the property getter and/or setter have been overridden, it is taken into account too.

    :param object_type: the class on which to execute.
    :param parameter:
    :param pycontract:
    :param validators:
    :return:
    """
    property_name = parameter.name

    # 1. create the private field name , e.g. '_foobar'
    private_property_name = '_' + property_name

    # 2. property getter (@property) - create or use overridden
    getter_fun = _get_getter_fun(object_type, parameter, private_property_name)

    # 3. property setter (@property_name.setter) - create or use overridden
    setter_fun, var_name = _get_setter_fun(object_type, parameter, private_property_name)

    # 4. add the contract to the setter, if any
    setter_fun_with_possible_contract = setter_fun
    if pycontract is not None:
        setter_fun_with_possible_contract = _add_contract_to_setter(setter_fun, var_name, pycontract,
                                                                    property_name)
    elif validators is not None:
        setter_fun_with_possible_contract = _add_validators_to_setter(setter_fun, var_name, validators,
                                                                      property_name)

    # 5. change the function name to make it look nice
    setter_fun_with_possible_contract.__name__ = property_name
    setter_fun_with_possible_contract.__module__ = object_type.__module__
    setter_fun_with_possible_contract.__qualname__ = object_type.__name__ + '.' + property_name
    # __annotations__
    # __doc__
    # __dict__

    # 6. Finally add the property to the class
    # WARNING : property_obj.setter(f) does absolutely nothing :) > we have to assign the result
    # setattr(object_type, property_name, property_obj.setter(f))
    new_prop = property(fget=getter_fun, fset=setter_fun_with_possible_contract)

    # # specific for enforce: here we might wrap the overriden property setter on which enforce has already written
    # # something.
    # if hasattr(setter_fun_with_possible_contract, '__enforcer__'):
    #     new_prop.__enforcer__ = setter_fun_with_possible_contract.__enforcer__
    # DESIGN DECISION > although this would probably work, it is probably better to 'force' users to always use the
    # @autoprops annotation BEFORE any other annotation. This is now done in autoprops_decorate

    setattr(object_type, property_name, new_prop)

    return


def _has_annotation(annotation, value):
    """ Returns a function that can be used as a predicate in get_members, that  """

    def matches_property_name(fun):
        """ return true if fun is a callable that has the correct annotation with value """
        return callable(fun) and hasattr(fun, annotation) \
               and getattr(fun, annotation) is value
    return matches_property_name


def _get_getter_fun(object_type: 'Type', parameter: Parameter, private_property_name: str):
    """
    Utility method to find the overridden getter function for a given property, or generate a new one

    :param object_type:
    :param property_name:
    :param private_property_name:
    :return:
    """

    property_name = parameter.name

    # -- check overridden getter for this property name
    overridden_getters = getmembers(object_type, predicate=_has_annotation(__GETTER_OVERRIDE_ANNOTATION, property_name))

    if len(overridden_getters) > 0:
        if len(overridden_getters) > 1:
            raise DuplicateOverrideError('Getter is overridden more than once for attribute name : ' + property_name)

        # --use the overridden getter
        getter_fun = overridden_getters[0][1]

        # --check its signature
        s = signature(getter_fun)
        if not ('self' in s.parameters.keys() and len(s.parameters.keys()) == 1):
            raise IllegalGetterSignatureException('overridden getter must only have a self parameter, found ' +
                                                  str(len(s.parameters.items()) - 1) + ' for function ' + str(
                getter_fun.__qualname__))

        # --use the overridden getter
        property_obj = property(getter_fun)
    else:
        # -- generate the getter :
        # @property
        # def foobar(self):
        #     return self.__foobar

        # --for some reason, this does not work, but the lambda function works !
        # def generated_getter_fun(self):
        #     getattr(self, private_property_name)
        #
        # # -- use the generated getter
        # getter_fun = generated_getter_fun

        getter_fun = lambda self: getattr(self, private_property_name)
        getter_fun.__annotations__['return'] = parameter.annotation  # add type hint to output declaration

    return getter_fun


def _get_setter_fun(object_type: 'Type', parameter: Parameter, private_property_name: str):
    """
    Utility method to find the overridden setter function for a given property, or generate a new one

    :param object_type:
    :param property_name:
    :param property_type:
    :param private_property_name:
    :return:
    """

    property_name = parameter.name

    overridden_setters = getmembers(object_type, _has_annotation(__SETTER_OVERRIDE_ANNOTATION, property_name))

    if len(overridden_setters) > 0:
        # --check that we only have one
        if len(overridden_setters) > 1:
            raise DuplicateOverrideError('Setter is overridden more than once for attribute name : ' + property_name)

        # --use the overridden setter
        setter_fun = overridden_setters[0][1]

        # --find the parameter name and check the signature
        s = signature(setter_fun)
        p = [attribute_name for attribute_name, param in s.parameters.items() if attribute_name is not 'self']
        if len(p) != 1:
            raise IllegalSetterSignatureException('overridden setter must have only 1 non-self argument, found ' +
                                                  str(len(s.parameters.items()) - 1) + ' for function '
                                                  + str(setter_fun.__qualname__))
        var_name = p[0]

    else:
        # --create the setter, equivalent of:
        # @foobar.setter
        # def foobar(self, foobar):
        #     self.__foobar = foobar

        # the internal / debuggable setter function, where you can put breakpoints
        def _autoprops_generated_setter(self, val):
            return setattr(self, private_property_name, val)

        # ** Dynamically compile a wrapper with correct argument name **
        # Credits: https://stackoverflow.com/questions/1409295/set-function-signature-in-python
        #      and https://github.com/python-attrs/attrs/blob/master/src/attr/_make.py

        # Generate a unique file name for this generated code so as to enable caching
        sha1 = hashlib.sha1()
        sha1.update(repr(object_type).encode("utf-8"))
        sha1.update(property_name.encode("utf-8"))
        unique_filename = "<autoprops_generated_setter {}>".format(sha1.hexdigest())

        # the generated wrapper with exact argument name in signature
        setterfunc_src = "def autoprops_generated_setter(self, {att_name}):\n" \
                         "    return _autoprops_generated_setter(self, {att_name})\n".format(att_name=property_name)

        setterfunc_code = compile(setterfunc_src, unique_filename, "exec")
        fakeglobals = {}
        eval(setterfunc_code, {"_autoprops_generated_setter": _autoprops_generated_setter}, fakeglobals)

        # In order of debuggers like PDB being able to step through the code,
        # we add a fake linecache entry.
        linecache.cache[unique_filename] = (
            len(setterfunc_src),
            None,
            setterfunc_src.splitlines(True),
            unique_filename,
        )

        # setter_fun = generated_setter_fun
        setter_fun = fakeglobals['autoprops_generated_setter']

        # remember the parameter name
        # var_name = 'val'
        var_name = property_name

        # add type hint annotation if provided
        if parameter.annotation:
            setter_fun.__annotations__[var_name] = parameter.annotation

        # add default value if provided
        if parameter.default is not Parameter.empty:
            setter_fun.__defaults__ = (parameter.default,)

    return setter_fun, var_name


def _add_contract_to_setter(setter_fun, var_name, property_contract, property_name):

    # 0. check that we can import contracts
    try:
        # noinspection PyUnresolvedReferences
        from contracts import ContractNotRespected, contract
    except ImportError as e:
        raise Exception('Use of _add_contract_to_setter requires that PyContract library is installed. Check that you '
                        'can \'import contracts\'')

    # -- check if a contract already exists on the function
    if hasattr(setter_fun, '__contracts__'):
        msg = 'overridden setter for attribute ' + property_name + ' implemented by function ' \
              + str(setter_fun.__qualname__) + ' has a contract while there is a contract already defined ' \
              + 'for this property in the __init__ constructor. This will lead to double-contract in the final ' \
              + 'setter, please remove the one on the overridden setter.'
        warn(msg)

    # -- add the generated contract
    setter_fun_with_possible_contract = contract(setter_fun, **{var_name: property_contract})

    # the only thing we can't do is to replace the function's parameter name dynamically in the error messages
    # so we wrap the function again to catch the potential pycontracts error :(
    # old:
    # @functools.wraps(func) -> to make the wrapper function look like the wrapped function
    # def wrapper(self, *args, **kwargs):
    # new:
    # we now use 'decorate' to have a wrapper that has the same signature, see below
    def _contracts_parser_interceptor(func, self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ContractNotRespected as er:
            er.error = er.error.replace('\'val\'', '\'' + property_name + '\'')
            raise er

    # f = _contracts_parser_interceptor(f)
    setter_fun_with_possible_contract = decorate(setter_fun_with_possible_contract, _contracts_parser_interceptor)
    return setter_fun_with_possible_contract


def _add_validators_to_setter(setter_fun, var_name, validators, property_name):

    # 0. check that we can import valid8
    # note: this is useless now but maybe one day validate will be another project ?
    try:
        # noinspection PyUnresolvedReferences
        from valid8 import decorate_with_validators
    except ImportError:
        raise Exception('Use of _add_contract_to_setter requires that valid8 library is installed. Check that you can'
                        ' \'import valid8\'')

    # -- check if a contract already exists on the function
    if hasattr(setter_fun, '__validators__'):
        msg = 'overridden setter for attribute ' + property_name + ' implemented by function ' \
              + str(setter_fun.__qualname__) + ' has validators while there are validators already defined ' \
              'for this property in the __init__ constructor. This will lead to double-contract in the final ' \
              'setter, please remove the one on the overridden setter.'
        warn(msg)

    # -- add the generated contract
    setter_fun_with_validation = decorate_with_validators(setter_fun, **{var_name: validators})

    # # the only thing we can't do is to replace the function's parameter name dynamically in the validation error
    # #  messages so we wrap the function again to catch the potential pycontracts error :(
    # # old:
    # # @functools.wraps(func) -> to make the wrapper function look like the wrapped function
    # # def wrapper(self, *args, **kwargs):
    # # new:
    # # we now use 'decorate' to have a wrapper that has the same signature, see below
    # def _contracts_parser_interceptor(func, self, *args, **kwargs):
    #     try:
    #         return func(self, *args, **kwargs)
    #     except ContractNotRespected as e:
    #         e.error = e.error.replace('\'val\'', '\'' + property_name + '\'')
    #         raise e

    # f = _contracts_parser_interceptor(f)
    # setter_fun_with_possible_contract = decorate(setter_fun_with_possible_contract, _contracts_parser_interceptor)
    return setter_fun_with_validation


def getter_override(attribute:str = None):
    """
    A decorator to indicate an overridden getter for a given attribute. If the attribute name is None, the function name
    will be used as the attribute name.

    :param attribute: the attribute name for which the decorated function is an overridden getter
    :return:
    """
    return _create_function_decorator__robust_to_args(autoprops_override_decorate, attribute, is_getter=True)


def setter_override(attribute:str = None):
    """
    A decorator to indicate an overridden setter for a given attribute. If the attribute name is None, the function name
     will be used as the attribute name. The @contract will still be dynamically added.

    :param attribute: the attribute name for which the decorated function is an overridden setter
    :return:
    """
    return _create_function_decorator__robust_to_args(autoprops_override_decorate, attribute, is_getter=False)


def autoprops_override_decorate(func: Callable, attribute:str = None, is_getter:bool = True) -> Callable:
    """
    Used to decorate a function as an overridden getter or setter, without using the @getter_override or
    @setter_override annotations. If the overridden setter has no @contract, the contract will still be
     dynamically added. Note: this should be executed BEFORE @autoprops or autoprops_decorate().

    :param func: the function on which to execute. Note that it won't be wrapped but simply annotated.
    :param attribute: the attribute name. If None, the function name will be used
    :param is_getter: True for a getter override, False for a setter override.
    :return:
    """

    # Simply annotate the fact that this is a function
    attr_name = attribute or func.__name__
    if is_getter:
        if hasattr(func, __GETTER_OVERRIDE_ANNOTATION):
            raise DuplicateOverrideError('Getter is overridden twice for attribute name : ' + attr_name)
        else:
            # func.__getter_override__ = attr_name
            setattr(func, __GETTER_OVERRIDE_ANNOTATION, attr_name)
    else:
        if hasattr(func, __SETTER_OVERRIDE_ANNOTATION):
            raise DuplicateOverrideError('Setter is overridden twice for attribute name : ' + attr_name)
        else:
            # func.__setter_override__ = attr_name
            setattr(func, __SETTER_OVERRIDE_ANNOTATION, attr_name)

    return func
