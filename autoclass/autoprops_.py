from copy import copy
from inspect import getmembers
from warnings import warn

from makefun import wraps, with_signature

try:
    from inspect import signature, Parameter, Signature
except ImportError:
    from funcsigs import signature, Parameter, Signature

try:
    from typing import Any, Tuple, Callable, Union, TypeVar, Iterable, Dict
    try:
        from typing import Type
    except ImportError:
        pass
    T = TypeVar('T')
except ImportError:
    pass

from decopatch import DECORATED, function_decorator, class_decorator

from autoclass.utils import check_known_decorators, AUTO, read_fields_from_init, DuplicateOverrideError

__GETTER_OVERRIDE_ANNOTATION = '__getter_override__'
__SETTER_OVERRIDE_ANNOTATION = '__setter_override__'


class IllegalGetterSignatureException(Exception):
    """ This is raised whenever an overridden getter has an illegal signature"""


class IllegalSetterSignatureException(Exception):
    """ This is raised whenever an overridden setter has an illegal signature"""


@class_decorator
def autoprops(include=None,  # type: Union[str, Tuple[str]]
              exclude=None,  # type: Union[str, Tuple[str]]
              cls=DECORATED):
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
    return autoprops_decorate(cls, include=include, exclude=exclude)


def autoprops_decorate(cls,           # type: Type[T]
                       include=None,  # type: Union[str, Tuple[str]]
                       exclude=None   # type: Union[str, Tuple[str]]
                       ):
    # type: (...) -> Type[T]
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
    check_known_decorators(cls, '@autoprops')

    # retrieve and filter the names
    init_fun = cls.__init__
    selected_names, init_fun_sig = read_fields_from_init(init_fun, include=include, exclude=exclude,
                                                         caller="@autoprops")

    # perform the class mod
    execute_autoprops_on_class(cls, init_fun=init_fun, init_fun_sig=init_fun_sig, prop_names=selected_names)

    return cls


def execute_autoprops_on_class(cls,            # type: Type[T]
                               init_fun,       # type: Callable
                               init_fun_sig,   # type: Signature
                               prop_names      # type: Iterable[str]
                               ):
    """
    This method will automatically add one getter and one setter for each constructor argument, except for those
    overridden using autoprops_override_decorate(), @getter_override or @setter_override.
    It will add a @contract on top of all setters (generated or overridden, if they don't already have one)

    :param cls: the class on which to execute.
    :param init_fun:
    :param init_fun_sig:
    :param prop_names:
    :return: nothing (`cls` is modified in-place)
    """
    # gather all information required: attribute names, type hints, and potential pycontracts/validators
    att_type_hints_and_defaults = {att_name: (init_fun_sig.parameters[att_name].annotation,
                                              init_fun_sig.parameters[att_name].default)
                                   for att_name in prop_names}
    pycontracts_dict = init_fun.__contracts__ if hasattr(init_fun, '__contracts__') else {}
    valid8ors_dict = init_fun.__validators__ if hasattr(init_fun, '__validators__') else {}

    # 1. Retrieve overridden getters/setters and check that there is no one that does not correspond to an attribute
    overridden_getters = dict()
    overridden_setters = dict()
    for m_name, m in getmembers(cls, predicate=callable):
        # Overridden getter ?
        try:
            overriden_getter_att_name = getattr(m, __GETTER_OVERRIDE_ANNOTATION)
        except AttributeError:
            pass  # no annotation
        else:
            if overriden_getter_att_name not in att_type_hints_and_defaults:
                raise AttributeError("Invalid getter function %r: attribute %r was not found in constructor "
                                     "signature." % (m.__name__, overriden_getter_att_name))
            elif overriden_getter_att_name in overridden_getters:
                raise DuplicateOverrideError("Getter is overridden more than once for attribute name : %s"
                                             % overriden_getter_att_name)
            else:
                overridden_getters[overriden_getter_att_name] = m

        # Overridden setter ?
        try:
            overriden_setter_att_name = getattr(m, __SETTER_OVERRIDE_ANNOTATION)
        except AttributeError:
            pass  # no annotation
        else:
            if overriden_setter_att_name not in att_type_hints_and_defaults:
                raise AttributeError("Invalid setter function %r: attribute %r was not found in constructor "
                                     "signature." % (m.__name__, overriden_setter_att_name))
            elif overriden_setter_att_name in overridden_setters:
                raise DuplicateOverrideError("Setter is overridden more than once for attribute name : %s"
                                             % overriden_setter_att_name)
            else:
                overridden_setters[overriden_setter_att_name] = m

    # 2. For each attribute to consider, create the corresponding property and add it to the class
    for attr_name, (type_hint, default_value) in att_type_hints_and_defaults.items():
        # valid8 validators: create copies, because we will modify them (changing the validated function ref)
        if valid8ors_dict is not None and attr_name in valid8ors_dict:
            validators = [copy(v) for v in valid8ors_dict[attr_name]]
        else:
            validators = None

        # create and add the property
        _add_property(cls, attr_name, type_hint, default_value,
                      overridden_getter=overridden_getters.get(attr_name, None),
                      overridden_setter=overridden_setters.get(attr_name, None),
                      pycontract=pycontracts_dict.get(attr_name, None) if pycontracts_dict is not None else None,
                      validators=validators)


def _add_property(cls,                     # type: Type[T]
                  property_name,           # type: str
                  type_hint,               # type: Any
                  default_value,           # type: Any
                  overridden_getter=None,  # type: Callable
                  overridden_setter=None,  # type: Callable
                  pycontract=None,         # type: Any
                  validators=None          # type: Any
                  ):
    """
    A method to dynamically add a property to a class with the optional given pycontract or validators.
    If the property getter and/or setter have been overridden, it is taken into account too.

    :param cls: the class on which to execute.
    :param property_name:
    :param type_hint:
    :param default_value: this is not really needed by property setter/getter but may be used by type checkers to
        determine from the signature if something is nonable.
    :param pycontract:
    :param validators:
    :return:
    """
    # 1. create the private field name , e.g. '_foobar'
    private_property_name = '_%s' % property_name

    # 2. property getter (@property) and setter (@property_name.setter) - create or use overridden
    getter_fun = _get_getter_fun(cls, property_name, type_hint, private_property_name,
                                 overridden_getter=overridden_getter)
    setter_fun, var_name = _get_setter_fun(cls, property_name, type_hint, default_value, private_property_name,
                                           overridden_setter=overridden_setter)

    # 3. add the contract to the setter, if any
    setter_fun_with_possible_contract = setter_fun
    if pycontract is not None:
        setter_fun_with_possible_contract = _add_contract_to_setter(setter_fun, var_name, pycontract, property_name)
    elif validators is not None:
        setter_fun_with_possible_contract = _add_validators_to_setter(setter_fun, var_name, validators, property_name)

    # 4. change the function name to make it look nice
    # TODO in which case is this really needed ?
    setter_fun_with_possible_contract.__name__ = property_name
    setter_fun_with_possible_contract.__module__ = cls.__module__
    setter_fun_with_possible_contract.__qualname__ = cls.__name__ + '.' + property_name
    # __annotations__
    # __doc__
    # __dict__

    # 5. Create the property with getter and setter
    # WARNING : property_obj.setter(f) does absolutely nothing :) > we have to assign the result
    new_prop = property(fget=getter_fun, fset=setter_fun_with_possible_contract)

    # specific for enforce: here we might wrap the overridden setter on which enforce has already written something.
    # if hasattr(setter_fun_with_possible_contract, '__enforcer__'):
    #     new_prop.__enforcer__ = setter_fun_with_possible_contract.__enforcer__
    # DESIGN DECISION > although this would probably work, it is probably better to 'force' users to always use the
    # @autoprops annotation BEFORE any other annotation. This is now done in autoprops_decorate

    # 6. Finally add the property to the class
    setattr(cls, property_name, new_prop)


def _has_annotation(annotation, value):
    """
    Returns a function that can be used as a predicate in getmembers. Used in _get_getter_fun and _get_setter_fun
    """
    def matches_property_name(fun):
        """ return true if fun is a callable that has the correct annotation with value """
        return callable(fun) and getattr(fun, annotation, None) == value

    return matches_property_name


def _get_getter_fun(cls,                    # type: Type
                    property_name,          # type: str
                    type_hint,              # type: Any
                    private_property_name,  # type: str
                    overridden_getter=AUTO  # type: Callable
                    ):
    """
    Utility method to find the overridden getter function for a given property, or generate a new one

    :param cls:
    :param property_name:
    :param type_hint:
    :param private_property_name:
    :return:
    """
    if overridden_getter is AUTO:
        # If not provided - look for an overridden getter in the class
        overridden_getters = getmembers(cls, predicate=_has_annotation(__GETTER_OVERRIDE_ANNOTATION, property_name))
        if len(overridden_getters) > 1:
            raise DuplicateOverrideError('Getter is overridden more than once for attribute name : %s' % property_name)
        else:
            try:
                overridden_getter = overridden_getters[0][1]
            except IndexError:
                pass

    if overridden_getter is not None:
        # --use the overridden getter found/provided
        getter_fun = overridden_getter
        try:  # python 2 - possibly unbind the function
            getter_fun = getter_fun.im_func
        except AttributeError:
            pass

        # --check its signature
        s = signature(getter_fun)
        if not ('self' in s.parameters.keys() and len(s.parameters.keys()) == 1):
            raise IllegalGetterSignatureException("overridden getter '%s' should have 0 non-self arguments, found %s"
                                                  % (getter_fun.__name__, s))
    else:
        # -- generate the getter :
        def autoprops_generated_getter(self):
            """ generated by `autoprops` - getter for a property """
            return getattr(self, private_property_name)

        # -- use the generated getter
        getter_fun = autoprops_generated_getter

        # -- add type hint to output declaration
        try:
            annotations = getter_fun.__annotations__
        except AttributeError:
            pass  # python 2 - no return type hint
        else:
            annotations['return'] = type_hint

    return getter_fun


def _get_setter_fun(cls,                    # type: Type
                    property_name,          # type: str
                    type_hint,              # type: Any
                    default_value,          # type: Any
                    private_property_name,  # type: str
                    overridden_setter=AUTO  # type: Callable
                    ):
    """
    Utility method to find the overridden setter function for a given property, or generate a new one

    :param cls:
    :param property_name:
    :param type_hint:
    :param default_value:
    :param private_property_name:
    :param overridden_setter: an already found overridden setter to use. If AUTO is provided (default), the class will
        be inspected to find them
    :return:
    """
    if overridden_setter is AUTO:
        # If not provided - look for an overridden setter in the class
        overridden_setters = getmembers(cls, predicate=_has_annotation(__SETTER_OVERRIDE_ANNOTATION, property_name))
        if len(overridden_setters) > 1:
            raise DuplicateOverrideError('Setter is overridden more than once for attribute name : %s' % property_name)
        else:
            try:
                overridden_setter = overridden_setters[0][1]
            except IndexError:
                pass

    if overridden_setter is not None:
        # --use the overridden setter found/provided
        setter_fun = overridden_setter
        try:  # python 2 - possibly unbind the function
            setter_fun = setter_fun.im_func
        except AttributeError:
            pass

        # --find the parameter name and check the signature
        s = signature(setter_fun)
        p = [attribute_name for attribute_name, param in s.parameters.items() if attribute_name is not 'self']
        if len(p) != 1:
            raise IllegalSetterSignatureException('overridden setter %s should have 1 and only 1 non-self argument, '
                                                  'found %s' % (setter_fun.__name__, s))
        actual_arg_name = p[0]
    else:
        # --create the setter: Dynamically compile a wrapper with correct argument name
        sig = Signature(parameters=[Parameter('self', kind=Parameter.POSITIONAL_OR_KEYWORD),
                                    Parameter(property_name, kind=Parameter.POSITIONAL_OR_KEYWORD,
                                              annotation=type_hint, default=default_value)])

        @with_signature(sig)
        def autoprops_generated_setter(self, **kwargs):
            """ generated by `autoprops` - setter for a property """
            setattr(self, private_property_name, kwargs[property_name])

        setter_fun = autoprops_generated_setter
        actual_arg_name = property_name

    return setter_fun, actual_arg_name


def _add_contract_to_setter(setter_fun, var_name, property_contract, property_name):
    """
    Utility function to add a pycontract contract to a setter

    :param setter_fun:
    :param var_name:
    :param property_contract:
    :param property_name:
    :return:
    """

    # 0. check that we can import contracts
    try:
        # noinspection PyUnresolvedReferences
        from contracts import ContractNotRespected, contract
    except ImportError as e:
        raise Exception('Use of _add_contract_to_setter requires that PyContract library is installed. Check that you '
                        'can \'import contracts\'')

    try:
        # python 2
        setter_fun = setter_fun.im_func
    except AttributeError:
        pass

    # -- check if a contract already exists on the function
    if hasattr(setter_fun, '__contracts__'):
        try:
            qname = str(setter_fun.__qualname__)
        except AttributeError:
            qname = setter_fun.__name__
        msg = "overridden setter for attribute %s implemented by function %s has a contract while there is a " \
              "contract already defined for this property in the __init__ constructor. This will lead to " \
              "double-contract in the final setter, please remove the one on the overridden setter." \
              "" % (property_name, qname)
        warn(msg)

    # -- add the generated contract
    setter_fun_with_possible_contract = contract(setter_fun, **{var_name: property_contract})

    # the only thing we can't do is to replace the function's parameter name dynamically in the error messages
    # so we wrap the function again to catch the potential pycontracts error :(
    @wraps(setter_fun_with_possible_contract)
    def _contracts_parser_interceptor(self, *args, **kwargs):
        try:
            return setter_fun_with_possible_contract(self, *args, **kwargs)
        except ContractNotRespected as er:
            er.error = er.error.replace('\'val\'', '\'' + property_name + '\'')
            raise er

    return _contracts_parser_interceptor


def _add_validators_to_setter(setter_fun, var_name, validators, property_name):
    """
    Utility function to add valid8 validators to a setter

    :param setter_fun:
    :param var_name:
    :param validators:
    :param property_name:
    :return:
    """

    # 0. check that we can import valid8
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

    # bind the validators to the setter function so that error message is correct
    for v in validators:
        v.validated_func = setter_fun_with_validation

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


@function_decorator
def getter_override(attribute=None,  # type: str
                    f=DECORATED
                    ):
    """
    A decorator to indicate an overridden getter for a given attribute. If the attribute name is None, the function name
    will be used as the attribute name.

    :param attribute: the attribute name for which the decorated function is an overridden getter
    :return:
    """
    return autoprops_override_decorate(f, attribute=attribute, is_getter=True)


@function_decorator
def setter_override(attribute=None,  # type: str
                    f=DECORATED
                    ):
    """
    A decorator to indicate an overridden setter for a given attribute. If the attribute name is None, the function name
     will be used as the attribute name. The @contract will still be dynamically added.

    :param attribute: the attribute name for which the decorated function is an overridden setter
    :return:
    """
    return autoprops_override_decorate(f, attribute=attribute, is_getter=False)


def autoprops_override_decorate(func,            # type: Callable
                                attribute=None,  # type: str
                                is_getter=True   # type: bool
                                ):
    # type: (...) -> Callable
    """
    Used to decorate a function as an overridden getter or setter, without using the @getter_override or
    @setter_override annotations. If the overridden setter has no @contract, the contract will still be
     dynamically added. Note: this should be executed BEFORE @autoprops or autoprops_decorate().

    :param func: the function on which to execute. Note that it won't be wrapped but simply annotated.
    :param attribute: the attribute name. If None, the function name will be used
    :param is_getter: True for a getter override, False for a setter override.
    :return:
    """
    # default attribute name is getter/setter function name
    if attribute is None:
        attribute = func.__name__

    if is_getter:
        # Simply annotate the fact that this is a getter function for this attribute
        # (a) check that there is no annotation yet
        if hasattr(func, __GETTER_OVERRIDE_ANNOTATION):
            already_name = getattr(func, __GETTER_OVERRIDE_ANNOTATION)
            raise DuplicateOverrideError('Function %s is already an overridden getter for attribute %s'
                                         % (func, already_name))

        # (b) set it
        # func.__getter_override__ = attribute
        setattr(func, __GETTER_OVERRIDE_ANNOTATION, attribute)
    else:
        # Simply annotate the fact that this is a getter function for this attribute
        # (a) check that there is no annotation yet
        if hasattr(func, __SETTER_OVERRIDE_ANNOTATION):
            already_name = getattr(func, __SETTER_OVERRIDE_ANNOTATION)
            raise DuplicateOverrideError('Function %s is already an overridden setter for attribute %s'
                                         % (func, already_name))

        # (b) set it
        # func.__getter_override__ = attribute
        setattr(func, __SETTER_OVERRIDE_ANNOTATION, attribute)

    return func
