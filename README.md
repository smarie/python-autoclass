# python-classtools-autocode

A python 3 library providing functions and decorators to automatically generate class code, such as **constructor body** or **properties getters/setters** along with optional support of **validation contracts** on the generated setters. 

The objective of this library is to reduce the amount of redundancy by automatically generatic parts of the code from the information already available somewhere else (typically, in the constructor signature). The intent is similar to [attrs](https://github.com/python-attrs/attrs): remove boilerplate.



## What's new

* Doc now generated from markdown using [mkdocs](http://www.mkdocs.org/)

## Want to contribute ?

Contributions are welcome ! Simply Fork this project on github, commit your contributions, and create pull requests.

Here is a non-exhaustive list of interesting open topics:

* Python 2 and < 3.5 compatibility
* Initial import of PyContract is quite slow (300ms on my machine). How to solve that, if that matters ?
* New annotations `@getters_wrapper(include, exclude)` and `@setters_wrapper(include, exclude)`, that would use `@contextmanager` or directly extend `GeneratorContextManager` in order to help users wrap all or part of the getters/setters with one function containing `yield`


## *Packaging*

This project uses `setuptools_scm` to synchronise the version number. Therefore the following command should be used for development snapshots as well as official releases: 

```bash
python setup.py egg_info bdist_wheel rotate -m.whl -k3
```