# pip-licenses

[![Build Status](https://travis-ci.org/raimon49/pip-licenses.svg?branch=master)](https://travis-ci.org/raimon49/pip-licenses) [![PyPI version](https://badge.fury.io/py/pip-licenses.svg)](https://badge.fury.io/py/pip-licenses) [![GitHub Release](https://img.shields.io/github/release/raimon49/pip-licenses.svg)](https://github.com/raimon49/pip-licenses/releases) [![Codecov](https://codecov.io/gh/raimon49/pip-licenses/branch/master/graph/badge.svg)](https://codecov.io/gh/raimon49/pip-licenses) [![BSD License](http://img.shields.io/badge/license-MIT-green.svg)](https://github.com/raimon49/pip-licenses/blob/master/LICENSE) [![Requirements Status](https://requires.io/github/raimon49/pip-licenses/requirements.svg?branch=master)](https://requires.io/github/raimon49/pip-licenses/requirements/?branch=master)

Dump the license list of packages installed with pip.

Table of Contents
=================

* [Description](#description)
* [Installation](#installation)
* [Usage](#usage)
* [Command\-Line Options](#command-line-options)
    * [\-\-with\-system](#--with-system)
    * [\-\-with\-authors](#--with-authors)
    * [\-\-with\-urls](#--with-urls)
    * [\-\-order](#--order)
    * [More Information](#more-information)
* [License](#license)
    * [Dependencies](#dependencies)

## Description

`pip-licenses` is a CLI tool for checking the software license of installed packages with pip.

Implemented with the idea inspired by `composer licenses` command in Composer (a.k.a PHP package management tool).

https://getcomposer.org/doc/03-cli.md#licenses

## Installation

Install it via PyPI using `pip` command.

```bash
$ pip install pip-licenses
```

## Usage

Execute the command with your venv (or virtualenv) environment.

```bash
# Install packages in your venv environment
(venv) $ pip install Django pip-licenses

# Check the licenses with your venv environment
(venv) $ pip-licenses
 Name    Version  License
 Django  2.0.2    BSD
 pytz    2017.3   MIT
```

## Command-Line Options

### --with-system

By default, system packages such as pip and setuptools are ignored.

If you want to output all including system package, use the `--with-system` option.

```bash
(venv) $ pip-licenses --with-system
 Name          Version  License
 Django        2.0.2    BSD
 PTable        0.9.2    BSD (3 clause)
 pip           9.0.1    MIT
 pip-licenses  1.0.0    MIT License
 pytz          2017.3   MIT
 setuptools    38.5.0   UNKNOWN
```

### --with-authors

When executed with the `--with-authors` option, output with author of the package.

```bash
(venv) $ pip-licenses --with-authors
 Name    Version  License  Author
 Django  2.0.2    BSD      Django Software Foundation
 pytz    2017.3   MIT      Stuart Bishop
```

### --with-urls

For packages without METADATA, the license is output as `UNKNOWN`. To get more package information, use the `--with-urls` option.

```bash
(venv) $ pip-licenses --with-urls
 Name    Version  License  URL
 Django  2.0.2    BSD      https://www.djangoproject.com/
 pytz    2017.3   MIT      http://pythonhosted.org/pytz
```

### --order

By default, it is ordered by package name.

If you give arguments to the `--order option`, you can output in other sorted order.

```bash
(venv) $ pip-licenses --order=license
```

### More Information

Other, please make sure to execute the `--help` option.

## License

[MIT License](https://github.com/raimon49/pip-licenses/blob/master/LICENSE)

### Dependencies

* [PTable](https://pypi.python.org/pypi/PTable) by Luke Maurits and maintainer of fork version Kane Blueriver under the BSD-3-Clause license
