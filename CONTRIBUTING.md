# How to contribute

## Design policy

The design policy of `pip-licenses` is as follows.

* Focus only on outputting license information of Python packages installed in user's environment.
* Support Python 3.9 or later.
* External packages that depend on runtime are [prettytable](https://pypi.org/project/prettytable/) and [tomli](https://pypi.org/project/tomli/) only.
    * Expect to be able to use [importlib\_metadata](https://importlib_metadata.readthedocs.io/) APIs.

## Setup

1. Fork this repository on your GitHub account.
2. Create a branch to represent changes.
    * Branch name does **NOT** need `feature/` prefix. Because git-flow is too complicated.
3. Create a new venv environment.
4. Install package for development via `make setup` .
    * Dependencies are managed by [pip-tools](https://pypi.org/project/pip-tools/).
    * If you want to add dependency packages for development, edit [dev-requirements.in](https://github.com/raimon49/pip-licenses/blob/master/dev-requirements.in) file and run `make update-depends` .
    * When you want to install the code under development, run `make local-install` .

## Implementation and testing

* `pip-licenses` always measures code coverage for code quality. If you implement the new feature, please also write unit test in [test\_piplicenses.py](https://github.com/raimon49/pip-licenses/blob/master/test_piplicenses.py).
    * Tests can be run with `make test` .
* Code conventions follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/).
    * You can format the code by running `make lint` .
* Send pull request to master branch.
