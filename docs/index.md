# python-autoclass

*Write compact python classes*

[![Python versions](https://img.shields.io/pypi/pyversions/autoclass.svg)](https://pypi.python.org/pypi/autoclass/) [![Build Status](https://travis-ci.org/smarie/python-autoclass.svg?branch=master)](https://travis-ci.org/smarie/python-autoclass) [![Tests Status](https://smarie.github.io/python-autoclass/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-autoclass/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-autoclass/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-autoclass)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-autoclass/) [![PyPI](https://img.shields.io/pypi/v/autoclass.svg)](https://pypi.python.org/pypi/autoclass/) [![Downloads](https://pepy.tech/badge/autoclass)](https://pepy.tech/project/autoclass) [![Downloads per week](https://pepy.tech/badge/autoclass/week)](https://pepy.tech/project/autoclass) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-autoclass.svg)](https://github.com/smarie/python-autoclass/stargazers)

!!! success "`autoclass` is now fully compliant with [`pyfields`](https://smarie.github.io/python-pyfields/) ! Check out how you can create very compact classes [here](#pyfields-combo)"

`autoclass` provides tools to automatically generate python classes code. The objective of this library is to reduce the amount of redundancy by automatically generating parts of the code from the information already available somewhere else (in the constructor signature or in the `pyfields` fields for example). It is made of several independent features that can be combined:

 * with `@autoargs` you don't have to write `self.xxx = xxx` in your constructor
 * with `@autoprops` all or part your constructor arguments become `properties` and their setter is annotated with the same PEP484 type hints and value validation methods
 * with `@autohash`, your object is hashable based on the tuple of all fields (so it can be used as a dictionary key or put in a set)
 * with `@autodict`, your object behaves like a dictionary, is comparable with dictionaries, and gets a string representation
 * with `@autorepr`, your object gets a string representation (use either this or `@autodict`, not both at the same time)
 * with `@autoclass`, you get all of the above at once (but you can still disable some of them)

The intent is similar to [attrs](https://github.com/python-attrs/attrs) and [PEP557 dataclasses](https://www.python.org/dev/peps/pep-0557): remove boilerplate code. However as opposed to these, 

 * this library can be applied on *any* class. It does not change anything in your coding habits: you can still create a `__init__` constructor, and everything else is provided with decorators. 
 * if information about fields is available from another library, `autoclass` can easily leverage it : for example you can now use [`pyfields`](https://smarie.github.io/python-pyfields/) to declare the fields, `autoclass` will support it.
 * all decorators above can be used independently, for example if you just need to add a dictionary behaviour to an existing class you can use `@autodict` only.
 * all created code is simple and readable. You can easily step through the generated functions in debug mode to understand what's going on
 * as opposed to `attrs`, setters are generated for the fields so validation libraries such as [valid8](https://smarie.github.io/python-valid8/) can wrap them. Alternatively if you use `pyfields`, it directly provides this feature.

In other words, `autoclass` simply generates the same code that you *would have written* manually. For this reason, in many cases you can use *other* libraries on top of the resulting classes without hassle. A good example is that you can use any PEP484 type checking library of your choice.


## Installing

```bash
> pip install autoclass
```

You may wish to also install 

 * [`pyfields`](https://smarie.github.io/python-pyfields/) to create compact classes.
 * a PEP484-based type checker: [typeguard](https://github.com/agronholm/typeguard) , [pytypes](https://github.com/Stewori/pytypes) or [enforce](https://github.com/RussBaz/enforce).
 * a value validator: [valid8](https://smarie.github.io/python-valid8/) was originally created in this project and is now independent.

Alternatively, you may use [PyContracts](https://andreacensi.github.io/contracts/index.html) to perform type and value validation at the same time using `@contract`, but this will not benefit from PEP484 and uses a dedicated syntax. This documentation also shows some examples.


```bash
> pip install pyfields
> pip install pytypes
> pip install valid8
> pip install PyContracts
```

## 1. Basic usage

The following code shows how you define a `House` with two attributes `name` and `nb_floors`:

```python
from autoclass import autoclass

@autoclass
class House:    
    def __init__(self, name, nb_floors = 1):
        pass
```

**That's it !** By default you get that the constructor is filled automatically, a "dictionary" behaviour is added to the class, a string representation of objects is available, and objects are comparable (equality) and hashable:

```bash
>>> obj = House('my_house', 3)

>>> print(obj)  # string representation
House(name='my_house', nb_floors=3)

>>> [att for att in obj.keys()]  # dictionary behaviour
['name', 'nb_floors']

>>> assert {obj, obj} == {obj}  # hashable: can be used in a set or as a dict key

>>> assert obj == House('my_house', 3)  # comparison (equality)
>>> assert obj == {'name': 'my_house', 'nb_floors': 3}  # comparison with dicts
```

If you wish to add some behaviour (custom logic, logging...) when attributes are accessed or set, you can easily override the generated getters and setters. For example, below we will print a message everytime `nb_floors` is set:

```python
from autoclass import autoclass, setter_override

@autoclass
class House:    
    def __init__(self, name, nb_floors = 1):
        pass
    
    @setter_override
    def nb_floors(self, nb_floors = 1):
        print('Set nb_floors to {}'.format(nb_floors))
        self._nb_floors = nb_floors
```

We can test it:

```bash
>>> obj = House('my_house')
Set nb_floors to 1

>>> obj.nb_floors = 3
Set nb_floors to 3
```

### `pyfields` combo

If you already use [`pyfields`](https://smarie.github.io/python-pyfields/) to define mandatory/optional fields with type/value validation, simply decorate your class with `@autoclass` and you'll get all of the above (dict view, hashability, string representation, equality...) too:

```python
from pyfields import field
from autoclass import autoclass
from mini_lambda import x

@autoclass
class House:
    name: str = field(check_type=True, doc="the name of your house")
    nb_floors: int = field(default=1, check_type=True, doc="the nb floors",
                           validators={
                               "should be positive": x >= 0,
                               "should be a multiple of 100": x % 100 == 0
                           })

```

Indeed behind the scenes, if `autoclass` detects that your class uses `pyfields`, it will automatically use the fields rather than the constructor signature to get the list of fields. You can check that all the features are there:

```bash
>>> obj = House('my_house', 200)

>>> print(obj)  # string representation
House(name='my_house', nb_floors=200)

>>> [att for att in obj.keys()]  # dictionary behaviour
['name', 'nb_floors']

>>> assert {obj, obj} == {obj}  # hashable: can be used in a set or as a dict key

>>> assert obj == House('my_house', 200)  # comparison (equality)
>>> assert obj == {'name': 'my_house', 'nb_floors': 200}  # comparison with dicts
```

Note: this works with python 2.7, and 3.5+. See [`pyfields` documentation ](https://smarie.github.io/python-pyfields/) for details.

## 2. Type and Value validation

If you do not use `pyfields`, then you might be interested to add type and value validation to your fields through another means.

### a- PEP484 Type validation

#### enforce

PEP484 is the standard for inserting python type hint in function signatures, starting from python 3.5 (a backport is available through the independent `typing` module). Many compliant type checkers are now available such as [enforce](https://github.com/RussBaz/enforce) or [pytypes](https://github.com/Stewori/pytypes).

If you decorate your *class constructor* with PEP484 type hints, then `autoclass` detects it and will automatically decorate the generated property getters and setters. We use `enforce` runtime checker in this example:

```python
from autoclass import autoclass
from enforce import runtime_validation

@runtime_validation
@autoclass
class House:
    # the constructor below is decorated with PEP484 type hints
    def __init__(self, name: str, nb_floors: int = 1):
        pass
```

We can test it:

```bash
>>> obj = House('my_house')

>>> obj.nb_floors = 'red'
enforce.exceptions.RuntimeTypeError: 
  The following runtime type errors were encountered:
       Argument 'nb_floors' was not of type <class 'int'>. Actual type was str.
```

See `enforce` documentation for details.

#### pytypes

Below is the same example, but with `pytypes` instead of `enforce`:

```python
from autoclass import autoclass
from pytypes import typechecked

@typechecked
@autoclass
class House:
    # the constructor below is decorated with PEP484 type hints
    def __init__(self, name: str, nb_floors: int = 1):
        pass
```

#### `typeguard`

TODO


### b- Simple Type+Value validation

#### valid8

[valid8](https://smarie.github.io/python-valid8/) was originally created in this project and is now independent. It provides mainly value validation, but also basic type validation. With `valid8`, in order to add validation to any function, you simply decorate that function with `@validate_arg`, possibly providing custom error types to raise:

```python
from valid8 import validate_arg

@validate_arg('foo', <validation functions>, error_type=MyErrorType)
def my_func(foo):
    ...
```

Now if you decorate your *class constructor* with `@validate_arg`, then `autoclass` detects it and will automatically decorate the generated property setters too. 

```python
from autoclass import autoclass
from mini_lambda import s, x, Len
from valid8 import validate_arg, InputValidationError
from valid8.validation_lib import instance_of, is_multiple_of

# 2 custom validation errors for valid8
class InvalidName(InputValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurface(InputValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

@autoclass
class House:
    @validate_arg('name', instance_of(str), Len(s) > 0,
                  error_type=InvalidName)
    @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                  error_type=InvalidSurface)
    def __init__(self, name, surface=None):
        pass
```

We can test it:

```bash
>>> obj = House('sweet home', 200)

>>> obj.surface = None   # Valid (surface is nonable by signature)

>>> obj.name = 12  # Type validation
InvalidName: name should be a non-empty string.

>>> obj.surface = 10000  # Value validation
InvalidSurface: Surface should be between 0 and 10000 and be a multiple of 100.
```

See `valid8` [documentation](https://smarie.github.io/python-valid8) for details. Note that other validation libraries relying on the same principles could probably be supported easily, please create an issue to suggest some !


#### PyContracts

[PyContracts](https://andreacensi.github.io/contracts/index.html) is also supported:

```python
from autoclass import autoclass
from contracts import contract

@autoclass
class House:

    @contract(name='str[>0]', 
              surface='None|(int,>=0,<10000)')
    def __init__(self, name, surface):
        pass
```


### c- PEP484 Type+Value validation

Finally, in real-world applications you might wish to combine both PEP484 type checking and value validation. This works as expected, for example with `enforce` and `valid8`:

```python
from autoclass import autoclass

# Imports - for type validation
from numbers import Integral
from enforce import runtime_validation, config
config(dict(mode='covariant'))  # type validation will accept subclasses too

# Imports - for value validation
from mini_lambda import s, x, Len
from valid8 import validate_arg, InputValidationError
from valid8.validation_lib import is_multiple_of

# 2 custom validation errors for valid8
class InvalidName(InputValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurface(InputValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

@runtime_validation
@autoclass
class House:
    @validate_arg('name', Len(s) > 0,
                  error_type=InvalidName)
    @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                  error_type=InvalidSurface)
    def __init__(self, name: str, surface: Integral=None):
        pass
```

We can test that validation works:

```bash
>>> obj = House('sweet home', 200)

>>> obj.surface = None   # Valid (surface is nonable by signature)

>>> obj.name = 12  # Type validation > PEP484
enforce.exceptions.RuntimeTypeError: 
  The following runtime type errors were encountered:
       Argument 'name' was not of type <class 'str'>. Actual type was int.

>>> obj.surface = 10000  # Value validation > valid8
InvalidSurface: Surface should be between 0 and 10000 and be a multiple of 100.
```


## Why autoclass ?

Python's primitive types (in particular `dict` and `tuple`) and it's dynamic typing system make it extremely powerful, to the point that it is often more convenient for developers to use primitive types or generic dynamic objects such as [Munch](https://github.com/Infinidat/munch), rather than small custom classes.

However there are certain cases where developers still want to define their own classes, for example to provide strongly-typed APIs to their clients. In such case, *separation of concerns* will typically lead developers to enforce attribute value validation directly in the class, rather than in the code using the object. Eventually developers end up with big classes like this one:

```python
from valid8 import validate, Boolean
from numbers import Real, Integral
from typing import Optional, Union

class House:

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
        validate('name', name, instance_of=str)
        self._name = name
    
    # --surface
    @property
    def surface(self) -> Real:
        return self._surface

    @surface.setter
    def surface(self, surface: Real):
        validate('surface', surface, instance_of=Real, min_value=0, min_strict=True)
        self._surface = surface
    
    # --nb_floors
    @property
    def nb_floors(self) -> Optional[Integral]:
        return self._nb_floors

    @nb_floors.setter
    def nb_floors(self, nb_floors: Optional[Integral]):
        validate('nb_floors', nb_floors, instance_of=Integral, enforce_not_none=False)
        self._surface = nb_floors # !**
        
    # --with_windows
    @property
    def with_windows(self) -> Boolean:
        return self._with_windows

    @with_windows.setter
    def with_windows(self, with_windows: Boolean):
        validate('with_windows', with_windows, instance_of=Boolean)
        self._with_windows = with_windows
```

Not to mention extra methods such as `__str__`, `__eq__`, `from_dict`, `to_dict`... 

Now that's **a lot of code** - and only for 4 attributes ! Not mentioning the code for `validate` that was not included here for the sake of readability. And guess what - it is still highly prone to **human mistakes**. For example I made a mistake in the setter for `nb_floors`, did you spot it ? Also it makes the code **less readable**: did you spot that the setter for the surface property is different from the others?

Really, *"there must be a better way"* : yes there is, and that's what this library provides.


## Main features

* **`@autoargs`** is a decorator for the `__init__` method of a class. It automatically assigns all of the `__init__` method's parameters to `self`. For more fine-grain tuning, explicit inclusion and exclusion lists are supported, too. *Note: the original @autoargs idea and code come from [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049)*

* **`@autoprops`** is a decorator for a whole class. It automatically generates properties getters and setters for all attributes, with the correct PEP484 type hints. As for `@autoargs`, the default list of attributes is the list of parameters of the `__init__` method, and explicit inclusion and exclusion lists are supported. 

    * `@autoprops` automatically adds `@contract` (*PyContracts*) or `@validate_arg` (from `valid8`) on the generated setters if a `@contract` or `@validate_arg` exists for that attribute on the `__init__` method. 
    * `@autoprops`-generated getters and setters are fully PEP484 decorated so that type checkers like *enforce* automatically apply to generated methods when used to decorate the whole class. No explicit integration needed in autoclass!
    * You may override the getter or setter generated by `@autoprops` using **`@getter_override`** and **`@setter_override`**. Note that the `@contract` and `@validate` will still be added on your custom setter if present on `__init__`, you don't have to repeat it yourself

* **`@autodict`** is a decorator for a whole class. It makes a class behave like a (read-only) dict, with control on which attributes are visible in that dictionary. So this is a 'dict view' on top of an object, basically the opposite of `munch` (that is an 'object view' on top of a dict). It automatically implements `__eq__`, `__str__` and `__repr__` if they are not present already.

* **`@autohash`** is a decorator for a whole class. It makes the class hashable by implementing `__hash__` if not already present, where the hash is computed from the tuple of selected fields (all by default, customizable).

* **`@autorepr`** is a decorator for a whole class. It adds a string representation by implementing `__str__` and `__repr__` if not already present.

* Equivalent manual wrapper methods are provided for all decorators in this library: 
    - `autoargs_decorate(init_func, include, exclude)`
    - `autoprops_decorate(cls, include, exclude)`
    - `autoprops_override_decorate(func, attribute, is_getter)`
    - `autodict_decorate(cls, include, exclude, only_known_fields, only_public_fields)`
    - `autohash_decorate(cls, include, exclude, only_known_fields, only_public_fields)`
    - `autorepr_decorate(cls, include, exclude, only_known_fields, only_public_fields)` 


## See Also

* Initial idea of autoargs : [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049)

* On properties in Python and why you should only use them if you really need to (for example, to perform validation by contract): [Python is not java](http://dirtsimple.org/2004/12/python-is-not-java.html) and the follow up article [Getters/Setters/Fuxors](http://2ndscale.com/rtomayko/2005/getters-setters-fuxors)

* [PyContracts](https://andreacensi.github.io/contracts/index.html)

* PEP484-based checkers: 
    * [enforce](https://github.com/RussBaz/enforce)
    * [pytypes](https://github.com/Stewori/pytypes)
    * [typeguard](https://github.com/agronholm/typeguard)
    * [typecheck-decorator](https://github.com/prechelt/typecheck-decorator)

* [attrs](https://github.com/python-attrs/attrs) is a library with the same target, but the way to use it is quite different from 'standard' python. It is very powerful and elegant, though.

* The new PEP out there, largely inspired by `attrs`: [PEP557](https://www.python.org/dev/peps/pep-0557). Check it out! There is also a [discussion on python-ideas](https://groups.google.com/forum/#!topic/python-ideas/8vUm84CCb3c).

* [decorator](http://decorator.readthedocs.io) library, which provides everything one needs to create complex decorators easily (signature and annotations-preserving decorators, decorators with class factory) as well as provides some useful decorators (`@contextmanager`, `@blocking`, `@dispatch_on`). We used it to preserve the signature of class constructors and overriden setter methods. Now we use [`makefun`](https://smarie.github.io/python-makefun/) instead, which was inspired by it.

* When came the time to find a name for this library I was stuck for a while. In my quest for finding an explicit name that was not already used, I found many interesting libraries on [PyPI](http://pypi.python.org/). I did not test them all but found them 'good to know':
    * [decorator-args](https://pypi.python.org/pypi/decorator-args/1.1)
    * [classtools](https://github.com/eevee/classtools)
    * [classutils](https://pypi.python.org/pypi/classutils)
    * [python-utils](https://pypi.python.org/pypi/python-utils)
    * [utils](https://pypi.python.org/pypi/utils/0.9.0)


*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-autoclass](https://github.com/smarie/python-autoclass)
