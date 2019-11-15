import sys
from collections import OrderedDict

from makefun import wraps

try:  # python 3+
    from inspect import signature, Signature
except ImportError:
    from funcsigs import signature, Signature

try:  # python 3.5+
    from typing import Tuple, Callable, Union, Iterable
except ImportError:
    pass

from decopatch import function_decorator, DECORATED

from autoclass.utils import read_fields_from_init


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
    # retrieve and filter the names
    selected_names, func_sig = read_fields_from_init(func, include=include, exclude=exclude, caller="@autoargs")

    # finally create the new function (a wrapper)
    return _autoargs_decorate(func, func_sig, selected_names)


def _autoargs_decorate(func,       # type: Callable
                       func_sig,   # type: Signature
                       att_names   # type: Iterable[str]
                       ):
    """
    Creates a wrapper around the function `func` so that all attributes in `att_names` are set to `self`
    BEFORE executing the function. The original function signature may be needed in some edge cases.

    :param func:
    :param func_sig:
    :param att_names:
    :return:
    """
    @wraps(func)
    def init_wrapper(self, *args, **kwargs):

        # bind arguments with signature: not needed anymore in nominal case since we use `makefun.wraps`
        # bound_values = func_sig.bind(self, *args, **kwargs)
        # apply_defaults(bound_values)

        # Assign to self each of the attributes
        need_introspect = False
        i = -1
        for i, att_name in enumerate(att_names):
            try:
                setattr(self, att_name, kwargs[att_name])
            except KeyError:
                # this may happen when the att names are BEFORE a var positional
                # Switch to introspection mode
                need_introspect = True
                break
        if need_introspect and i >= 0:
            bound_values = func_sig.bind(self, *args, **kwargs)
            apply_defaults(bound_values)
            # noinspection PyUnboundLocalVariable
            arg_dict = bound_values.arguments
            for att_name in att_names[i:]:
                setattr(self, att_name, arg_dict[att_name])

        # finally execute the constructor function
        return func(self, *args, **kwargs)

    # return wrapper
    return init_wrapper


if sys.version_info >= (3, 0):
    # the function exists, use it
    def apply_defaults(bound_values):
        bound_values.apply_defaults()
else:
    # the `inspect` backport (`funcsigs`) does not implement the function
    # TODO when funcsigs implements PR https://github.com/aliles/funcsigs/pull/30 remove this
    def apply_defaults(bound_values):
        arguments = bound_values.arguments

        # Creating a new one and not modifying in-place for thread safety.
        new_arguments = []

        for name, param in bound_values._signature.parameters.items():
            try:
                new_arguments.append((name, arguments[name]))
            except KeyError:
                if param.default is not param.empty:
                    val = param.default
                elif param.kind is param.VAR_POSITIONAL:
                    val = ()
                elif param.kind is param.VAR_KEYWORD:
                    val = {}
                else:
                    # BoundArguments was likely created by bind_partial
                    continue
                new_arguments.append((name, val))

        bound_values.arguments = OrderedDict(new_arguments)
