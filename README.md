# pip-licenses

[![Build Status](https://travis-ci.org/raimon49/pip-licenses.svg?branch=master)](https://travis-ci.org/raimon49/pip-licenses) [![PyPI version](https://badge.fury.io/py/pip-licenses.svg)](https://badge.fury.io/py/pip-licenses) [![GitHub Release](https://img.shields.io/github/release/raimon49/pip-licenses.svg)](https://github.com/raimon49/pip-licenses/releases) [![Codecov](https://codecov.io/gh/raimon49/pip-licenses/branch/master/graph/badge.svg)](https://codecov.io/gh/raimon49/pip-licenses) [![BSD License](http://img.shields.io/badge/license-MIT-green.svg)](https://github.com/raimon49/pip-licenses/blob/master/LICENSE) [![Requirements Status](https://requires.io/github/raimon49/pip-licenses/requirements.svg?branch=master)](https://requires.io/github/raimon49/pip-licenses/requirements/?branch=master)

Dump the license list of packages installed with pip.

## Description

`pip-licenses` is a CLI tool for checking the software license of installed packages with pip.

Implemented with the idea inspired by `composer licenses` command in Composer (a.k.a PHP package management tool).

## Installation

Install it via PyPI using `pip` command.

```console
$ pip install pip-licenses
```

## Usage

Execute the command with your venv (or virtualenv) environment.

```console
# Install your venv environment
(venv) $ pip install Django pip-licenses

# Check the licenses
(venv) $ pip-licenses
 Name    Version  License
 Django  2.0.2    BSD
 pytz    2017.3   MIT
```
