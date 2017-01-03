import functools
from inspect import getfullargspec, Parameter, ismethod, getmro, isfunction, getmodule, signature, getmembers, isclass
from typing import Tuple, Type, Any, Callable


def _call_decorator_with_or_without_args(manual_decorator_function: Callable, objectIsFunction: bool,
                                         first_arg, *remaining_args, **kwargs):
    """
    Utility function for all decorators: checks if the first argument is

    :param manual_decorator_function:
    :param first_arg:
    :param remaining_args:
    :param kwargs:
    :return:
    """
    if (objectIsFunction and callable(first_arg)) or (not objectIsFunction and isclass(first_arg)):
        # we have been called without argument. In that case 'first_arg' contains 'func' or 'cls'
        return manual_decorator_function(first_arg, *remaining_args, **kwargs)
    else:
        # called with arguments : return a function that can wrap a class
        def f(func):
            return manual_decorator_function(func, first_arg, *remaining_args, **kwargs)
        return f


def _call_func_decorator_with_or_without_args(manual_decorator_function: Callable, first_arg, *remaining_args, **kwargs):
    return _call_decorator_with_or_without_args(manual_decorator_function, True, first_arg, *remaining_args, **kwargs)


def _call_class_decorator_with_or_without_args(manual_decorator_function: Callable, first_arg, *remaining_args, **kwargs):
    return _call_decorator_with_or_without_args(manual_decorator_function, False, first_arg, *remaining_args, **kwargs)


def autoargs(include:Tuple[str]=None,exclude:Tuple[str]=None):
    """
    Defines a decorator with parameters, to automatically affect the contents of a function to self.
    Initial code from http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049

    :param include: a tuple of attribute names to include in the auto-assignment. If None, all arguments will be
    included by default
    :param exclude: a tuple of attribute names to exclude from the auto-assignment. In such case, include should be None
    :return:
    """
    return _call_func_decorator_with_or_without_args(autoargs_decorate, include, exclude=exclude)


def autoargs_decorate(func, include:Tuple[str]=None, exclude:Tuple[str]=None):
    """
    Creates a function wrapper to automatically affect the contents of a function to self.

    :param func: the function to wrap
    :param include: a tuple of attribute names to include in the auto-assignment. If None, all arguments will be
    included by default
    :param exclude: a tuple of attribute names to exclude from the auto-assignment. In such case, include should be None
    :return:
    """

    if include and exclude:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

    #if not callable(func):
        # that's because we are trying to call the constructor dynamically
    #    func = include[0]
    #attrs, varargs, varkw, defaults = getargspec(func)

    signature_attrs, signature_varargs, signature_varkw, signature_defaults, signature_kwonlyargs, \
    signature_kwonlydefaults, signature_annotations = getfullargspec(func)
    # TODO better use signature(func) ?

    # Does not work for the moment. Besides locking fields seems to have issues with pickle serialization
    # so we'd rather not propose this option
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

    def sieve(attr):
        return _sieve(attr, include=include, exclude=exclude)

    @functools.wraps(func)  # to make the wrapper function look like the wrapped function
    def wrapper(self, *args, **kwargs):

        # handle default values and kw arguments
        for attr,val in zip(reversed(signature_attrs),reversed(signature_defaults or [])):
            if sieve(attr):
                # set default or provided value
                setattr(self, attr, kwargs[attr] if attr in kwargs.keys() else val)

        # handle positional arguments
        signature_positional_attrs = signature_attrs[1:len(args)+1]
        for attr,val in zip(signature_positional_attrs,args):
            if sieve(attr):
                setattr(self, attr, val)

        # handle varargs : since we dont know their name, store them in a field named after the vararg name
        if signature_varargs:
            remaining_args=args[len(signature_positional_attrs):]
            if sieve(signature_varargs):
                setattr(self, signature_varargs, remaining_args)

        # handle varkw : since we know their names, store them directly
        if signature_varkw:
            #for attr,val in signature_varkw.iteritems():
            #    if sieve(attr):
            #        setattr(self,attr,val)
            for attr, val in kwargs.items():
                if sieve(signature_varkw) or sieve(attr):
                    setattr(self, attr, val)

        # finally execute
        return func(self,*args,**kwargs)

    return wrapper


def _sieve(attr, include:Tuple[str]=None, exclude:Tuple[str]=None):
    """decide whether an action has to be performed on the attribute or not, based on its name"""

    if include and exclude:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

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


def get_class_that_defined_method(meth):
    """
    Utility method, from http://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3/25959545#25959545

    :param meth:
    :return:
    """

    if ismethod(meth):
        # this won't happen in python 3.5 : https://bugs.python.org/issue27901
        for cls in getmro(meth.__self__.__class__):
           if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__ # fallback to __qualname__ parsing
    if isfunction(meth):
        cls = getattr(getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return None # not required since None would have been implicitly returned anyway


def _lock_fieldnames_class(object_type: Type[Any], field_names:Tuple[str]=None):
    """
    Utility method to lock the possible fields of a class to the arguments declared in the constructor

    :param object_type:
    :param field_names: optional explicit list of field names
    :return:
    """

    if not field_names:

        # 1. Find the constructor
        # extract unique constructor __init__
        constructor = get_constructor(object_type)

        # extract the __init__ signature
        s = signature(constructor)

        field_names = s.parameters.keys()

    # now lock the names of fields : no additional field can be created on this object anymore
    object_type.__slots__ = field_names
