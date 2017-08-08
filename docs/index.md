# python-autoclass

[![Build Status](https://travis-ci.org/smarie/python-autoclass.svg?branch=master)](https://travis-ci.org/smarie/python-autoclass) [![Tests Status](https://smarie.github.io/python-autoclass/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-autoclass/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-autoclass/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-autoclass) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-autoclass/) [![PyPI](https://img.shields.io/badge/PyPI-autoclass-blue.svg)](https://pypi.python.org/pypi/autoclass/)

`autoclass` provides tools to automatically generate python 3.5+ classes code, such as **constructor body** or **properties getters/setters**, along with optional support of **validation contracts**.

The objective of this library is to reduce the amount of redundancy by automatically generating parts of the code from the information already available somewhere else (typically, in the constructor signature). The intent is similar to [attrs](https://github.com/python-attrs/attrs): remove boilerplate.

## Installing

```bash
> pip install pyoad
```

You may wish to also install [PyContracts](https://andreacensi.github.io/contracts/index.html) or [enforce](https://github.com/RussBaz/enforce) in order to use the `@contract` or `@runtime_validation` annotations shown in this documentation.

```bash
> pip install PyContracts
> pip install enforce
```

## Example usage

The following snippet shows a `HouseConfiguration` class with four attributes.
Each attribute is validated against the expected type everytime you try to set it (constructor AND modifications), and the `name` and `surface` attribute are further validated (`len(name) > 0` and `surface >= 0`). Notice the size of the resulting code !

```python
from autoclass import autoargs, autoprops, setter_override
from autoclass import Boolean, validate, minlens, gt
from numbers import Real, Integral
from typing import Optional
from enforce import runtime_validation, config

config(dict(mode='covariant'))  # to accept subclasses in validation

@runtime_validation
@autoprops
class HouseConfiguration(object):
    @autoargs
    @validate(name=minlens(0),
              surface=gt(0))
    def __init__(self,
                 name: str,
                 surface: Real,
                 nb_floors: Optional[Integral] = 1,
                 with_windows: Boolean = False):
        pass

    # -- overriden setter for surface for custom validation or other things
    @setter_override
    def surface(self, surface):
        print('Set surface to {}'.format(surface))
        self._surface = surface
```

We can test that validation works:

```python
# Test
t = HouseConfiguration('test', 12, 2)
t.nb_floors = None  # Declared 'Optional': no error
t.nb_floors = 2.2   # Type validation: enforce raises a RuntimeTypeError
t.surface = -1      # Value validation: @validate raises a ValidationError
HouseConfiguration('', 12, 2)  # Value validation: @validate raises a ValidationError
```

Note that the `Real` and `Integral` types come from the [`numbers`](https://docs.python.org/3.6/library/numbers.html) built-in module. They provide an easy way to support both python primitives AND e.g. numpy primitives. In this library we provide an additional `Boolean` class to complete the picture.


## Why autoclass ?

Python's primitive types (in particular `dict` and `tuple`) and it's dynamic typing system make it extremely powerful, to the point that it is often more convenient for developers to use primitive types or generic dynamic objects such as [Munch](https://github.com/Infinidat/munch), rather than small custom classes.

However there are certain cases where developers still want to define their own classes, for example to provide strongly-typed APIs to their clients. In such case, *separation of concerns* will typically lead developers to enforce attribute value validation directly in the class, rather than in the code using the object. Eventually developers end up with big classes like this one:

```python
from autoclass import check_var, Boolean
from numbers import Real, Integral
from typing import Optional, Union

class HouseConfiguration(object):

    def __init__(self,
                 name: str,
                 surface: Real,
                 nb_floors: Optional[Integral] = 1,
                 with_windows: Boolean = False):
        self.name = name
        self.surface = surface
        self.nb_floors = nb_floors
        self.with_windows = with_windows
    
    # --name
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        check_var(name, var_name='name', var_types=str)
        self._name = name
    
    # --surface
    @property
    def surface(self) -> Real:
        return self._surface

    @surface.setter
    def surface(self, surface: Real):
        check_var(surface, var_name='surface', var_types=Real, 
                  min_value=0, min_strict=True)
        self._surface = surface
    
    # --nb_floors
    @property
    def nb_floors(self) -> Optional[Integral]:
        return self._nb_floors

    @nb_floors.setter
    def nb_floors(self, nb_floors: Optional[Integral]):
        check_var(nb_floors, var_name='nb_floors', var_types=Integral, 
                  enforce_not_none=False)
        self._surface = nb_floors # !**
        
    # --with_windows
    @property
    def with_windows(self) -> Boolean:
        return self._with_windows

    @with_windows.setter
    def with_windows(self, with_windows: Boolean):
        check_var(with_windows, var_name='with_windows', var_types=Boolean)
        self._with_windows = with_windows
```

Now that's **a lot of code** - and only for 4 attributes ! Not mentioning the code for `check_var` that was not included here for the sake of readability (I include it in the library, for reference). And guess what - it is still highly prone to **human mistakes**. For example I made a mistake in the setter for `nb_floors`, did you spot it ? Also it makes the code **less readable**: did you spot that the setter for the surface property is different from the others?

Really, *"there must be a better way"* : yes there is, and that's what this library provides - it can be used alone, or in combination with [PyContracts](https://andreacensi.github.io/contracts/index.html) and/or any PEP484-based checker such as [enforce](https://github.com/RussBaz/enforce), [typeguard](https://github.com/agronholm/typeguard), [typecheck-decorator](https://github.com/prechelt/typecheck-decorator), etc. in order to generate all the repetitive code for you. Here is an example with PyContracts:

```python
from autoclass import Boolean, autoprops, autoargs, setter_override
from typing import Optional, Union
from numbers import Real, Integral
from contracts import contract

@autoprops
class HouseConfiguration(object):

    @autoargs
    @contract(name='str[>0]', 
              surface='(int|float),>=0',
              nb_floors='None|int',
              with_windows='bool')
    def __init__(self, 
                 name: str, 
                 surface: Real, 
                 nb_floors: Optional[Integral] = 1, 
                 with_windows: Boolean = False):
        pass
    
    # -- overriden setter for surface - no need to repeat the @contract
    @setter_override
    def surface(self, surface: Real):
        assert surface > 0
        self._surface = surface
```

As you can see, this is more compact: 

* all object attributes (mandatory and optional with their default value) are declared in the `__init__` signature along with their optional [PEP 484 type hints](https://docs.python.org/3.5/library/typing.html)
* all attribute validation contracts are declared once in the `@contract` annotation of `__init__`
* it is still possible to implement custom logic in a getter or a setter, without having to repeat the `@contract`

Note: unfortunately with PyContracts the type information is duplicated. However if you use type checkers relying on PEP484 directly such as [enforce](https://github.com/RussBaz/enforce), [typeguard](https://github.com/agronholm/typeguard), [typecheck-decorator](https://github.com/prechelt/typecheck-decorator), etc. this is not the case - as we saw in the [initial example with enforce and validate](#example_usage).


## Main features

* **`@validate`** is a decorator for any method, that adds input validators to the method.

* Many validators are provided out of the box to use with `@validate`: `gt`, `between`, `is_in`, `maxlen`... check them out in [the validators list page](https://smarie.github.io/python-autoclass/validators/). But you can of course use your own, too.

* **`@autoargs`** is a decorator for the `__init__` method of a class. It automatically assigns all of the `__init__` method's parameters to `self`. For more fine-grain tuning, explicit inclusion and exclusion lists are supported, too. *Note: the original @autoargs idea and code come from [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049)*

* **`@autoprops`** is a decorator for a whole class. It automatically generates properties getters and setters for all attributes, with the correct PEP484 type hints. As for `@autoargs`, the default list of attributes is the list of parameters of the `__init__` method, and explicit inclusion and exclusion lists are supported. 

* **`@autoprops`** automatically adds `@contract` (*PyContracts*) or `@validate` (from `autoclass`) on the generated setters if a `@contract` or `@validate` exists for that attribute on the `__init__` method.

* **`@autoprops`**-generated getters and setters are fully PEP484 decorated so that type checkers like *enforce*'s `@runtime_validation` automatically apply to generated methods when used to decorate the whole class. No explicit integration needed in autoclass!

* You may override the getter or setter generated by `@autoprops` using **`@getter_override`** and **`@setter_override`**. Note that the `@contract` and `@validate` will still be added on your custom setter if present on `__init__`, you don't have to repeat it yourself

* Equivalent manual wrapper methods are provided for all decorators in this library: `autoargs_decorate(init_func, include, exclude)`, `autoprops_decorate(cls, include, exclude)`, `autoprops_override_decorate(func, attribute, is_getter)`, `validate_decorate(func, **validators)`


## See Also

* Initial idea of autoargs : [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049)

* On properties in Python and why you should only use them if you really need to (for example, to perform validation by contract): [Python is not java](http://dirtsimple.org/2004/12/python-is-not-java.html) and the follow up article [Getters/Setters/Fuxors](http://2ndscale.com/rtomayko/2005/getters-setters-fuxors)

* [PyContracts](https://andreacensi.github.io/contracts/index.html)

* PEP484-based checkers: 
    * [enforce](https://github.com/RussBaz/enforce)
    * [typeguard](https://github.com/agronholm/typeguard)
    * [typecheck-decorator](https://github.com/prechelt/typecheck-decorator)

* [attrs](https://github.com/python-attrs/attrs) is a library with the same target, but the way to use it is quite different from 'standard' python. It is very powerful and elegant, though.

* [decorator](http://pythonhosted.org/decorator/) library, which provides everything one needs to create complex decorators easily (signature and annotations-preserving decorators, decorators with class factory) as well as provides some useful decorators (`@contextmanager`, `@blocking`, `@dispatch_on`). We use it to preserve the signature of class constructors and overriden setter methods.

* When came the time to find a name for this library I was stuck for a while. In my quest for finding an explicit name that was not already used, I found many interesting libraries on [PyPI](http://pypi.python.org/). I did not test them all but found them 'good to know':
    * [decorator-args](https://pypi.python.org/pypi/decorator-args/1.1)
    * [classtools](https://github.com/eevee/classtools)
    * [classutils](https://pypi.python.org/pypi/classutils)
    * [python-utils](https://pypi.python.org/pypi/python-utils)
    * [utils](https://pypi.python.org/pypi/utils/0.9.0)


*Do you like this library ? You might also like [these](https://github.com/smarie?utf8=%E2%9C%93&tab=repositories&q=&type=&language=python)* 


## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-autoclass](https://github.com/smarie/python-autoclass)
