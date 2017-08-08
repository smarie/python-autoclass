## Usage details

### @validate

Adds input validation to a method. Simply declare the name of the input to validate and associate to it a validator or a list of validators:

```python
@validate(<input_name>=<validator_or_list_of_validators>, ...)
```

Many validators are provided out of the box to use with `@validate`: `gt`, `between`, `is_in`, `maxlen`... check them out in [the validators list page](https://smarie.github.io/python-autoclass/validators/). For example below we check that input `a` is not `None`, is even, and is greater than 1, and that input `b` is even:

```python
from autoclass import validate, not_none, is_even, gt

@validate(a=[not_none, is_even, gt(1)], b=is_even)
def myfunc(a, b):
    print('hello')
    
myfunc(84, 82)  # OK
myfunc(None,0)  # ValidationError: a is None
myfunc(1,0)     # ValidationError: a is not even
myfunc(2,1)     # ValidationError: b is not even
myfunc(0,0)     # ValidationError: a is not >= 1
```

#### `not_none` in combination with type checkers such as enforce

When used in combination with a PEP484 type checker such as enforce, you don't need to include the `not_none` validator. Indeed if an input is not explicitly declared with type `Optional[...]` or `Union[NoneType, ...]`, a good type checker should already raise an error:

```python
from enforce import runtime_validation
from numbers import Integral
from autoclass import validate, is_even, gt

@runtime_validation
@validate(a=[is_even, gt(1)], b=is_even)
def myfunc(a: Integral, b):
    print('hello')

# -- check that the validation works
myfunc(84, None) # OK because b has no type annotation nor not_none validator
myfunc(None, 0)  # RuntimeTypeError: a is None
```


#### Implementing custom validators

You may implement your own validators: simply provide a function that returns `True` in case of correct validation, and either raises an exception or returns `False` in case validation fails. The `ValidationError` type is provided for convenience, but you may wish to use another exception type. The example below shows four styles of validators 

```python
from autoclass import validate, ValidationError

def is_mod_3(x):
    """ A simple validator with no parameters """
    return x % 3 == 0

def is_mod(ref):
    """ A validator generator, with parameters """
    def is_mod_ref(x):
        return x % ref == 0
    return is_mod_ref

def gt_ex1(x):
    """ A validator raising a custom exception in case of failure """
    if x >= 1:
        return True
    else:
        raise ValidationError('gt_ex1: x >= 1 does not hold for x=' + str(x))

def gt_assert2(x):
    """ (not recommended) A validator relying on assert and therefore only valid in 'debug' mode """
    assert x >= 2

@validate(a=[gt_ex1, gt_assert2, is_mod_3],
          b=is_mod(5))
def myfunc(a, b):
    print('hello')

# -- check that the validation works
myfunc(21, 15)  # ok
myfunc(4,21)    # ValidationError: a is not a multiple of 3
myfunc(15,1)    # ValidationError: b is not a multiple of 5
myfunc(1,0)     # AssertionError: a is not >= 2
myfunc(0,0)     # ValidationError: a is not >= 1
```


### @autoargs

Automatically affects the contents of a function to self. Initial code and test examples from [this answer from utnubu](http://stackoverflow.com/questions/3652851/what-is-the-best-way-to-do-automatic-attribute-assignment-in-python-and-is-it-a#answer-3653049).

A few illustrative examples can be found in the unit tests below.

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

* Basic functionality, with special case of variable arguments `*args` and keyword arguments `**kw`. Note that `*args` are stored in a single attribute while `**kw` are stored in several attributes

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
# -- **kw is dispatched in several attributes
assert a.verbose == True
assert a.bar == 'bar'
```
    
* Explicit list of names to include:

```python
class C(object):
    @autoargs(include=('bar', 'baz', 'verbose'))
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

* Explicit list of names to exclude:

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


### @autoprops

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

* if a **[PyContracts](https://andreacensi.github.io/contracts/index.html)** `@contract` annotation exist on the `__init__` method, mentioning a contract for a given parameter, the
parameter contract will be added on the generated setter method:

```python
from contracts import ContractNotRespected, contract

@autoprops
class FooConfigA(object):

    @autoargs
    @contract(a='str[>0]', b='list[>0](str[>0])')
    def __init__(self, a: str, b: List[str]):
        pass

t = FooConfigA('rhubarb', ['pie', 'pie2'])

# check that the generated getters work
t.b=['r']
assert t.b[0] == 'r'

# check that there are contracts on the generated setters
t.a = ''  # raises ContractNotRespected
t.b = ['r','']  # raises ContractNotRespected
```

* if a `@validate` annotation exist on the `__init__` method, mentioning a contract for a given parameter, the parameter contract will be added on the generated setter method:

```python
@autoprops
class FooConfigA(object):

    @autoargs
    @validate(a=minlens(0))
    def __init__(self, a: str):
        pass

t = FooConfigA('rhubarb')

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
class FooConfigA(object):
    @autoargs
    @contract(a='str[>0]', b='list[>0](str[>0])')
    def __init__(self, a: str, b: List[str]):
        pass

# we execute it here
autoprops_decorate(FooConfigA)

t = FooConfigA('rhubarb', ['pie', 'pie2'])

# check that the generated getters work
t.b = ['r']
assert t.b[0] == 'r'

# check that there are contracts on the generated setters
t.a = ''  # raises ContractNotRespected
t.b = ['r','']  # raises ContractNotRespected
```