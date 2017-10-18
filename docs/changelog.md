### 1.8.1 - minor improvements
 * Now detecting conflicts with `enforce` when annotations are not in the right order (see [#12](https://github.com/smarie/python-autoclass/issues/12))
 * Added tests for `on_each_` and `on_all_` and fixed corresponding bugs.

### 1.8.0 - new validators for collections
 * Added `on_each_` and `on_all_`

### 1.7.1 - bug fix: lts validator
 * `lts` was erroneously mappend onto `gt`. Fixed this.

### 1.7.0 - @autoclass
 * New decorator `@autoclass` to apply several features at once.
 * `@autodict` now also generates a `from_dict` static method in the class, as well as `__str__`, `__repr__` and `__eq__` if not present 

### 1.6.0 - @autodict
 * New decorator `@autodict` to make a class behave like a (read-only) dict. So this is a 'dict view' on top of an object, basically the opposite of `munch` (that is an 'object view' on top of a dict)

### 1.5.0 - Robustness and minor improvements

 * better error messages for set enforcers
 * uniform management of validators lists: now passing a list creates an 'and_' operator behind the scenes
 * better handling of empty lists
 * and, or, xor now automatically replace themselves with their contents when their contents is a single validator
 * added a few tests to improve coverage (hopefully)

### 1.4.3 - User-friendly validators error messages

* better validation error messages for parametrized validators

### 1.4.2 - Improved and documented validators

 * improved validators list documentation
 * added new validator: `and_`
 * fixed bugs in `or_`, `not_`, and `xor_` : since custom validators may now throw exceptions other than `ValidationError` and may return `None`, there was a need to update them to take these cases into account
 * `not_` may now be applied to a list of validators (implicit `and_`)
 * more unit tests for boolean validators

### 1.4.1 - Improved and documented validation feature 

 * A validator function may now return `None`
 * improved documentation on `@validate` in particular for custom validators implementation

### 1.4.0 - Added validation feature

 * New: `@validate` annotation allowing to implement input validation. Comes with a bunch of built-in validators.

### 1.3.1 - Documentation and Travis integration 2

 * Improved documentation
 * Automatic test report generation in travis
 * Automatic PyPI deployment on tags in travis

### 1.3.0 - Project renaming

 * `classtools-autocode` Project was renamed `autoclass` for clarity
 * Travis configuration was updated accordingly

### 1.2.0 - Performance and documentation

 * improved examples in the documentation
 * improved performance of var_checker (lessons learnt from parsyfiles)

### 1.1.0 - Mkdocs and enforce

 * now using mkdocs to generate the documentation from markdown
 * `@autoprops`: generated getters and setters now have correct PEP484 signature, which makes the library compliant with `enforce`
 * updated documentation accordingly
 
### 1.0.0 - First public working version with PyContracts
