import sys
from collections import OrderedDict

from makefun import wraps

try:  # python 3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

try:  # python 3.5+
    from typing import Tuple, Callable, Union
except ImportError:
    pass

from decopatch import function_decorator, DECORATED

from autoclass.utils import is_attr_selected, validate_include_exclude


@function_decorator
def autoargs(include=None,  # type: Union[str, Tuple[str]]
             exclude=None,  # type: Union[str, Tuple[str]]
             f=DECORATED
             ):
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
    return autoargs_decorate(f, include=include, exclude=exclude)


def autoargs_decorate(func,          # type: Callable
                      include=None,  # type: Union[str, Tuple[str]]
                      exclude=None   # type: Union[str, Tuple[str]]
                      ):
    # type: (...) -> Callable
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
    validate_include_exclude(include, exclude)

    # (1) then retrieve function signature
    # attrs, varargs, varkw, defaults = getargspec(func)
    func_sig = signature(func)

    # check that include/exclude dont contain names that are incorrect
    if include is not None:
        incorrect = set([include] if isinstance(include, str) else include) - set(func_sig.parameters.keys())
        if len(incorrect) > 0:
            raise ValueError("@autoargs definition exception: include contains '%s' that is/are "
                             "not part of signature for %s" % (incorrect, func))
    if exclude is not None:
        incorrect = set([exclude] if isinstance(exclude, str) else exclude) - set(func_sig.parameters.keys())
        if len(incorrect) > 0:
            raise ValueError("@autoargs definition exception: exclude contains '%s' that is/are "
                             "not part of signature for %s" % (incorrect, func))

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
    @wraps(func)
    def init_wrapper(self, *args, **kwargs):

        # match the received arguments with the signature to know who is who, and add default values to get a full list
        bound_values = func_sig.bind(self, *args, **kwargs)
        apply_defaults(bound_values)

        # Assign to self the ones that needs to
        for att_name, att_value in bound_values.arguments.items():
            if is_attr_selected(att_name, include=include, exclude=exclude):
                # value = a normal value, or cur_kwargs as a whole
                setattr(self, att_name, att_value)

        # finally execute the constructor function
        return func(self, *args, **kwargs)

    # return wrapper
    return init_wrapper


if sys.version_info >= (3, 0):
    def apply_defaults(bound_values):
        bound_values.apply_defaults()
else:
    # TODO when funcsigs implements PR https://github.com/aliles/funcsigs/pull/30 remove this
    def apply_defaults(bound_values):
        arguments = bound_values.arguments

        # Creating a new one and not modifying in-place for thread safety.
        new_arguments = []

        for name, param in bound_values._signature.parameters.items():
            try:
                new_arguments.append((name, arguments[name]))
            except KeyError:
                if param.default is not param._empty:
                    val = param.default
                elif param.kind is param._VAR_POSITIONAL:
                    val = ()
                elif param.kind is param._VAR_KEYWORD:
                    val = {}
                else:
                    # BoundArguments was likely created by bind_partial
                    continue
                new_arguments.append((name, val))

        bound_values.arguments = OrderedDict(new_arguments)
