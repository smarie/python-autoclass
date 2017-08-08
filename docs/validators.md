## Validators list

Several validators are bundled in the package to be used with `@validate`. Don't hesitate to propose new ones !

### All objects

#### not_none

Checks that the input is not None. This is a special validator: if it is not present and first in the validators' list, a `None` input will always be silently ignored. 

Note that if you use `@validate` in combination with a PEP484 type checker such as enforce, you don't need to include the `not_none` validator. Indeed if an input is not explicitly declared with type `Optional[...]` or `Union[NoneType, ...]`, a good type checker should already raise an error.

#### and_(validators_list)

An 'and' validator: returns True if all of the provided validators are happy with the input. This method will raise a ValidationException on the first False received or Exception caught

#### not_(validator or validators_list)

Generates the inverse of the provided validator: when the validator returns False or raises a `ValidationError`, this validator returns True. Otherwise it returns False. If the `catch_all` parameter is set to `True`, any exception will be caught instead of just `ValidationError`s.

Note that you may provide a list of validators to `not_()`. It will be interpreted as `not_(and_(<valiators_list>))`

```python
@validate(a=not_(is_even), b=not_([is_even, is_mod(3)]))
def myfunc(a, b):
    print('hello')

myfunc(11, 11)  # ok
myfunc(84, 82)  # ValidationError! a is even
myfunc(84, 3)   # ValidationError: b is odd (ok) but it is a multiple of 3 (nok)
```

#### or_(validators_list)

An 'or' validator: returns True if at least one of the provided validators is happy with the input. All exceptions will be silently caught. In case of failure, a global ValidationException will be raised, together with the first exception message if any.

#### xor_(validators_list)

A 'xor' validator: returns True if exactly one of the provided validators is happy with the input. All exceptions will be silently caught. In case of failure, a global ValidationException will be raised, together with the first exception message if any.

### Comparables

#### gt(min_value, strict: bool = False)

'Greater than' validator generator. Returns a validator to check that `x >= min_value` (strict=False, default) or `x > min_value` (strict=True)

#### gts(min_value)

Alias for 'greater than' validator generator in strict mode

#### lt(max_value, strict: bool = False)

'Lesser than' validator generator. Returns a validator to check that `x <= max_value` (strict=False, default) or `x < max_value` (strict=True)

#### lts(max_value)

Alias for 'lesser than' validator generator in strict mode

#### between(min_value, max_value, open_left: bool = False, open_right: bool = False)

'Is between' validator generator. Returns a validator to check that `min_val <= x <= max_val` (default). `open_right` and `open_left` flags allow to transform each side into strict mode. For example setting `open_left=True` will enforce `min_val < x <= max_val`

### Numbers

#### is_even

Validates that x is even (`x % 2 == 0`)

#### is_odd

Validates that x is odd (`x % 2 != 0`)

#### is_mod(ref)

Validates that x is a multiple of the reference (`x % ref == 0`)


### Collections

#### minlen(min_length, strict: bool = False)

'Minimum length' validator generator. Returns a validator to check that `len(x) >= min_length` (strict=False, default) or `len(x) > min_length` (strict=True)

#### minlens(min_length)

Alias for minlen in strict mode

#### maxlen(max_length, strict: bool = False)

'Maximum length' validator generator. Returns a validator to check that `len(x) <= max_length` (strict=False, default) or `len(x) < max_length` (strict=True)

#### maxlens(max_length)

Alias for maxlen in strict mode

#### is_in(allowed_values)

'Values in' validator generator. Returns a validator to check that x is in the provided set `allowed_values`

#### is_subset(reference_set)

'Is subset' validator generator. Returns a validator to check that `x` is a subset of `reference_set`. That is, `len(x - reference_set) == 0`

#### is_superset(reference_set)

'Is superset' validator generator. Returns a validator to check that `x` is a superset of `reference_set`. That is, `len(reference_set - x) == 0`