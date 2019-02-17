# How to contribute

## Design policy

The design policy of pip-licenses is as follows.

* Focus only on outputting license information of Python packages installed in user's environment.
* Supports both Python 2.7 and 3.4 or later.
* External packages that depend on runtime are [PTable](https://pypi.org/project/PTable/) only.
    * Expect that pip and setuptools are implicitly installed.

## Setup

1. Create a new venv environment.
2. Install package for development via `make setup` .
    * Dependencies are managed by [pip-tools](https://pypi.org/project/pip-tools/).
    * If you want to add dependency packages for development, edit [dev-requirements.in](https://github.com/raimon49/pip-licenses/blob/master/dev-requirements.in) file and run `make update-depends` .

## Implementation and testing

* Code conventions follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/).
* pip-licenses always measures code coverage for code quality. If you implement the new feature, please also write unit test in [test\_piplicenses.py](https://github.com/raimon49/pip-licenses/blob/master/test_piplicenses.py).
    * Tests can be run with `make test` .
