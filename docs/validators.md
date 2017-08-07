## Validators list

Several validators are bundled in the package to be used with `@validate`. Don't hesitate to propose new ones !

### All objects

#### not_none

Checks that the input is not None. This is a special validator: if it is not present and first in the validators' list, a `None` input will always be silently ignored. 

#### not_

Generates the inverse of the provided validator: when the validator returns False or raises a ValidationError, this validator returns True. Otherwise it returns False.

#### or_

An 'or' validator: returns True if at least one of the provided validators is happy with the input.

#### xor_

A 'xor' validator: returns True if exactly one of the provided validators is happy with the input.

### Comparables

#### gt

'Greater than' validator generator. Returns a validator to check that `x >= min_value` (strict=False, default) or `x > min_value` (strict=True)

#### gts

Alias for 'greater than' validator generator in strict mode

#### lt

'Lesser than' validator generator. Returns a validator to check that `x <= max_value` (strict=False, default) or `x < max_value` (strict=True)

#### lts

Alias for 'lesser than' validator generator in strict mode

#### between

'Is between' validator generator. Returns a validator to check that `min_val <= x <= max_val` (default). `open_right` and `open_left` flags allow to transform each side into strict mode. For example setting `open_left=True` will enforce `min_val < x <= max_val`

### Numbers

#### is_even

Validates that x is even (`x % 2 == 0`)

#### is_odd

Validates that x is odd (`x % 2 != 0`)

### Collections

#### minlen

'Minimum length' validator generator. Returns a validator to check that `len(x) >= min_length` (strict=False, default) or `len(x) > min_length` (strict=True)

#### minlens

Alias for minlen in strict mode

#### maxlen

'Maximum length' validator generator. Returns a validator to check that `len(x) <= max_length` (strict=False, default) or `len(x) < max_length` (strict=True)

#### maxlens

Alias for maxlen in strict mode

#### is_in

'Values in' validator generator. Returns a validator to check that x is in the provided set of allowed values

#### is_subset

'Is subset' validator generator. Returns a validator to check that `x` is a subset of `reference_set`. That is, `len(x - reference_set) == 0`

#### is_superset

'Is superset' validator generator. Returns a validator to check that `x` is a superset of `reference_set`. That is, `len(reference_set - x) == 0`