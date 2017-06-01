[![Documentation Status](https://readthedocs.org/projects/classtools-autocode/badge/?version=latest)](http://classtools-autocode.readthedocs.io/en/latest/?badge=latest)

# python-classtools-autocode

Project page : [official](http://classtools-autocode.readthedocs.io), [backup](https://smarie.github.io/python-classtools-autocode/)

## What's new

* Doc now generated from markdown using [mkdocs](http://www.mkdocs.org/)

## Want to contribute ?

Contributions are welcome ! Simply fork this project on github, commit your contributions, and create pull requests.

Here is a non-exhaustive list of interesting open topics: https://github.com/smarie/python-classtools-autocode/issues

## Packaging

This project uses `setuptools_scm` to synchronise the version number. Therefore the following command should be used for development snapshots as well as official releases: 

```bash
python setup.py egg_info bdist_wheel rotate -m.whl -k3
```