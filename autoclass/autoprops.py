from inspect import getmembers, signature
from typing import Type, Any, Tuple, Callable, Union, Optional
from warnings import warn

from decorator import decorate

from autoclass.validate import validate_decorate
from autoclass.autoargs import get_constructor, _sieve
from autoclass.utils import _create_function_decorator__robust_to_args, _create_class_decorator__robust_to_args

__GETTER_OVERRIDE_ANNOTATION = '__getter_override__'
__SETTER_OVERRIDE_ANNOTATION = '__setter_override__'


class IllegalGetterSignatureException(Exception):
    """ This is raised whenever an overriden getter has an illegal signature"""


class IllegalSetterSignatureException(Exception):
    """ This is raised whenever an overriden setter has an illegal signature"""


class DuplicateOverrideError(Exception):
    """ This is raised whenever a getter or setter is overriden twice for the same attribute"""


def autoprops(include:Union[str, Tuple[str]]=None, exclude:Union[str, Tuple[str]]=None):
    """
    A decorator to automatically generate all properties getters and setters from the class constructor.
    * if a @contract annotation exist on the __init__ method, mentioning a contract for a given parameter, the
    parameter contract will be added on the generated setter method
    * The user may override the generated getter and/or setter by creating them explicitly in the class and annotating
    them with @getter_override or @setter_override. Note that the contract will still be dynamically added on the
    setter, even if the setter already has one (in such case a `UserWarning` will be issued)

    :param include: a named tuple of explicit attributes to include (None means all)
    :param exclude: a named tuple of explicit attributes to exclude. In such case, include should be None.
    :return:
    """
    return _create_class_decorator__robust_to_args(autoprops_decorate, include, exclude=exclude)


def autoprops_decorate(cls: Type[Any], include: Union[str, Tuple[str]] = None,
                       exclude: Union[str, Tuple[str]] = None) -> Type[Any]:
    """
    To automatically generate all properties getters and setters from the class constructor manually, without using
    @autoprops decorator.
    * if a @contract annotation exist on the __init__ method, mentioning a contract for a given parameter, the
    parameter contract will be added on the generated setter method
    * The user may override the generated getter and/or setter by creating them explicitly in the class and annotating
    them with @getter_override or @setter_override. Note that the contract will still be dynamically added on the
    setter, even if the setter already has one (in such case a `UserWarning` will be issued)

    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a named tuple of explicit attributes to include (None means all)
    :param exclude: a named tuple of explicit attributes to exclude. In such case, include should be None.
    :return:
    """

    # perform the class mod
    _execute_autoprops_on_class(cls, include=include, exclude=exclude)

    # TODO better create a wrapper than modify the class?
    # class Autoprops_Wrapper(object):
    #     def __init__(self, *args, **kwargs):
    #         self.wrapped = cls(*args, **kwargs)
    #
    # return Autoprops_Wrapper

    return cls


def _execute_autoprops_on_class(object_type: Type[Any], include:Union[str, Tuple[str]]=None,
                                exclude:Union[str, Tuple[str]]=None):
    """
    This method will automatically add one getter and one setter for each constructor argument, except for those
    overriden using autoprops_override_decorate(), @getter_override or @setter_override.
    It will add a @contract on top of all setters (generated or overriden, if they don't already have one)

    :param object_type: the class on which to execute.
    :param include: a named tuple of explicit attributes to include (None means all)
    :param exclude: a named tuple of explicit attributes to exclude. In such case, include should be None.
    :return:
    """

    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

    # 1. Find the __init__ constructor signature and possible pycontracts @contract
    constructor = get_constructor(object_type)
    s = signature(constructor)

    # option a) pycontracts
    contracts_dict = constructor.__contracts__ if hasattr(constructor, '__contracts__') else {}
    # option b) validate
    validators_dict = constructor.__validators__ if hasattr(constructor, '__validators__') else {}

    # 2. For each attribute that is not 'self' and is included and not excluded, add the property
    added = []
    for attr_name in s.parameters.keys():
        if _sieve(attr_name, include=include, exclude=exclude):
            added += attr_name
            attr_type = s.parameters[attr_name]._annotation
            _add_property(object_type, attr_name, attr_type,
                          pycontract=(contracts_dict[attr_name] if attr_name in contracts_dict.keys() else None),
                          validators=(validators_dict[attr_name] if attr_name in validators_dict.keys() else None))

    # 3. Finally check that there is no overriden setter or getter that does not correspond to an attribute
    extra_overrides = getmembers(object_type, predicate=(lambda fun: callable(fun) and
                                                                     (hasattr(fun, __GETTER_OVERRIDE_ANNOTATION)
                                                                      and getattr(fun, __GETTER_OVERRIDE_ANNOTATION) not in added)
                                                                      or
                                                                     (hasattr(fun, __SETTER_OVERRIDE_ANNOTATION))
                                                                      and getattr(fun, __SETTER_OVERRIDE_ANNOTATION) not in added)
                                 )
    if len(extra_overrides) > 0:
        raise AttributeError('Attribute named \'' + extra_overrides[0][0] + '\' was not found in constructor signature. Therefore its '
                                                    'getter/setter can not be overriden by function ' + extra_overrides[0][1].__qualname__)


def _add_property(object_type: Type[Any], property_name: str, property_type: type, pycontract: Any = None,
                  validators: Any = None):
    """
    A method to dynamically add a property to a class with the optional given pycontract or validators.
    If the property getter and/or setter have been overriden, it is taken into account too.

    :param object_type: the class on which to execute.
    :param property_name:
    :param property_type:
    :param pycontract:
    :param validators:
    :return:
    """

    # 1. create the private field name , e.g. '_foobar'
    private_property_name = '_' + property_name

    # 2. property getter (@property)
    getter_fun = _get_getter_fun(object_type, property_name, property_type, private_property_name)

    # 3. property setter (@property_name.setter)
    setter_fun, var_name = _get_setter_fun(object_type, property_name, property_type, private_property_name)

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
    #__annotations__
    #__doc__
    #__dict__

    # 6. Finally add the property to the class
    # WARNING : property_obj.setter(f) does absolutely nothing :) > we have to assign the result
    # setattr(object_type, property_name, property_obj.setter(f))
    setattr(object_type, property_name, property(fget=getter_fun, fset=setter_fun_with_possible_contract))

    return


def _get_getter_fun(object_type: Type, property_name: str, property_type: Optional[Type], private_property_name: str):
    """
    Utility method to find the overriden getter function for a given property, or generate a new one

    :param object_type:
    :param property_name:
    :param private_property_name:
    :return:
    """

    # -- check overriden getter for this property name
    overriden_getters = getmembers(object_type, predicate=(lambda fun: callable(fun)
                                                                       and hasattr(fun, __GETTER_OVERRIDE_ANNOTATION)
                                                                       and getattr(fun,
                                                                                   __GETTER_OVERRIDE_ANNOTATION) is property_name))
    if len(overriden_getters) > 0:
        if len(overriden_getters) > 1:
            raise DuplicateOverrideError('Getter is overriden more than once for attribute name : ' + property_name)

        # --use the overriden getter
        getter_fun = overriden_getters[0][1]

        # --check its signature
        s = signature(getter_fun)
        if not ('self' in s.parameters.keys() and len(s.parameters.keys()) == 1):
            raise IllegalGetterSignatureException('Overriden getter must only have a self parameter, found ' +
                                                  str(len(s.parameters.items()) - 1) + ' for function ' + str(
                getter_fun.__qualname__))

        # --use the overriden getter
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
        getter_fun.__annotations__['return'] = property_type  # declare that we return a <type>

    return getter_fun


def _get_setter_fun(object_type: Type, property_name: str, property_type: Optional[Type], private_property_name: str):
    """
    Utility method to find the overriden setter function for a given property, or generate a new one

    :param object_type:
    :param property_name:
    :param property_type:
    :param private_property_name:
    :return:
    """

    overriden_setters = getmembers(object_type, predicate=(lambda fun: callable(fun)
                                                                       and hasattr(fun, __SETTER_OVERRIDE_ANNOTATION)
                                                                       and getattr(fun,
                                                                                   __SETTER_OVERRIDE_ANNOTATION) is property_name))
    if len(overriden_setters) > 0:
        if len(overriden_setters) > 1:
            raise DuplicateOverrideError('Setter is overriden more than once for attribute name : ' + property_name)

        # --use the overriden setter
        setter_fun = overriden_setters[0][1]
        # --find the parameter name and check the signature
        s = signature(setter_fun)
        p = [attribute_name for attribute_name, param in s.parameters.items() if attribute_name is not 'self']
        if len(p) != 1:
            raise IllegalSetterSignatureException('Overriden setter must have only 1 non-self argument, found ' +
                                                  str(len(s.parameters.items()) - 1) + ' for function ' + str(
                setter_fun.__qualname__))
        var_name = p[0]
    else:
        # --create the setter :
        # @foobar.setter
        # def foobar(self, foobar):
        #     self.__foobar = foobar
        def generated_setter_fun(self, val):
            return setattr(self, private_property_name, val)
        generated_setter_fun.__annotations__['val'] = property_type  # declare that we need a <type> as input

        # other options (more complex) to fiddle with the signature :
        # http://stackoverflow.com/questions/18625510/how-can-i-programmatically-change-the-argspec-of-a-function-not-in-a-python-de
        # http://stackoverflow.com/questions/10303248/true-dynamic-and-anonymous-functions-possible-in-python

        # remember the parameter name
        var_name = 'val'
        setter_fun = generated_setter_fun

    return setter_fun, var_name


def _add_contract_to_setter(setter_fun, var_name, property_contract, property_name):

    # 0. check that we can import contracts
    try:
        # noinspection PyUnresolvedReferences
        from contracts import ContractNotRespected, contract
    except ImportError as e:
        raise Exception(
            'Use of _add_contract_to_setter requires that PyContract library is installed. Check that you can \'import contracts\'')

    # -- check if a contract already exists on the function
    if hasattr(setter_fun, '__contracts__'):
        msg = 'Overriden setter for attribute ' + property_name + ' implemented by function ' \
              + str(setter_fun.__qualname__) + ' has a contract while there is a contract already defined ' \
                                               'for this property in the __init__ constructor. This will lead to double-contract in the final ' \
                                               'setter, please remove the one on the overriden setter.'
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
        except ContractNotRespected as e:
            e.error = e.error.replace('\'val\'', '\'' + property_name + '\'')
            raise e

    # f = _contracts_parser_interceptor(f)
    setter_fun_with_possible_contract = decorate(setter_fun_with_possible_contract, _contracts_parser_interceptor)
    return setter_fun_with_possible_contract


def _add_validators_to_setter(setter_fun, var_name, validators, property_name):

    # 0. check that we can import validate
    # note: this is useless now but maybe one day validate will be another project ?
    try:
        # noinspection PyUnresolvedReferences
        from autoclass import validate
    except ImportError as e:
        raise Exception(
            'Use of _add_contract_to_setter requires that validate library is installed. Check that you can '
            '\'import validate\'')

    # -- check if a contract already exists on the function
    if hasattr(setter_fun, '__validators__'):
        msg = 'Overriden setter for attribute ' + property_name + ' implemented by function ' \
              + str(setter_fun.__qualname__) + ' has validators while there are validators already defined ' \
              'for this property in the __init__ constructor. This will lead to double-contract in the final ' \
              'setter, please remove the one on the overriden setter.'
        warn(msg)

    # -- add the generated contract
    setter_fun_with_possible_contract = validate_decorate(setter_fun, **{var_name: validators})

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
    return setter_fun_with_possible_contract


def getter_override(attribute:str = None):
    """
    A decorator to indicate an overriden getter for a given attribute. If the attribute name is None, the function name
    will be used as the attribute name.

    :param attribute: the attribute name for which the decorated function is an overriden getter
    :return:
    """
    return _create_function_decorator__robust_to_args(autoprops_override_decorate, attribute, is_getter=True)


def setter_override(attribute:str = None):
    """
    A decorator to indicate an overriden setter for a given attribute. If the attribute name is None, the function name
     will be used as the attribute name. The @contract will still be dynamically added.

    :param attribute: the attribute name for which the decorated function is an overriden setter
    :return:
    """
    return _create_function_decorator__robust_to_args(autoprops_override_decorate, attribute, is_getter=False)


def autoprops_override_decorate(func: Callable, attribute:str = None, is_getter:bool = True) -> Callable:
    """
    Used to decorate a function as an overriden getter or setter, without using the @getter_override or
    @setter_override annotations. If the overriden setter has no @contract, the contract will still be
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
            raise DuplicateOverrideError('Getter is overriden twice for attribute name : ' + attr_name)
        else:
            func.__getter_override__ = attr_name
    else:
        if hasattr(func, __SETTER_OVERRIDE_ANNOTATION):
            raise DuplicateOverrideError('Setter is overriden twice for attribute name : ' + attr_name)
        else:
            func.__setter_override__ = attr_name

    return func