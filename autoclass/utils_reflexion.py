# from inspect import signature, getmembers, Parameter
# from typing import Any  # do not import Type for compatibility with earlier python 3.5


# def get_missing_mandatory_parameters(param_names:set, object_type:Type[Any]):
#     """
#     Utility method to get the set of missing mandatory parameters, from a set of parameters and an object type
#
#     :param param_names:
#     :param object_type:
#     :return:
#     """
#     return set(param_names) - set(get_mandatory_param_names(object_type))


# def get_all_param_names(item_type: Type[Any]):
#     """
#     Utility function to extract the constructor and find all its parameter names
#
#     :param item_type:
#     :return:
#     """
#     # extract unique constructor signature
#     constructor = get_constructor(item_type)
#     s = signature(constructor)
#
#     # return all parameters
#     return [attribute_name for attribute_name, param in s.parameters.items()]


# def get_mandatory_param_names(item_type: Type[Any]):
#     """
#     Utility function to extract the constructor and find its mandatory parameter names
#
#     :param item_type:
#     :return:
#     """
#     # extract unique constructor signature
#     constructor = get_constructor(item_type)
#     s = signature(constructor)
#
#     # return mandatory parameters
#     return [attribute_name for attribute_name, param in s.parameters.items() if param.default is Parameter.empty]


def get_constructor(typ, allow_inheritance: bool=False):
    """
    Utility method to return the unique constructor (__init__) of a type

    :param typ: a type
    :param allow_inheritance: if True, the constructor will be returned even if it is not defined in this class
    (inherited). By default this is set to False: an exception is raised when no constructor is explicitly defined in
    the class
    :return: the found constructor
    """

    # constructors = [f[1] for f in getmembers(typ) if f[0] is '__init__']
    # if len(constructors) > 1:
    #     raise Exception('Several constructors were found for class ' + str(typ))
    # if len(constructors) == 0:
    #     raise Exception('No constructor was found for class ' + str(typ))
    #
    # constructor = constructors[0]
    #
    # # if constructor is a wrapped function, access to the underlying function

    # faster: just access it!
    if allow_inheritance:
        return typ.__init__
    else:
        # check that the constructor is really defined here
        if '__init__' in typ.__dict__:
            return typ.__init__
        else:
            raise Exception('No explicit constructor was found for class ' + str(typ))


# def get_class_that_defined_method(meth):
#     """
#     Utility method, from
# http://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3/25959545#25959545
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
