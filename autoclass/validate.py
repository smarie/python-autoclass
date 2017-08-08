from inspect import getfullargspec
from numbers import Integral
from typing import Callable, Dict, Any, Set

from decorator import decorate

from autoclass.utils import _create_function_decorator__robust_to_args, apply_on_func_args


def validate(**validators: Dict[str, Callable[[Any], bool]]):
    """
    Defines a decorator with parameters, that will execute the provided input validators PRIOR to executing the 
    function. Specific entry 'returns' may contain validators executed AFTER executing the function.
    
    ```
    def is_even(x):
        return x % 2 == 0
    
    def gt(a):
        def gt(x):
            return x >= a
        return gt
    
    @validate(a=[is_even, gt(1)], b=is_even)
    def myfunc(a, b):
        print('hello')
    ```
    
    will generate the equivalent of :
    
    ```
    def myfunc(a, b):
        gt1 = gt(1)
        if is_even(a) and gt1(a) and is_even(b):
            print('hello')
        else:
            raise ValidationException(...)
    ```
    
    :param validators: 
    :return: 
    """
    return _create_function_decorator__robust_to_args(validate_decorate, **validators)


def validate_decorate(func: Callable, **validators: Dict[str, Callable[[Any], bool]]) -> Callable:
    """
    Defines a decorator with parameters, that will execute the provided input validators PRIOR to executing the 
    function. Specific entry 'returns' may contain validators executed AFTER executing the function.
    
    :param func: 
    :param include: 
    :param exclude: 
    :return: 
    """
    # (1) retrieve function signature
    # attrs, varargs, varkw, defaults = getargspec(func)
    signature_attrs, signature_varargs, signature_varkw, signature_defaults, signature_kwonlyargs, \
    signature_kwonlydefaults, signature_annotations = getfullargspec(func)
    # TODO better use signature(func) ? but that would be less compliant with python 2

    # (2) check that provided validators dont contain names that are incorrect
    if validators is not None:
        incorrect = set(validators.keys()) - set(signature_attrs)
        if len(incorrect) > 0:
            raise ValueError('@validate definition exception: validators are defined for \'' + str(incorrect) + '\' '
                             'that is/are not part of signature for ' + str(func))

    # (3) create a wrapper around the function to add validation
    # -- old:
    # @functools.wraps(func) -> to make the wrapper function look like the wrapped function
    # def wrapper(self, *args, **kwargs):
    # -- new:
    # we now use 'decorate' at the end of this code to have a wrapper that has the same signature, see below
    def wrapper(func, *args, **kwargs):
        # apply _validate on all received arguments
        apply_on_func_args(func, args, kwargs, signature_attrs, signature_defaults, signature_varargs, signature_varkw,
                           _validate, validators)

        # finally execute the method
        return func(*args, **kwargs)

    a = decorate(func, wrapper)
    # save the validators somewhere for reference
    a.__validators__ = validators
    return a


def _validate(value_to_validate, validator_func, func, att_name, ignore_if_none: bool = True):
    """
    Subroutine that actually executes validation

    :param value_to_validate: the value to validate
    :param validator_func: the validator function or a list of validator functions that will be applied on
    value_to_validate
    :param func: the method for which this validation is performed. This is used just for errors
    :param att_name: the name of the attribute that is being validated
    :return:
    """
    try:
        # try to interprete validator_func as a collection of validators
        # --handle case where the first is not_none
        if validator_func[0] is not_none:
            for val_func in validator_func:
                _validate(value_to_validate, val_func, func, att_name, ignore_if_none=False)
        else:
            for val_func in validator_func:
                # --the first was not not_none : dont allow it elsewhere
                if val_func is not_none:
                    raise ValueError('not_none is a special validator that can only be provided at the beginning of the'
                                     ' validators list')
                _validate(value_to_validate, val_func, func, att_name)

    except TypeError:
        # try to interprete validator_func as a single validator
        if (value_to_validate is None) and (validator_func is not not_none):
            # value is None : skip validation (users should explicitly include not_none as the first validator to
            # change this behaviour)
            pass
        else:
            # validate
            res = validator_func(value_to_validate)
            if res not in {None, True}:
                raise ValidationError.create(func, att_name, validator_func, value_to_validate)


class ValidationError(Exception):
    """
    Exception raised whenever validation fails. It may be directly triggered by Validators, or it is raised if 
    validator returns false
    """

    def __init__(self, contents):
        """
        We actually can't put more than 1 argument in the constructor, it creates a bug in Nose tests
        https://github.com/nose-devs/nose/issues/725
        
        Please use ValidationError.create() instead

        :param contents:
        """
        super(ValidationError, self).__init__(contents)

    @staticmethod
    def create(func, att_name, validator_func, item, extra_msg: str = ''):
        """
        
        :param func:
        :param att_name:
        :param validator_func: 
        :param item: 
        :param extra_msg
        :return: 
        """
        return ValidationError('Error validating input \'' + str(att_name) + '=' + str(item) + '\' for function \''
                               + str(func) + '\' with validator ' + str(validator_func) + '.\n' + extra_msg)


# ----------- some convenient validators ...
def not_none(x: Any):
    """ 'Is not None' validator """
    return x is not None


def not_(validator):
    """ Generates the inverse of the provided validator: when the validator returns False or raises a ValidationError,
     this validator returns True. Otherwise it returns False. """
    def validate(x):
        try:
            res = validator(x)
            # inverse the result
            return not res
        except ValidationError:
            # this is probably sane to return True
            return True

    return validate


def or_(validators):
    """ An 'or' validator: returns True if at least one of the provided validators is happy with the input. """

    def validate(x):
        for validator in validators:
            try:
                if validator(x):
                    # we can return : one validator was happy
                    return True
            except ValidationError:
                pass
        # no validator accepted: return false
        return False

    return validate


def xor_(validators):
    """ A 'xor' validator: returns True if exactly one of the provided validators is happy with the input. """

    def validate(x):
        ok = False
        for validator in validators:
            try:
                if validator(x):
                    if ok:
                        # second validator happy : fail, to many validators happy
                        return False
                    else:
                        # we found the first one happy
                        ok = True
            except ValidationError:
                pass
        # return if were happy or not
        return ok

    return validate

# ------------- orderables ----------------
def gt(min_value: Any, strict: bool = False):
    """
    'Greater than' validator generator.
    Returns a validator to check that x >= min_value (strict=False, default) or x > min_value (strict=True)

    :param min_value: minimum value for x
    :param strict: Boolean flag to switch between x >= min_value (strict=False) and x > min_value (strict=True)
    :return:
    """
    if strict:
        def gt(x):
            return x > min_value
    else:
        def gt(x):
            return x >= min_value
    return gt


def gts(min_value_strict: Any):
    """ Alias for 'greater than' validator generator in strict mode """
    return gt(min_value_strict, True)


def lt(max_value: Any, strict: bool = False):
    """
    'Lesser than' validator generator.
    Returns a validator to check that x <= max_value (strict=False, default) or x < max_value (strict=True)

    :param max_value: maximum value for x
    :param strict: Boolean flag to switch between x <= max_value (strict=False) and x < max_value (strict=True)
    :return:
    """
    if strict:
        def lt(x):
            return x < max_value
    else:
        def lt(x):
            return x <= max_value
    return lt


def lts(max_value_strict: Any):
    """ Alias for 'lesser than' validator generator in strict mode """
    return gt(max_value_strict, True)


def between(min_val: Any, max_val: Any, open_left: bool = False, open_right: bool = False):
    """
    'Is between' validator generator.
    Returns a validator to check that min_val <= x <= max_val (default). open_right and open_left flags allow to
    transform each side into strict mode. For example setting open_left=True will enforce min_val < x <= max_val

    :param min_val: minimum value for x
    :param max_val: maximum value for x
    :param open_left: Boolean flag to turn the left inequality to strict mode
    :param open_right: Boolean flag to turn the right inequality to strict mode
    :return:
    """
    if open_left and open_right:
        def between(x):
            return (min_val < x) and (x < max_val)
    elif open_left:
        def between(x):
            return (min_val < x) and (x <= max_val)
    elif open_right:
        def between(x):
            return (min_val <= x) and (x < max_val)
    else:
        def between(x):
            return (min_val <= x) and (x <= max_val)
    return between


# ------------- integers ------------------
def is_even(x: Integral):
    """ 'Is even' validator """
    return x % 2 == 0


def is_odd(x: Integral):
    """ 'Is odd' validator """
    return x % 2 != 0


# ------------- collections ----------------
def minlen(min_length: Integral, strict: bool = False):
    """
    'Minimum length' validator generator.
    Returns a validator to check that len(x) >= min_length (strict=False, default) or len(x) > min_length (strict=True)

    :param min_length: minimum length for x
    :param strict: Boolean flag to switch between len(x) >= min_length (strict=False) and len(x) > min_length
    (strict=True)
    :return:
    """
    if strict:
        def minlen(x):
            return len(x) > min_length
    else:
        def minlen(x):
            return len(x) >= min_length
    return minlen


def minlens(min_length_strict: Integral):
    """ Alias for 'Minimum length' validator generator in strict mode """
    return minlen(min_length_strict, True)


def maxlen(max_length: Integral, strict: bool = False):
    """
    'Maximum length' validator generator.
    Returns a validator to check that len(x) <= max_length (strict=False, default) or len(x) < max_length (strict=True)

    :param max_length: maximum length for x
    :param strict: Boolean flag to switch between len(x) <= max_length (strict=False) and len(x) < max_length
    (strict=True)
    :return:
    """
    if strict:
        def maxlen(x):
            return len(x) < max_length
    else:
        def maxlen(x):
            return len(x) <= max_length
    return maxlen


def maxlens(max_length_strict: Integral):
    """ Alias for 'Maximum length' validator generator in strict mode """
    return maxlen(max_length_strict, True)


def is_in(allowed_values: Set):
    """
    'Values in' validator generator.
    Returns a validator to check that x is in the provided set of allowed values

    :param allowed_values: a set of allowed values
    :return:
    """
    def valin(x):
        return x in allowed_values
    return valin


def is_subset(reference_set: Set):
    """
    'Is subset' validator generator.
    Returns a validator to check that x is a subset of reference_set

    :param reference_set: the reference set
    :return:
    """
    def is_subset(x):
        return len(x - reference_set) == 0
    return is_subset


def is_superset(reference_set: Set):
    """
    'Is superset' validator generator.
    Returns a validator to check that x is a superset of reference_set

    :param reference_set: the reference set
    :return:
    """
    def is_superset(x):
        return len(reference_set - x) == 0
    return is_superset
