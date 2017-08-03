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
