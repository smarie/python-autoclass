# Changelog

### 2.1.3 - Fixed DeprecationWarning

Fixed DeprecationWarning. Fixed [#35](https://github.com/smarie/python-autoclass/issues/35)

### 2.1.2 - bugfix

Fixed bug happening when `pyfields` is not installed. Fixed [#33](https://github.com/smarie/python-autoclass/issues/33).

### 2.1.1 - `pyproject.toml`

Added `pyproject.toml`.

### 2.1.0 - `@autoeq`

**Features**

 - Added independent `@autoeq`, supported in `@autoclass` and automatically activated when `autodict=False`. Fixed [#32](https://github.com/smarie/python-autoclass/issues/32).

**Bugfixes**

 - Fixed `@autorepr` when `only_known_fields` is `False`: now property names are correctly used instead of the private names.

 - Fixed `@autodict`'s generated `__eq__` method: when the other object is a dictionary a direct comparison is now done before trying super.

### 2.0.0 - `pyfields` support + major refactoring

**Features**

 - default string representation in `@autodict` is now more readable. Legacy representation is still available through a parameter. Fixed [#29](https://github.com/smarie/python-autoclass/issues/29).
 
 - `pyfields` can now be used as the source for the list of attributes, in `@autohash`, `@autodict`, and `@autoclass`. Fixes [#28](https://github.com/smarie/python-autoclass/issues/28)
 
 - new `@autorepr` decorator. Previously this feature was only available through `@autodict`, it can now be used without it. `autorepr` is supported in `@autoclass`, and if users set `autodict=False` by default it will be enabled. Fixed  Fixed [#30](https://github.com/smarie/python-autoclass/issues/30) and [#31](https://github.com/smarie/python-autoclass/issues/31).

**Misc / bugfixes**

 - Major refactoring: more readable and maintainable code.
 
 - Fixed `@autodict` behaviour when the list was `vars(self)` and used together with `@autoprops`: with some options the private names were appearing and with others the public property names were appearing. Now the public property names always appear if they exist.

### 1.18.0 - `@autoslots`

New `@autoslots` feature, that can also be used from `@autoclass` by setting `(autoslots=True)`. Fixes [#9](https://github.com/smarie/python-autoclass/issues/9)

### 1.17.2 - Added `__version__` attribute

Added `__version__` attribute at package level.

### 1.17.1 - Fixed bug with latest `valid8`

 * Fixed `ValidationError` happening in all use cases. Fixed [#25](https://github.com/smarie/python-autoclass/issues/25).

### 1.17.0 - Fixed `include`/`exclude` behaviour concerning property attributes

 * Names used in `include` and `exclude` are now correctly taken into account by `autodict` and `autohash` even if the names correspond to property names and therefore the actual attributes names start with an underscore. Fixes [#21](https://github.com/smarie/python-autoclass/issues/21)

### 1.16.0 - Python 2 support

 * This library now works on python 2.7, 3.5, 3.6 and 3.7. Fixes [#3](https://github.com/smarie/python-autoclass/issues/3).

### 1.15.1 - fixed valid8 exception message

 * Fixed [#24](https://github.com/smarie/python-autoclass/issues/24)

### 1.15.0 - more tolerance for inherited constructors

 * `autodict`, `autohash` and `autoprops` now tolerate inherited constructors

### 1.14.0 - submodule name changes

 * The submodule names were conflicting with the variable names: renamed them all
 * The init file has been improved so as not to export symbols from other packages. Fixes [#23](https://github.com/smarie/python-autoclass/issues/23)

### 1.13.0 - @autodict_override

 * New annotation `@autodict_override` that you can use to override `__iter__`, `__getitem__` or `__len__`. Fixes [#22](https://github.com/smarie/python-autoclass/issues/22)

### 1.12.0 - autodict fix

 * In case of inheritance, the order of attributes in now better and reproductible. Fixes [#20](https://github.com/smarie/python-autoclass/issues/20)
 * Printed representation created by @autodict now uses the same order than the generated keys iterator on the dictionary-faceted object.

### 1.11.0 - autodict fixes

 * `@autodict` does not add the `from_dict` class method anymore if this method already exists. If it does not already exist however, it is now always created (even if `only_constructor_args=False`)
 * inheritance is now handled more correctly (not perfect but it seems to handle more cases) with `@autodict`. Fixes [#19](https://github.com/smarie/python-autoclass/issues/19)

### 1.10.2 - minor bugfix

 * Fixed [#18](https://github.com/smarie/python-autoclass/issues/18)

### 1.10.1 - compatibility

 * Now compliant with old versions of `typing` module: `typing.Type` is not imported explicitly anymore.
 * tests updated with latest version of `valid8`

### 1.10.0 - bugfixes and updated doc

 * Updated documentation main page
 * `@autoargs` behaviour wrt keyword arguments changed. See usage page for details.
 * `include` and `exclude` parameters now support any kind of sequence, in all decorators
 * Bugfix: [Setter is called twice for default values](https://github.com/smarie/python-autoclass/issues/16)
 * Bugfix: [@autoprops argument name in setter is not correct](https://github.com/smarie/python-autoclass/issues/17)
 

### 1.9.2 - added autohash + fix

 * new annotation `@autohash`
 * The equality method `__eq__` generated by `@autodict` is now correct
 * `@autodict`: fixed consistency with default values of `only_public_fields`: it was False when using the individual decorator, but True when using @autoclass global decorator or the manual decoration method. Now it is True everywhere.

### 1.9.1 - a few fixes

 * Now compliant with valid8 2.0.0
 * Fixed #13: now generated setters have default values when it was the case on the constructor.

### 1.9.0 - valid8 is now an independent project

 * `Boolean`, `validate`, `validate_decorate` and all validators have been moved to an independent project, thus decoupling `autoclass` from the choice of validator library.

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
