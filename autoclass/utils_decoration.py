from inspect import isclass
from typing import Callable


def _call_decorator_with_or_without_args(decorator_function_impl: Callable, objectIsFunction: bool, *args, **kwargs):
    """
    Utility function for all decorators: handles the fact that 
    * if the decorator has been called with arguments, then we have to return a decorator factory
    * if the decorator has been called without arguments, then we have to directly return the decoration result

    :param decorator_function_impl:
    :param args:
    :param kwargs:
    :return:
    """

    if len(args) > 0 and ((objectIsFunction and callable(args[0])) or (not objectIsFunction and isclass(args[0]))):
        # we have been called without argument. In that case 'args[0]' contains the object_to_decorate
        return decorator_function_impl(*args, **kwargs)
    else:
        # called with arguments : lets return a factory function
        def f(object_to_decorate):
            return decorator_function_impl(object_to_decorate, *args, **kwargs)
        return f


def _create_function_decorator__robust_to_args(decorator_impl: Callable, *args, **kwargs):
    """
    Utility method to implement a decorator for functions based on the provided implementation and arguments
    
    :param decorator_impl: a function taking as first argument a function
    :param args: 
    :param kwargs: 
    :return: 
    """
    return _call_decorator_with_or_without_args(decorator_impl, True, *args, **kwargs)


def _create_class_decorator__robust_to_args(decorator_impl: Callable, *args, **kwargs):
    """
    Utility method to create a decorator for classes based on the provided implementation and arguments
    
    :param decorator_impl: 
    :param args: 
    :param kwargs: 
    :return: 
    """
    return _call_decorator_with_or_without_args(decorator_impl, False, *args, **kwargs)


def apply_on_func_args(func, cur_args, cur_kwargs,
                       signature_attrs, signature_defaults, signature_varargs, signature_varkw,
                       func_to_apply, func_to_apply_paramers_dict):
    """
    Applies func_to_apply on each argument of func according to what's received in current call (cur_args, cur_kwargs).
    For each argument of func named 'att' in its signature, the following method is called:

    `func_to_apply(cur_att_value, func_to_apply_paramers_dict[att], func, att_name)`

    :param func:
    :param cur_args:
    :param cur_kwargs:
    :param signature_attrs:
    :param signature_defaults:
    :param signature_varargs:
    :param signature_varkw:
    :param func_to_apply:
    :param func_to_apply_paramers_dict:
    :return:
    """
    # handle default values and kw arguments
    for attr, val in zip(reversed(signature_attrs), reversed(signature_defaults or [])):
        if attr in func_to_apply_paramers_dict.keys():
            # set default or provided value
            if attr in cur_kwargs.keys():
                # provided: we never seem to enter here, why ? maybe depends on the version of python
                func_to_apply(cur_kwargs[attr], func_to_apply_paramers_dict[attr], func, attr)
            else:
                # default
                func_to_apply(val, func_to_apply_paramers_dict[attr], func, attr)

    # handle positional arguments
    for attr, val in zip(signature_attrs, cur_args):
        if attr in func_to_apply_paramers_dict.keys():
            func_to_apply(val, func_to_apply_paramers_dict[attr], func, attr)

    # handle varargs : since we dont know their name, they can only be validated as a whole
    if signature_varargs:
        remaining_args = cur_args[len(signature_attrs):]
        if signature_varargs in func_to_apply_paramers_dict.keys():
            func_to_apply(remaining_args, func_to_apply_paramers_dict[signature_varargs], func, signature_varargs)

    # handle varkw : since we know their names, they can be validated either as a whole or independently
    if signature_varkw:
        # either the item is the whole dictionary (if func signature is generic such as in **kwargs)
        if signature_varkw in func_to_apply_paramers_dict.keys():
            # value = the cur_kwargs as a whole
            func_to_apply(cur_kwargs, func_to_apply_paramers_dict[signature_varkw], func, signature_varkw)
        else:
            # or each item is handled independently (if func signature contains the kw args names such as a, b)
            for attr, val in cur_kwargs.items():
                if attr in func_to_apply_paramers_dict.keys():
                    func_to_apply(val, func_to_apply_paramers_dict[attr], func, attr)
