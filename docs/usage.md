# Usage details

## @autoargs

Automatically affects the contents of a function to self. Initial code and test examples from [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049).

A few illustrative examples can be found below.

* Basic functionality, no customization - all constructor arguments are auto-assigned: 

```python
from autoclass import autoargs

class A(object):
    @autoargs
    def __init__(self, foo, path, debug=False):
        pass

# Test : 
# -- create an instance
a = A('rhubarb', 'pie', debug=True)

# -- check that the fields exist and have the correct value
assert a.foo == 'rhubarb'
assert a.path == 'pie'
assert a.debug == True
```

* Basic functionality, with special case of variable arguments `*args`. Note that the variable arguments are stored in a single attribute: 

```python
class B(object):
    @autoargs
    def __init__(self, foo, path, debug=False, *args):
        pass

# Test : 
# -- create an instance
a = B('rhubarb', 'pie', True, 100, 101)
# -- check that the fields exist and have the correct value
assert a.foo == 'rhubarb'
assert a.path == 'pie'
assert a.debug == True
# -- *args is in a single attribute
assert a.args == (100, 101)
```

* Basic functionality, with special case of variable arguments `*args` and keyword arguments `**kw`. Note that `*args` are stored in a single attribute and now `**kw` are, too (for consistency reasons this changed in 1.10.0).

```python
class C(object):
    @autoargs
    def __init__(self, foo, path, debug=False, *args, **kw):
        pass

# Test : 
# -- create an instance
a = C('rhubarb', 'pie', True, 100, 101, verbose=True, bar='bar')
# -- check that the fields exist and have the correct value
assert a.foo == 'rhubarb'
assert a.path == 'pie'
assert a.debug == True
# -- *args is in a single attribute
assert a.args == (100, 101)
# -- **kw is in a single attribute too
assert a.kw == dict(verbose=True, bar='bar')
```
    
* Explicit tuple or list of names to include:

```python
class C(object):
    @autoargs(include=['bar', 'baz', 'verbose'])
    def __init__(self, foo, bar, baz, verbose=False):
        pass

# Test : 
# -- create an instance
a = C('rhubarb', 'pie', 1)
# -- check that the fields exist and have the correct value
assert a.bar == 'pie'
assert a.baz == 1
assert a.verbose == False
# -- check that a non-included field does not exist
print(a.foo)# raises AttributeError
```

* Explicit tuple or list of names to exclude:

```python
class C(object):
    @autoargs(exclude=('bar', 'baz', 'verbose'))
    def __init__(self, foo, bar, baz, verbose=False):
        pass

# Test : 
# -- create an instance
a = C('rhubarb', 'pie', 1)
# -- check that the fields exist and have the correct value
assert a.foo == 'rhubarb'
# -- check that the non-included fields do not exist
print(a.bar)  # raises AttributeError
print(a.baz)  # raises AttributeError
print(a.verbose)  # raises AttributeError
```

Finally note that `@autoargs` is automatically applied when you decorate the whole class with `@autoclass`, see below.


## @autoprops

Automatically generates all properties getters and setters from the class constructor.

* Basic functionality, no customization - all constructor arguments become properties: 

```python
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
assert t.a == ''
assert t.b[0] == 'r'
```

* You can include or exclude some properties in the list of those generated with :

```python
@autoprops(include=('a', 'b'))
class Foo(object):
    ...

@autoprops(exclude=('b'))
class Bar(object):
    ...
```

* if a **[PyContracts](https://andreacensi.github.io/contracts/index.html)** `@contract` annotation exist on the `__init__` method, mentioning a contract for a given parameter, the
parameter contract will be added on the generated setter method:

```python
from contracts import ContractNotRespected, contract

@autoprops
class FooConfigB(object):

    @autoargs
    @contract(a='str[>0]', b='list[>0](str[>0])')
    def __init__(self, a: str, b: List[str]):
        pass

t = FooConfigB('rhubarb', ['pie', 'pie2'])

# check that the generated getters work
t.b=['r']
assert t.b[0] == 'r'

# check that there are contracts on the generated setters
t.a = ''  # raises ContractNotRespected
t.b = ['r','']  # raises ContractNotRespected
```

* if a `@validate` annotation (from `valid8` library) exist on the `__init__` method, mentioning a contract for a given parameter, the parameter contract will be added on the generated setter method:

```python
# we use valid8 as the value validator
from valid8 import validate

@autoprops
class FooConfigC(object):

    @autoargs
    @validate(a=minlens(0))
    def __init__(self, a: str):
        pass

t = FooConfigC('rhubarb')

# check that the generated getters work
t.a='r'
assert t.a == 'r'

# check that there are validators on the generated setters
t.a = ''  # raises ValidationError
```

* The user may override the generated getter and/or setter by creating them explicitly in the class and annotating
them with `@getter_override` or `@setter_override`. Note that the contract will still be dynamically added on the setter, even if the setter already has one (in such case a `UserWarning` will be issued)

```python
@autoprops
class FooConfigD(object):

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

t = FooConfigD('rhubarb', ['pie', 'pie2'])

# check that we can still read a's value
assert t.a == 'rhubarb'

# check that 'b' still has a getter generated
t.b = ['eh', 'oh']
assert t.b == ['eh', 'oh']

# check that 'a' still has a contract on its setter
t.a = ''  # raises ContractNotRespected

# check that 'b' still has a contract on its setter
t.b=['']  # raises ContractNotRespected
```


* Note: you may also perform the same action without decorator, using `autoprops_decorate(cls)`.

```python
# we don't use @autoprops here
class FooConfigD(object):
    @autoargs
    @contract(a='str[>0]', b='list[>0](str[>0])')
    def __init__(self, a: str, b: List[str]):
        pass

# we execute it here
autoprops_decorate(FooConfigD)

t = FooConfigD('rhubarb', ['pie', 'pie2'])

# check that the generated getters work
t.b = ['r']
assert t.b[0] == 'r'

# check that there are contracts on the generated setters
t.a = ''  # raises ContractNotRespected
t.b = ['r','']  # raises ContractNotRespected
```

Finally note that `@autoprops` is automatically applied when you decorate the whole class with `@autoclass`, see below.


## @autodict

Automatically generates a read-only dictionary view on top of the object. It does several things:

* it adds `collections.Mapping` to the list of parent classes (i.e. to the class' `__bases__`)
* it generates `__len__`, `__iter__` and `__getitem__` in order for the appropriate fields to be exposed in the dict view. Parameters allow to customize the list of fields that will be visible. Note that any methods with the same name will be overridden.
* if `only_constructor_args` is `True` (default), it generates a static `from_dict` method in the class corresponding to a call to the constructor with the unfolded dict. Note that this method may be overridden by the user.
* if `__eq__` is not implemented on this class, it generates a version that handles the case `self == other` where other is of the same type. In that case the dictionary equality is used. Other equality tests remain unchanged.
* if `__str__` and `__repr__` are not implemented on this class, it generates them too.

Examples:

* Basic functionality, no customization - all constructor arguments can be viewed in the dict: 

```python
@autodict
class A(object):
    def __init__(self, a: int, b: str):
        self.a = a
        self.b = b

o = A(1, 'r')
# o behaves like a read-only dict
assert o == dict(o)
assert o == {'a': 1, 'b': 'r'}

# you can create an object from a dict too, thanks to the generated class function
p = A.from_dict({'a': 1, 'b': 'r'})
assert p == o

# str and repr methods show interesting stuff
str(p)  # "A({'a': 1, 'b': 'r'})"
repr(p)  # "A({'a': 1, 'b': 'r'})"
```

* You can obviously combine it with `@autoargs`:

```python
@autodict
class B(object):
    @autoargs
    def __init__(self, a: int, b: str):
        pass

o = B(1, 'r')
# same results
assert o == {'a': 1, 'b': 'r'}
p = B.from_dict({'a': 1, 'b': 'r'})
assert p == o
```

* Note that by default only fields with the same name than constructor arguments are visible:

```python
@autodict
class C(object):
    @autoargs
    def __init__(self, a: str, b: List[str]):
        self.non_constructor_arg = 't'
        self._private = 1
        self.__class_private = 't'

o = C(1, 'r')
# only fields corresponding to constructor arguments are visible
assert o == {'a': 1, 'b': 'r'}
```

* You can decide to open to all object fields, including or excluding (default) the fields that are not arguments of the constructor, and including or excluding (default) the class-private ones. Note that class-private attributes will be visible with their usual scrambled name:

```python
@autodict(only_constructor_args=False, only_public_fields=False)
class D(object):
    @autoargs
    def __init__(self, a: str, b: List[str]):
        self.non_constructor_arg = 'b'
        self._private = 1
        self.__class_private = 't'

o = D(1, 'r')
# o behaves like a read-only dict, all fields are now visible
assert o == dict(o)
assert o == {'a': 1, 'b': 'r',
             'non_constructor_arg': 'b',
             '_private': 1,
             '_D__class_private': 't'}  # notice the name
``` 

* In addition, you can include or exclude some names in the list of visible fields with one of `include` or `exclude`:

```python
@autodict(include=['a', 'b'], ...)
class Foo(object):
    ...

@autodict(exclude=['b'], ...)
class Bar(object):
    ...
```

Finally note that `@autodict` is automatically applied when you decorate the whole class with `@autoclass`, see below.


## @autohash

A decorator to makes objects of the class implement __hash__, so that they can be used correctly for example in sets. Parameters allow to customize the list of attributes that are taken into account in the hash.

Examples:

* Basic functionality, no customization - all object fields are used in the hash: 

```python
@autohash
class A(object):
    def __init__(self, a: int, b: str):
        self.a = a
        self.b = b

o = A(1, 'r')
o._test = 2

# o is hashable
assert hash(o) == hash((1, 'r', 2))

p = A(1, 'r')
p._test = 2
# o and p have identical hash
assert hash(o) == hash(p)

# dynamic and private fields are taken into account by default
p._test = 3
assert hash(o) != hash(p)
```

* You can decide to restrict the hash to only the fields that are constructor arguments, or to only the fields that are public:

```python
from random import random

@autohash(only_constructor_args=True, only_public_fields=True)
class D(object):
    @autoargs
    def __init__(self, a: str, _b: str):
        self.non_constructor_arg = random()
        self._private = random()
        self.__class_private = random()

o = D(1, 'r')
p = D(1, 'r')

# o and p have the same hash because only the constructor arguments are taken into account
assert hash(o) == hash(p)
assert hash(o) == hash((1, 'r'))
``` 

* In addition, you can include or exclude some names in the list of visible fields with one of `include` or `exclude`:

```python
@autohash(include=['a', 'b'], ...)
class Foo(object):
    ...

@autohash(exclude=['b'], ...)
class Bar(object):
    ...
```

Finally note that `@autohash` is automatically applied when you decorate the whole class with `@autoclass`, see below.


## @autoclass

Applies all or part of the above decorators at once. Useful if you want to make the most from this library.

* Basic functionality, no customization - all constructor arguments become properties that are auto-assigned in constructor, and the object behaves like a dict and can be created from a dict: 

```python
from numbers import Integral
from typing import Optional

# we will use enforce as the runtime checker
import enforce as en
from enforce import runtime_validation
en.config(dict(mode='covariant'))  # allow subclasses when validating types

# we use valid8 as the value validator
from valid8 import validate

# class definition
@runtime_validation
@autoclass
class AllOfTheAbove:
    @validate(a=gt(1), c=minlen(1))
    def __init__(self, a: Integral, b: Boolean, c: Optional[List[str]] = None):
        pass

# instance creation
o = AllOfTheAbove(a=2, b=True)

# @autoargs works
assert o.a == 2

# @autoprops works, in combination with any runtime checker (here demonstrated with enforce)
o.b = 1  # !RuntimeTypeError Argument 'b' was not of type Boolean. Actual type was int.

# @autodict works
assert o == {'a': 2, 'b': True, 'c': None}
assert AllOfTheAbove.from_dict(o) == o
assert dict(**o) == o
```

* you can also disable part of the features :

```python
@autoclass(autodict=False)
class PartsOfTheAbove:
    @validate(a=gt(1), c=minlen(1))
    def __init__(self, a: Integral, b: Boolean, c: Optional[List[str]] = None):
        pass

# instance creation
o = PartsOfTheAbove(a=2, b=True)

assert o == {'a': 2, 'b': True, 'c': None}  # AssertionError
assert PartsOfTheAbove.from_dict(o) == o  # AttributeError: 'PartsOfTheAbove' has no attribute 'from_dict'
assert dict(**o) == o  # TypeError: argument after ** must be a mapping
```


## Alternative to decorators: manual function wrappers

Equivalent manual wrapper methods are provided for all decorators in this library: `autoargs_decorate(init_func, include, exclude)`, `autoprops_decorate(cls, include, exclude)`, `autoprops_override_decorate(func, attribute, is_getter)`, `autodict_decorate(cls, include, exclude, only_constructor_args, only_public_fields)`, `autoclass_decorate(cls, include, exclude, autoargs, autoprops, autodict)`

Therefore you can do:

```python
from autoclass import autoclass_decorate

class A:
    ...

A = autoclass_decorate(A)
```
