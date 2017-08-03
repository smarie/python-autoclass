from inspect import getfullargspec, Parameter, ismethod, getmro, isfunction, getmodule, signature, getmembers, isclass
from typing import Tuple, Type, Any, Callable, Union

from decorator import decorate

from autoclass.utils import _create_function_decorator__robust_to_args
from autoclass.var_checker import check_var


def autoargs(include:Union[str, Tuple[str]]=None,exclude:Union[str, Tuple[str]]=None):
    """
    Defines a decorator with parameters, to automatically assign the inputs of a function to self PRIOR to executing 
    the function. In other words:
    
    ```
    @autoargs
    def myfunc(a):
        print('hello')
    ```
    
    will create the equivalent of
    
    ```
    def myfunc(a):
        self.a = a
        print('hello')
    ```
    
    Initial code from http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049

    :param include: a tuple of attribute names to include in the auto-assignment. If None, all arguments will be
    included by default
    :param exclude: a tuple of attribute names to exclude from the auto-assignment. In such case, include should be None
    :return:
    """
    return _create_function_decorator__robust_to_args(autoargs_decorate, include, exclude=exclude)


def autoargs_decorate(func: Callable, include:Union[str, Tuple[str]]=None, exclude:Union[str, Tuple[str]]=None) -> Callable:
    """
    Defines a decorator with parameters, to automatically assign the inputs of a function to self PRIOR to executing 
    the function. This is the inline way to apply the decorator 
    
    ```
    myfunc2 = autoargs_decorate(myfunc)
    ```
    
    
    See autoargs for details.

    :param func: the function to wrap
    :param include: a tuple of attribute names to include in the auto-assignment. If None, all arguments will be
    included by default
    :param exclude: a tuple of attribute names to exclude from the auto-assignment. In such case, include should be None
    :return:
    """

    # (0) first check parameters
    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

    # (1) then retrieve function signature
    # attrs, varargs, varkw, defaults = getargspec(func)
    signature_attrs, signature_varargs, signature_varkw, signature_defaults, signature_kwonlyargs, \
    signature_kwonlydefaults, signature_annotations = getfullargspec(func)
    # TODO better use signature(func) ?

    # check that include/exclude dont contain names that are incorrect
    if include is not None:
        incorrect = set(list([include] if isinstance(include, str) else include)) - set(signature_attrs)
        if len(incorrect) > 0:
            raise ValueError('@autoargs definition exception: include contains \'' + str(incorrect) + '\' that is/are '
                            'not part of signature for ' + str(func))
    if exclude is not None:
        incorrect = set([exclude] if isinstance(exclude, str) else exclude) - set(signature_attrs)
        if len(incorrect) > 0:
            raise ValueError('@autoargs definition exception: exclude contains \'' + str(incorrect) + '\' that is/are '
                             'not part of signature for ' + str(func))

    # (2) Optionally lock the class only for the provided fields
    # Does not work for the moment. Besides locking fields seems to have issues with pickle serialization
    # so we'd rather not propose this option.
    #
    # See 'attrs' project for this kind of advanced features https://github.com/python-attrs/attrs
    #
    # if lock_class_fields:
    #     if signature_varkw:
    #         raise Exception('cant lock field names with variable kwargs')
    #     else:
    #         object_type = get_class_that_defined_method(func)
    #         if include:
    #             fields = include
    #         else:
    #             fields = signature_attrs[1:]
    #             if signature_varargs:
    #                 fields.append(signature_varargs)
    #             if exclude:
    #                 for a in exclude:
    #                     fields.remove(a)
    #
    #         # right now, doesnot work
    #         _lock_fieldnames_class(object_type, field_names=tuple(fields))

    # (3) Finally, create a wrapper around the function so that all attributes included/not excluded are
    # set to self BEFORE executing the function.

    # -- old:
    # @functools.wraps(func) -> to make the wrapper function look like the wrapped function
    # def wrapper(self, *args, **kwargs):

    # -- new:
    # we now use 'decorate' at the end of this code to have a wrapper that has the same signature, see below
    def wrapper(func, self, *args, **kwargs):

        # handle default values and kw arguments
        for attr, val in zip(reversed(signature_attrs), reversed(signature_defaults or [])):
            if sieve(attr):
                # set default or provided value
                if attr in kwargs.keys():
                    # provided: we never seem to enter here, why ? maybe depends on the version of python
                    setattr(self, attr, kwargs[attr])
                else:
                    # default
                    setattr(self, attr, val)

        # handle positional arguments except 'self' (the first)
        signature_positional_attrs = signature_attrs[1:len(args)+1]
        for attr,val in zip(signature_positional_attrs,args):
            if sieve(attr):
                setattr(self, attr, val)

        # handle varargs : since we dont know their name, store them in a global field named after the vararg name
        if signature_varargs:
            remaining_args=args[len(signature_positional_attrs):]
            if sieve(signature_varargs):
                setattr(self, signature_varargs, remaining_args)

        # handle varkw : since we know their names, store them directly in independent fields
        if signature_varkw:
            for attr, val in kwargs.items():
                if sieve(signature_varkw) or sieve(attr):
                    setattr(self, attr, val)

        # finally execute the function
        return func(self, *args, **kwargs)

    def sieve(attr):
        """
        Locally-defined function that we use in the wrapper to check if an attribute shall be included in the processing
        :param attr: 
        :return: 
        """
        return _sieve(attr, include=include, exclude=exclude)

    # return wrapper
    return decorate(func, wrapper)


def _sieve(attr, include:Union[str, Tuple[str]]=None, exclude:Union[str, Tuple[str]]=None):
    """decide whether an action has to be performed on the attribute or not, based on its name"""

    if include is not None and exclude is not None:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

    check_var(include, var_name='include', var_types=[str, tuple], enforce_not_none=False)
    check_var(exclude, var_name='exclude', var_types=[str, tuple], enforce_not_none=False)

    if attr is 'self':
        return False
    if exclude and attr in exclude:
        return False
    if not include or attr in include:
        return True
    else:
        return False


def get_missing_mandatory_parameters(param_names:set, object_type:Type[Any]):
    """
    Utility method to get the set of missing mandatory parameters, from a set of parameters and an object type

    :param param_names:
    :param object_type:
    :return:
    """
    return (set(param_names) - set(get_mandatory_param_names(object_type)))


def get_all_param_names(item_type: Type[Any]):
    """
    Utility function to extract the constructor and find all its parameter names

    :param item_type:
    :return:
    """
    # extract unique constructor signature
    constructor = get_constructor(item_type)
    s = signature(constructor)

    # return all parameters
    return [attribute_name for attribute_name, param in s.parameters.items()]


def get_mandatory_param_names(item_type: Type[Any]):
    """
    Utility function to extract the constructor and find its mandatory parameter names

    :param item_type:
    :return:
    """
    # extract unique constructor signature
    constructor = get_constructor(item_type)
    s = signature(constructor)

    # return mandatory parameters
    return [attribute_name for attribute_name, param in s.parameters.items() if param.default is Parameter.empty]


def get_constructor(item_type):
    """
    Utility method to return the unique constructor of a class

    :param item_type:
    :return:
    """
    constructors = [f[1] for f in getmembers(item_type) if f[0] is '__init__']
    if len(constructors) > 1:
        raise Exception('Several constructors were found for class ' + str(item_type))
    if len(constructors) == 0:
        raise Exception('No constructor was found for class ' + str(item_type))

    constructor = constructors[0]

    # if constructor is a wrapped function, access to the underlying function

    return constructor


# def get_class_that_defined_method(meth):
#     """
#     Utility method, from http://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3/25959545#25959545
#
#     :param meth:
#     :return:
#     """
#
#     if ismethod(meth):
#         # this won't happen in python 3.5 : https://bugs.python.org/issue27901
#         for cls in getmro(meth.__self__.__class__):
#            if cls.__dict__.get(meth.__name__) is meth:
#                 return cls
#         meth = meth.__func__ # fallback to __qualname__ parsing
#     if isfunction(meth):
#         cls = getattr(getmodule(meth),
#                       meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
#         if isinstance(cls, type):
#             return cls
#     return None # not required since None would have been implicitly returned anyway


# def _lock_fieldnames_class(object_type: Type[Any], field_names:Tuple[str]=None):
#     """
#     Utility method to lock the possible fields of a class to the arguments declared in the constructor
#
#     :param object_type:
#     :param field_names: optional explicit list of field names
#     :return:
#     """
#
#     if not field_names:
#
#         # 1. Find the constructor
#         # extract unique constructor __init__
#         constructor = get_constructor(object_type)
#
#         # extract the __init__ signature
#         s = signature(constructor)
#
#         field_names = s.parameters.keys()
#
#     # now lock the names of fields : no additional field can be created on this object anymore
#     object_type.__slots__ = field_names
