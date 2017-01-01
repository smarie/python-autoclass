import functools
from inspect import getmembers, signature, getfullargspec, Parameter, ismethod, getmro, isfunction, getmodule
from typing import Type, Any, Tuple


def autoprops(cls,**kwargs):
    """
    A decorator to automatically generate all properties getters and setters from the class constructor.
    Not all parameters of the __init__ method will have getter and setter generated:
    * if a @contract annotation exist on the __init__ method, mentioning a contract for a given parameter,
    a getter and a setter will be generated, and the parameter contract will be added on the generated setter method
    * The user may override the generated getter and setter by creating them explicitly in the class. In that case,
    if the setter has no contract, the contract will still be dynamically added

    From http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049
    :param include:
    :param kwargs:
    :return:
    """

    # perform the class mod
    # TODO better create a wrapper than modify the class?
    _autoprops_class(cls)

    # class Autoprops_Wrapper(object):
    #     def __init__(self, *args, **kwargs):
    #         self.wrapped = cls(*args, **kwargs)
    #
    # return Autoprops_Wrapper

    return cls


def _autoprops_class(object_type: Type[Any]):
    """
    This method will automatically add one getter and one setter for each constructor argument *that has a contract*
    It will also set the slots of the class so that it can not have any additional attribute created dynamically

    :param object_type:
    :return:
    """

    # 1. Find the constructor
    # extract unique constructor __init__
    constructor = get_constructor(object_type)

    # extract the __init__ signature
    s = signature(constructor)

    # extract the contracts added by pycontracts decorator if any
    contracts_dict = constructor.__contracts__ if hasattr(constructor, '__contracts__') else {}
    for att_to_transform_in_prop, contract_string in contracts_dict.items():
        if contract_string is not None:
            add_property(object_type, att_to_transform_in_prop, contract_string)


def add_property(object_type:Type[Any], property_name:str, property_contract:Any):
    """
    A method to dynamically define a getter and a setter for a property
    :param property_name:
    :param property_contract:
    :return:
    """

    # 0. check that we can import contracts
    try:
        # noinspection PyUnresolvedReferences
        from contracts import ContractNotRespected, contract
    except ImportError as e:
        raise Exception(
            'Use of @autoprops requires that PyContract library is installed. Check that you can \'import contracts\'')

    # a) create the private field name :
    #
    # __datetimeName
    private_property_name = '__' + property_name

    # b) create the property
    #
    # @property
    # def datetimeName(self):
    #     return self.__datetimeName
    property_obj = property(lambda self: getattr(self, private_property_name))

    # c) create the setter
    #
    # @datetimeName.setter
    # @contract(val='str[>0]')  # check_var(val, var_name='datetimeName', var_types=str)
    # def datetimeName(self, datetimeName):
    #     self.__datetimeName = datetimeName
    def setter_fun(self, val):
        setattr(self, private_property_name, val)
    # add the contract without the decorator
    f = contract(setter_fun, **{'val': property_contract})

    # change the function name to make it look nice
    f.__name__ = property_name
    f.__module__ = object_type.__module__
    f.__qualname__ = object_type.__name__ + '.' + property_name
    #__annotations__
    #__doc__

    # the only thing we can't do is to replace the parameter function name dynamically
    # so we wrap the function again :(
    def _contracts_parser_interceptor(func):
        @functools.wraps(func)  # to make the wrapper function look like the wrapped function
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except ContractNotRespected as e:
                e.error = e.error.replace('\'val\'', '\'' + property_name + '\'')
                raise e
        return wrapper


    # WARNING : this does absolutely nothing :)
    # property_obj.setter(f)

    # Add the property's setter (and getter) to the class
    setattr(object_type, property_name, property_obj.setter(_contracts_parser_interceptor(f)))

    return



def autoargs(include:Tuple[str]=None,exclude:Tuple[str]=None):
    """
    Defines a decorator with parameters, to automatically affect the contents of a function to self.
    From http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049

    :param include: a tuple of attribute names to include in the auto-assignment. If None, all arguments will be
    included by default
    :param exclude: a tuple of attribute names to exclude from the auto-assignment. In such case, include should be None
    :return:
    """
    if callable(include):
        # we have probably been called without argument
        return _get_autoargs_decorator()(include)
    else:
        return _get_autoargs_decorator(include=include, exclude=exclude)


def _get_autoargs_decorator(include:Tuple[str]=None,exclude:Tuple[str]=None,lock_class_fields=False):
    """
    lock doesnot work
    :param include:
    :param exclude:
    :param lock_class_fields:
    :return:
    """

    if include and exclude:
        raise ValueError('Only one of \'include\' or \'exclude\' argument should be provided.')

    def _autoargs_decorator(func):

        #if not callable(func):
            # that's because we are trying to call the constructor dynamically
        #    func = include[0]
        #attrs, varargs, varkw, defaults = getargspec(func)

        signature_attrs, signature_varargs, signature_varkw, signature_defaults, signature_kwonlyargs, \
        signature_kwonlydefaults, signature_annotations = getfullargspec(func)
        # TODO better use signature(func) ?

        if lock_class_fields:
            if signature_varkw:
                raise Exception('cant lock field names with variable kwargs')
            else:
                object_type = get_class_that_defined_method(func)
                if include:
                    fields = include
                else:
                    fields = signature_attrs[1:]
                    if signature_varargs:
                        fields.append(signature_varargs)
                    if exclude:
                        for a in exclude:
                            fields.remove(a)

                # right now, doesnot work
                _lock_fieldnames_class(object_type, field_names=tuple(fields))

        def sieve(attr):
            """decide whether the action has to be performed on the attribute or not, based on its name"""
            if exclude and attr in exclude:
                return False
            if not include or attr in include:
                return True
            else:
                return False

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
            return func(self,*args,**kwargs)

        return wrapper

    return _autoargs_decorator



def get_missing_mandatory_parameters(param_names:set, object_type:Type[Any]):
    """
    Utility method to get the set of missing mandatory parameters, from a set of parameters and an object type

    :param param_names:
    :param object_type:
    :return:
    """
    return (set(param_names) - set(get_mandatory_param_names(object_type)))


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
        raise ValueError('Several constructors were found for class ' + str(item_type))
    if len(constructors) == 0:
        raise ValueError('No constructor was found for class ' + str(item_type))

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
