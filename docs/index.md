# python-classtools-autocode

`classtools-autocode` provides tools to automatically generate python 3.5 classes code, such as **constructor body** or **properties getters/setters**, along with optional support of **validation contracts**.

The objective of this library is to reduce the amount of redundancy by automatically generatic parts of the code from the information already available somewhere else (typically, in the constructor signature). The intent is similar to [attrs](https://github.com/python-attrs/attrs): remove boilerplate.

Github page : (https://github.com/smarie/python-classtools-autocode) 

## Why ?

Python's primitive types (in particular `dict` and `tuple`) and it's dynamic typing system make it extremely powerful, to the point that it is often more convenient for developers to use primitive types or generic dynamic objects such as [Munch](https://github.com/Infinidat/munch).

However there are certain cases where developers still want to define their own classes, for example to provide strongly-typed APIs to their clients. In such case, *separation of concerns* will typically lead developers to enforce attribute value validation directly in the class, rather than in the code using the object. Eventually developers end up with big classes like this one:

```python
from classtools_autocode import check_var
from typing import Optional, Union
from warnings import warn

class HouseConfiguration(object):

    def __init__(self, name: str, surface: Union[int, float], nb_floors: Optional[int], 
    with_windows: bool = False):
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
    def surface(self) -> Union[int, float]:
        return self._surface

    @surface.setter
    def surface(self, surface: Union[int, float]):
        check_var(surface, var_name='surface', var_types=[int,float], min_value=0)
        warn('You should really not do that..')
        self._surface = surface
    
    # --nb_floors
    @property
    def nb_floors(self) -> Optional[int]:
        return self._nb_floors

    @nb_floors.setter
    def nb_floors(self, nb_floors: Optional[int]):
        check_var(nb_floors, var_name='nb_floors', var_types=int, min_value=0, enforce_not_none=False)
        self._surface = nb_floors #
        
    # --with_windows
    @property
    def with_windows(self) -> bool:
        return self._with_windows

    @with_windows.setter
    def with_windows(self, with_windows: bool):
        check_var(with_windows, var_name='with_windows', var_types=bool)
        self._with_windows = with_windows
```

Now that's **a lot of code** - and only for 4 attributes ! Not mentioning the code for `check_var` that was not included here for the sake of readability (I include it in the library, for reference).  And guess what - it is still highly prone to **human mistakes**. For example I made a mistake in the setter for `nb_floors`, did you spot it ? Also it makes the code **less readable**: did you spot that the setter for the surface property is different from the others?

Really, *"there must be a better way"* : yes there is, and that's what this library provides - it can be used alone, or in combination with [PyContracts](https://andreacensi.github.io/contracts/index.html) and/or any PEP484-based checker such as [enforce](https://github.com/RussBaz/enforce), [typeguard](https://github.com/agronholm/typeguard), [typecheck-decorator](https://github.com/prechelt/typecheck-decorator), etc. in order to generate all the repetitive code for you :

```python
from classtools_autocode import autoprops, autoargs, setter_override
from typing import Optional, Union
from contracts import contract
from warnings import warn

@autoprops
class HouseConfiguration(object):

    @autoargs
    @contract(name='str[>0]', 
              surface='(int|float),>=0',
              nb_floors='None|int,>=0',
              with_windows='bool')
    def __init__(self, 
                 name: str, 
                 surface: Union[int, float], 
                 nb_floors: Optional[int], 
                 with_windows: bool = False):
        pass
    
    # -- overriden setter for surface - no need to repeat the @contract
    @setter_override
    def surface(self, surface: Union[int, float]):
        warn('You should really not do that..')
        self._surface = surface
```

As you can see, now all information is present only once: 

* all object attributes (mandatory and optional with their default value) are declared in the `__init__` signature along with their optional [PEP 484 type hints](https://docs.python.org/3.5/library/typing.html)
* all attribute validation contracts are declared once in the `@contract` annotation of `__init__`
* it is still possible to implement custom logic in a getter or a setter, without having to repeat the `@contract`

Note: actually one might argue that the type information is duplicated. This is true if you use PyContracts, but not if you use type checkers relying on PEP484 directly such as [enforce](https://github.com/RussBaz/enforce):
 
```python
from classtools_autocode import autoprops, autoargs, setter_override
from typing import Optional, Union
from enforce import runtime_validation
from warnings import warn

@runtime_validation
@autoprops
class HouseConfiguration(object):

    @autoargs
    def __init__(self, 
                 name: str, 
                 surface: Union[int, float], 
                 nb_floors: Optional[int], 
                 with_windows: bool = False):
        pass
    
    # -- overriden setter for surface - need to repeat the PEP484 type hints
    @setter_override
    def surface(self, surface: Union[int, float]):
        warn('You should really not do that..')
        self._surface = surface
```


## Main features

* **`@autoargs`** is a decorator for the `__init__` method of a class. It automatically assigns all of the `__init__` method's parameters to `self`. For more fine-grain tuning, explicit inclusion and exclusion lists are supported, too. *Note: the original @autoargs idea and code come from [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049)*

* **`@autoprops`** is a decorator for a whole class. It automatically generates properties getters and setters for all attributes, with the correct PEP484 type hints. As for `@autoargs`, the default list of attributes is the list of parameters of the `__init__` method, and explicit inclusion and exclusion lists are supported. 

* **`@autoprops`** automatically adds *PyContracts* `@contract` on the generated setters if a `@contract` exist for that property on the `__init__` method.

* **`@autoprops`**-generated getters and setters are fully PEP484 decorated so that type checkers like *enforce*'s `@runtime_validation` automatically apply to generated methods when used to decorate the whole class.

* You may override the getter or setter generated by `@autoprops` using **`@getter_override`** and **`@setter_override`**. Note that the `@contract` will still be added on your custom setter if present on `__init__`.

* Equivalent manual wrapper methods are provided for all decorators in this library: `autoargs_decorate(init_func, include, exclude)`, `autoprops_decorate(cls, include, exclude)`, `autoprops_override_decorate(func, attribute, is_getter)`. 


## Installation

### Recommended : create a clean virtual environment

We strongly recommend that you use conda *environment* or pip *virtualenv*/*venv* in order to better manage packages. Once you are in your virtual environment, open a terminal and check that the python interpreter is correct:

```bash
(Windows)>  where python
(Linux)  >  which python
```

The first executable that should show up should be the one from the virtual environment.


### Installation steps

This package is available on `PyPI`. You may therefore use `pip` to install from a release

```bash
> pip install classtools_autocode
```

### Checkers installation (optional)

You may wish to also install [PyContracts](https://andreacensi.github.io/contracts/index.html) or [enforce](https://github.com/RussBaz/enforce) in order to use the `@contract` and `@runtime_validation` annotations respectively.

```bash
> pip install PyContracts
> pip install enforce
```


### Uninstalling

As usual : 

```bash
> pip uninstall classtools_autocode
```

## Usage details

### @autoargs

Automatically affects the contents of a function to self. Initial code and test examples from [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049).

A few illustrative examples can be found in the unit tests below.

* Basic functionality, no customization - all constructor arguments are auto-assigned: 

    ```python
    from classtools_autocode import autoargs
    def test_autoargs_simple(self):
    
        # Basic functionality, no customization - all constructor arguments are auto-assigned
        class A(object):
            @autoargs
            def __init__(self, foo, path, debug=False):
                pass
    
        # Test : 
        # -- create an instance
        a = A('rhubarb', 'pie', debug=True)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)
    ```

* Basic functionality, with special case of variable arguments `*args`. Note that the variable arguments are stored in a single attribute: 

    ```python
    def test_autoargs_varargs(self):
    
        # Basic functionality, with special case of variable arguments *args.
        # -- note that the variable arguments are stored in a single attribute
        class B(object):
            @autoargs
            def __init__(self, foo, path, debug=False, *args):
                pass
    
        # Test : 
        # -- create an instance
        a = B('rhubarb', 'pie', True, 100, 101)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)
        # -- *args is in a single attribute
        self.assertTrue(a.args == (100, 101))
    ```

* Basic functionality, with special case of variable arguments `*args` and keyword arguments `**kw`. Note that `*args` are stored in a single attribute while `**kw` are stored in several attributes

    ```python
    def test_autoargs_varargs_kwvarargs(self):
    
        # Basic functionality, with special case of variable arguments *args and keyword arguments **kw
        # -- note that *args are stored in a single attribute while **kw are stored in several attributes
        class C(object):
            @autoargs
            def __init__(self, foo, path, debug=False, *args, **kw):
                pass
    
        # Test : 
        # -- create an instance
        a = C('rhubarb', 'pie', True, 100, 101, verbose=True, bar='bar')
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        self.assertTrue(a.path == 'pie')
        self.assertTrue(a.debug == True)
        # -- *args is in a single attribute
        self.assertTrue(a.args == (100, 101))
        # -- **kw is dispatched in several attributes
        self.assertTrue(a.verbose == True)
        self.assertTrue(a.bar == 'bar')
    ```
    
* Explicit list of names to include:

    ```python
    def test_autoargs_include(self):
    
        # Explicit list of names to include
        class C(object):
            @autoargs(include=('bar', 'baz', 'verbose'))
            def __init__(self, foo, bar, baz, verbose=False):
                pass
    
        # Test : 
        # -- create an instance
        a = C('rhubarb', 'pie', 1)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.bar == 'pie')
        self.assertTrue(a.baz == 1)
        self.assertTrue(a.verbose == False)
        # -- check that a non-included field does not exist
        with self.assertRaises(AttributeError):
            print(a.foo)
    ```

* Explicit list of names to exclude:

    ```python
    def test_autoargs_exclude(self):
    
        # Explicit list of names to exclude
        class C(object):
            @autoargs(exclude=('bar', 'baz', 'verbose'))
            def __init__(self, foo, bar, baz, verbose=False):
                pass
    
        # Test : 
        # -- create an instance
        a = C('rhubarb', 'pie', 1)
        # -- check that the fields exist and have the correct value
        self.assertTrue(a.foo == 'rhubarb')
        # -- check that the non-included fields do not exist
        with self.assertRaises(AttributeError):
            print(a.bar)
        with self.assertRaises(AttributeError):
            print(a.baz)
        with self.assertRaises(AttributeError):
            print(a.verbose)
    ```



### @autoprops

Automatically generates all properties getters and setters from the class constructor.

* Basic functionality, no customization - all constructor arguments become properties: 

    ```python
    def test_autoprops_no_contract(self):
        
        # Basic functionality, no customization - all constructor arguments become properties
        @autoprops
        class FooConfigA(object):

            @autoargs
            def __init__(self, a: str, b: List[str]):
                pass

        t = FooConfigA('rhubarb', ['pie', 'pie2'])

        # there are no contracts on the generated setters
        t.a=''
        t.b=['r','']
        # check that the generated getters work
        self.assertTrue(t.a == '')
        self.assertTrue(t.b[0] == 'r')
    ```

* if a **[PyContracts](https://andreacensi.github.io/contracts/index.html)** `@contract` annotation exist on the `__init__` method, mentioning a contract for a given parameter, the
parameter contract will be added on the generated setter method:

    ```python
    def test_autoprops(self):
    
        # Basic functionality with PyContracts - if a `@contract` annotation exist on the `__init__` method, mentioning
        # a contract for a given parameter, the parameter contract will be added on the generated setter method
        from contracts import ContractNotRespected, contract
    
        @autoprops
        class FooConfigA(object):
    
            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass
    
        t = FooConfigA('rhubarb', ['pie', 'pie2'])
    
        # check that there are contracts on the generated setters
        with self.assertRaises(ContractNotRespected):
            t.a = ''
        with self.assertRaises(ContractNotRespected):
            t.b = ['r','']
    
        # check that the generated getters work
        t.b=['r']
        self.assertTrue(t.b[0] == 'r')
    ```

* The user may override the generated getter and/or setter by creating them explicitly in the class and annotating
them with `@getter_override` or `@setter_override`. Note that the contract will still be dynamically added on the setter, even if the setter already has one (in such case a `UserWarning` will be issued)

    ```python
    def test_autoprops_override(self):
        from contracts import ContractNotRespected, contract
      
        @autoprops
        class FooConfigC(object):
        
            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass
        
            @getter_override
            def a(self):
                # in addition to getting the fields we'd like to print something
                print('a is being read. Its value is \'' + str(self._a) + '\'')
                return self._a
        
            @setter_override(attribute='b')
            def another_name(self, toto: List[str]):
                # in addition to setting the fields we'd like to print something
                print('Property \'b\' was set to \'' + str(toto) + '\'')
                self._b = toto
        
        
        t = FooConfigC('rhubarb', ['pie', 'pie2'])
        
        # check that we can still read a's value
        self.assertTrue(t.a == 'rhubarb')
        
        # check that 'a' still has a contract on its setter
        with self.assertRaises(ContractNotRespected):
            t.a = ''
        
        # check that 'b' still has a contract on its setter
        with self.assertRaises(ContractNotRespected):
            t.b=[''] # we can not
        
        # check that 'b' still has a getter generated
        t.b = ['eh', 'oh']
        self.assertTrue(t.b == ['eh', 'oh'])
    ```


* Note: you may also perform the same action without decorator, using `autoprops_decorate(cls)`.

    ```python
    def test_manual(self):

        from contracts import ContractNotRespected
        from contracts import contract

        # we don't use @autoprops here
        class FooConfigA(object):
            @autoargs
            @contract(a='str[>0]', b='list[>0](str[>0])')
            def __init__(self, a: str, b: List[str]):
                pass

        # we execute it here
        autoprops_decorate(FooConfigA)

        t = FooConfigA('rhubarb', ['pie', 'pie2'])

        # check that there are contracts on the generated setters
        with self.assertRaises(ContractNotRespected):
            t.a = ''
        with self.assertRaises(ContractNotRespected):
            t.b = ['r','']

        # check that the generated getters work
        t.b = ['r']
        self.assertTrue(t.b[0] == 'r')
    ```

## See Also

* Initial idea of autoargs : [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049)

* On properties in Python and why you should only use them if you really need to (for example, to perform validation by contract): [Python is not java](http://dirtsimple.org/2004/12/python-is-not-java.html) and the follow up article [Getters/Setters/Fuxors](http://2ndscale.com/rtomayko/2005/getters-setters-fuxors)

* [PyContracts](https://andreacensi.github.io/contracts/index.html)

* PEP484-based checkers: 
    * [enforce](https://github.com/RussBaz/enforce)
    * [typeguard](https://github.com/agronholm/typeguard)
    * [typecheck-decorator](https://github.com/prechelt/typecheck-decorator)

* [attrs](https://github.com/python-attrs/attrs)

* [decorator](http://pythonhosted.org/decorator/) library, which provides everything one needs to create complex decorators easily (signature and annotations-preserving decorators, decorators with class factory) as well as provides some useful decorators (`@contextmanager`, `@blocking`, `@dispatch_on`). We use it to preserve the signature of class constructors and overriden setter methods.

* When came the time to find a name for this library I was stuck for a while. In my quest for finding an explicit name that was not already used, I found many interesting libraries on [PyPI](http://pypi.python.org/). I did not test them all but found them 'good to know':
    
    * [decorator-args](https://pypi.python.org/pypi/decorator-args/1.1)
    * [classtools](https://github.com/eevee/classtools)
    * [classutils](https://pypi.python.org/pypi/classutils)
    * [python-utils](https://pypi.python.org/pypi/python-utils)
    * [utils](https://pypi.python.org/pypi/utils/0.9.0)


*Do you like this library ? You might also like [these](https://github.com/smarie?utf8=%E2%9C%93&tab=repositories&q=&type=&language=python)* 


## Want to contribute ?

Details on the github page: https://github.com/smarie/python-classtools-autocode 