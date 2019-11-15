#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.

import platform
import sys
import types
import warnings

from autoclass.utils import check_known_decorators, read_fields, Source
from decopatch import class_decorator, DECORATED

try:  # python 3+
    from inspect import signature
except ImportError:
    from funcsigs import signature

try:  # python 3.5+
    from typing import Union, Tuple, TypeVar
    try:  # python 3.5.3+
        from typing import Type
    except ImportError:
        pass
    C = TypeVar('C')
except ImportError:
    pass


@class_decorator
def autoslots(include=None,           # type: Union[str, Tuple[str]]
              exclude=None,           # type: Union[str, Tuple[str]]
              use_public_names=True,  # type: bool
              add_weakref_slot=True,  # type: bool
              cls=DECORATED
              ):
    """
    Creates a replacement class with slots instead of the decorated class.

    In the new class, the slots are automatically created using the attributes list introspected from constructor,
    optionally filtered with the include/exclude filters.

    If `use_public_names` is set to `True` (default) the slots names are the same than the attributes in the
    constructor. If it is set to `False`, private names (with a leading `_`) will be used, corresponding to property
    names.

    This feature is mostly a copy from `attrs` as they tackled one nasty issue with super() very nicely.

    :param include: a tuple of explicit attributes to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param use_public_names: a boolean (default=True) indicating if the slot names should be the same names than the
        constructor names, or the
    :param add_weakref_slot: a boolean indicating if a `__weakref__` slot should be added (default: True)
    :param cls: the class on which to execute. Note that it won't be wrapped.
    :return:
    """
    return autoslots_decorate(cls, include=include, exclude=exclude, use_public_names=use_public_names,
                              add_weakref_slot=add_weakref_slot)


def autoslots_decorate(cls,                    # type: Type[C]
                       include=None,           # type: Union[str, Tuple[str]]
                       exclude=None,           # type: Union[str, Tuple[str]]
                       use_public_names=True,  # type: bool
                       add_weakref_slot=True,  # type: bool
                       ):
    # type: (...) -> Type[C]
    """



    :param cls: the class on which to execute. Note that it won't be wrapped.
    :param include: a tuple of explicit attributes to include (None means all)
    :param exclude: a tuple of explicit attribute names to exclude. In such case, include should be None.
    :param use_public_names: a boolean (default=True) indicating if the slot names should be the same names than the
        constructor names, or the
    :param add_weakref_slot: a boolean indicating if a `__weakref__` slot should be added (default: True)
    :return:
    """
    # first check that we do not conflict with other known decorators
    check_known_decorators(cls, '@autoslots')

    # retrieve the list of fields from pyfields or constructor signature
    selected_names, source = read_fields(cls, include=include, exclude=exclude, caller="@autoslots")

    # c. Collect the various items in the namespace of the class
    cd = {k: v for k, v in cls.__dict__.items() if k not in ("__dict__", "__weakref__")}

    # Traverse the MRO to check for an existing __weakref__.
    weakref_inherited = False
    base_names = []
    for base_cls in cls.__mro__[1:-1]:
        base_names += getattr(base_cls, "__slots__", ())
        if "__weakref__" in  getattr(base_cls, "__dict__", ()):  # not needed: "in basename"
            weakref_inherited = True
            break

    if use_public_names:
        names = selected_names
    else:
        names = tuple("_%s" % a for a in selected_names)

    # are there slots already on this class ?
    existing_cls_slots = list(cls.__dict__.get("__slots__", ()))

    if add_weakref_slot and not weakref_inherited \
        and "__weakref__" not in names:  # and "__weakref__" not in existing_cls_slots \
        names += ("__weakref__",)

    # Now we augment the namespace of the class to create, with

    # We only add the names of attributes that aren't inherited.
    # Settings __slots__ to inherited attributes wastes memory.
    slot_names = [name for name in names if name not in base_names and name not in existing_cls_slots]
    # add pre-existing slots from the class
    for es in existing_cls_slots:
        slot_names.append(es)
        # remove existing slot descriptor from the class
        del cd[es]
    cd["__slots__"] = tuple(slot_names)

    # __getstate__/__setstate__ need to be overridden for pickle to continue working
    # see https://stackoverflow.com/questions/28665411/odd-behavior-with-slots-and-pickle
    # __weakref__ is not writable.
    state_attr_names = tuple(an for an in slot_names if an != "__weakref__")

    def __getstate__(self):
        """
        Generated by @autoslots
        """
        return tuple(getattr(self, name) for name in state_attr_names)

    def __setstate__(self, state):
        """
        Generated by @autoslots
        """
        for name, value in zip(state_attr_names, state):
            setattr(self, name, value)

    cd["__getstate__"] = __getstate__
    cd["__setstate__"] = __setstate__

    # Finally create the new class
    new_cls = type(cls)(cls.__name__, cls.__bases__, cd)

    # Shameously copied from `attrs` (in particular very tricky code of `set_closure_cell` below)
    # A fix for https://github.com/python-attrs/attrs/issues/102.
    # On Python 3, if a method mentions `__class__` or uses the no-arg super(), the
    # compiler will bake a reference to the class in the method itself
    # as `method.__closure__`.  Since we replace the class with a
    # clone, we rewrite these references so it keeps working.
    for item in cls.__dict__.values():
        if isinstance(item, (classmethod, staticmethod)):
            # Class- and staticmethods hide their functions inside.
            # These might need to be rewritten as well.
            closure_cells = getattr(item.__func__, "__closure__", None)
        else:
            closure_cells = getattr(item, "__closure__", None)

        if not closure_cells:  # Catch None or the empty list.
            continue
        for cell in closure_cells:
            try:
                match = cell.cell_contents is cls
            except ValueError:  # ValueError: Cell is empty
                pass
            else:
                if match:
                    set_closure_cell(cell, new_cls)

    return new_cls


# ------------- code below shameously copied from https://github.com/python-attrs/attrs/blob/master/src/attr/_compat.py
# so as to fix the bug in autoslots when super() is used.

PY2 = sys.version_info[0] == 2
PYPY = platform.python_implementation() == "PyPy"


if PY2:
    def just_warn(*args, **kw):  # pragma: nocover
        """
        We only warn on Python 3 because we are not aware of any concrete
        consequences of not setting the cell on Python 2.
        """

else:  # Python 3 and later.
    def just_warn(*args, **kw):
        """
        We only warn on Python 3 because we are not aware of any concrete
        consequences of not setting the cell on Python 2.
        """
        warnings.warn(
            "Running interpreter doesn't sufficiently support code object "
            "introspection.  Some features like bare super() or accessing "
            "__class__ will not work with slotted classes.",
            RuntimeWarning,
            stacklevel=2,
        )


def make_set_closure_cell():
    """Return a function of two arguments (cell, value) which sets
    the value stored in the closure cell `cell` to `value`.
    """
    # pypy makes this easy. (It also supports the logic below, but
    # why not do the easy/fast thing?)
    if PYPY:  # pragma: no cover

        def set_closure_cell(cell, value):
            cell.__setstate__((value,))

        return set_closure_cell

    # Otherwise gotta do it the hard way.

    # Create a function that will set its first cellvar to `value`.
    def set_first_cellvar_to(value):
        x = value
        return

        # This function will be eliminated as dead code, but
        # not before its reference to `x` forces `x` to be
        # represented as a closure cell rather than a local.
        def force_x_to_be_a_cell():  # pragma: no cover
            return x

    try:
        # Extract the code object and make sure our assumptions about
        # the closure behavior are correct.
        if PY2:
            co = set_first_cellvar_to.func_code
        else:
            co = set_first_cellvar_to.__code__
        if co.co_cellvars != ("x",) or co.co_freevars != ():
            raise AssertionError  # pragma: no cover

        # Convert this code object to a code object that sets the
        # function's first _freevar_ (not cellvar) to the argument.
        if sys.version_info >= (3, 8):
            # CPython 3.8+ has an incompatible CodeType signature
            # (added a posonlyargcount argument) but also added
            # CodeType.replace() to do this without counting parameters.
            set_first_freevar_code = co.replace(
                co_cellvars=co.co_freevars, co_freevars=co.co_cellvars
            )
        else:
            args = [co.co_argcount]
            if not PY2:
                args.append(co.co_kwonlyargcount)
            args.extend(
                [
                    co.co_nlocals,
                    co.co_stacksize,
                    co.co_flags,
                    co.co_code,
                    co.co_consts,
                    co.co_names,
                    co.co_varnames,
                    co.co_filename,
                    co.co_name,
                    co.co_firstlineno,
                    co.co_lnotab,
                    # These two arguments are reversed:
                    co.co_cellvars,
                    co.co_freevars,
                ]
            )
            set_first_freevar_code = types.CodeType(*args)

        def set_closure_cell(cell, value):
            # Create a function using the set_first_freevar_code,
            # whose first closure cell is `cell`. Calling it will
            # change the value of that cell.
            setter = types.FunctionType(
                set_first_freevar_code, {}, "setter", (), (cell,)
            )
            # And call it to set the cell.
            setter(value)

        # Make sure it works on this interpreter:
        def make_func_with_cell():
            x = None

            def func():
                return x  # pragma: no cover

            return func

        if PY2:
            cell = make_func_with_cell().func_closure[0]
        else:
            cell = make_func_with_cell().__closure__[0]
        set_closure_cell(cell, 100)
        if cell.cell_contents != 100:
            raise AssertionError  # pragma: no cover

    except Exception:
        return just_warn
    else:
        return set_closure_cell


set_closure_cell = make_set_closure_cell()
