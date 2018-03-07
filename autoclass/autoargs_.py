from inspect import signature
from collections import Sequence
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
    check_var(include, var_name='include', var_types=[str, Sequence], enforce_not_none=False)
    check_var(exclude, var_name='exclude', var_types=[str, Sequence], enforce_not_none=False)

    # (1) then retrieve function signature
    # attrs, varargs, varkw, defaults = getargspec(func)
    func_sig = signature(func)

    # check that include/exclude dont contain names that are incorrect
    if include is not None:
        incorrect = set(list([include] if isinstance(include, str) else include)) - set(func_sig.parameters.keys())
        if len(incorrect) > 0:
            raise ValueError('@autoargs definition exception: include contains \'' + str(incorrect) + '\' that is/are '
                            'not part of signature for ' + str(func))
    if exclude is not None:
        incorrect = set([exclude] if isinstance(exclude, str) else exclude) - set(func_sig.parameters.keys())
        if len(incorrect) > 0:
            raise ValueError('@autoargs definition exception: exclude contains \'' + str(incorrect) + '\' that is/are '
                             'not part of signature for ' + str(func))

    # TODO this should be in @autoslots decorator at class level, not here.
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
    # -- NOTE: we used @functools.wraps(func), we now use 'decorate' to have a wrapper that has the same signature
    def init_wrapper(init_func, self, *args, **kwargs):

        # match the received arguments with the signature to know who is who, and add default values to get a full list
        bound_values = func_sig.bind(self, *args, **kwargs)
        bound_values.apply_defaults()

        # Assign to self the ones that needs to
        for att_name, att_value in bound_values.arguments.items():
            if _sieve(att_name, include=include, exclude=exclude):
                # value = a normal value, or cur_kwargs as a whole
                setattr(self, att_name, att_value)
            # The behaviour below is removed as it is too complex to explain
            # else:
            #     if func_sig.parameters[att_name].kind == Parameter.VAR_KEYWORD:
            #         # if the attribute is variable-length keyword argument we can try to find a matching key inside it
            #         # each item is handled independently (if func signature contains the kw args names such as a, b)
            #         for name, value in att_value.items():
            #             if _sieve(name, include=include, exclude=exclude):
            #                 setattr(self, name, value)

        # finally execute the constructor function
        return init_func(self, *args, **kwargs)

    # return wrapper
    return decorate(func, init_wrapper)
