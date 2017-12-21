from inspect import getfullargspec
from typing import Tuple, Callable, Union

from autoclass.utils_decoration import _create_function_decorator__robust_to_args
from autoclass.utils_include_exclude import _sieve
from autoclass.var_checker import check_var
from decorator import decorate


def autoargs(include: Union[str, Tuple[str]]=None, exclude: Union[str, Tuple[str]]=None):
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


def autoargs_decorate(func: Callable, include: Union[str, Tuple[str]]=None, exclude: Union[str, Tuple[str]]=None) \
        -> Callable:
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
    check_var(include, var_name='include', var_types=[str, tuple], enforce_not_none=False)
    check_var(exclude, var_name='exclude', var_types=[str, tuple], enforce_not_none=False)

    # (1) then retrieve function signature
    # attrs, varargs, varkw, defaults = getargspec(func)
    signature_attrs, signature_varargs, signature_varkw, signature_defaults, signature_kwonlyargs, \
    signature_kwonlydefaults, signature_annotations = getfullargspec(func)
    # TODO better use signature(func) ? see how it's done in valid8

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
