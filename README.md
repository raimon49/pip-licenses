# pip-licenses

[![Build Status](https://travis-ci.org/raimon49/pip-licenses.svg?branch=master)](https://travis-ci.org/raimon49/pip-licenses) [![PyPI version](https://badge.fury.io/py/pip-licenses.svg)](https://badge.fury.io/py/pip-licenses) [![GitHub Release](https://img.shields.io/github/release/raimon49/pip-licenses.svg)](https://github.com/raimon49/pip-licenses/releases) [![Codecov](https://codecov.io/gh/raimon49/pip-licenses/branch/master/graph/badge.svg)](https://codecov.io/gh/raimon49/pip-licenses) [![BSD License](http://img.shields.io/badge/license-MIT-green.svg)](https://github.com/raimon49/pip-licenses/blob/master/LICENSE) [![Requirements Status](https://requires.io/github/raimon49/pip-licenses/requirements.svg?branch=master)](https://requires.io/github/raimon49/pip-licenses/requirements/?branch=master)

Dump the software license list of Python packages installed with pip.

## Table of Contents

* [Description](#description)
* [Installation](#installation)
* [Usage](#usage)
* [Command\-Line Options](#command-line-options)
    * [\-\-from\-classifier](#--from-classifier)
    * [\-\-with\-system](#--with-system)
    * [\-\-with\-authors](#--with-authors)
    * [\-\-with\-urls](#--with-urls)
    * [\-\-ignore\-packages](#--ignore-packages)
    * [\-\-order](#--order)
    * [\-\-format\-markdown](#--format-markdown)
    * [More Information](#more-information)
* [License](#license)
    * [Dependencies](#dependencies)

## Description

`pip-licenses` is a CLI tool for checking the software license of installed Python packages with pip.

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

### --from-classifier

By default, this tool finds the license from package Metadata. However, depending on the type of package, it does not declare a license only in the Classifiers.

(See also): [Set license to MIT in setup.py by alisianoi ・ Pull Request #1058 ・ pypa/setuptools](https://github.com/pypa/setuptools/pull/1058), [PEP 314\#License](https://www.python.org/dev/peps/pep-0314/#license)

If you want to refer to the license declared in Classifiers, use the `--from-classifier` option.

```bash
(venv) $ pip-licenses --from-classifier --with-system
 Name          Version  License
 Django        2.0.2    BSD License
 PTable        0.9.2    BSD License
 pip           9.0.1    MIT License
 pip-licenses  1.0.0    MIT License
 pytz          2017.3   MIT License
 setuptools    38.5.0   MIT License
```

### --with-system

By default, system packages such as `pip` and `setuptools` are ignored.

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

For packages without Metadata, the license is output as `UNKNOWN`. To get more package information, use the `--with-urls` option.

```bash
(venv) $ pip-licenses --with-urls
 Name    Version  License  URL
 Django  2.0.2    BSD      https://www.djangoproject.com/
 pytz    2017.3   MIT      http://pythonhosted.org/pytz
```

### --ignore-packages

When executed with the `--ignore-packages` option, ignore the package specified by argument from list output.

```bash
(venv) $ pip-licenses --ignore-packages django
 Name  Version  License
 pytz  2017.3   MIT
```

Package names of arguments can be separated by spaces.

```bash
(venv) $ pip-licenses --with-system --ignore-packages django pip pip-licenses
 Name        Version  License
 PTable      0.9.2    BSD (3 clause)
 pytz        2017.3   MIT
 setuptools  38.5.0   UNKNOWN
```

### --order

By default, it is ordered by package name.

If you give arguments to the `--order option`, you can output in other sorted order.

```bash
(venv) $ pip-licenses --order=license
```

### --format-markdown

When executed with the `--format-markdown` option, you can output list in markdown format.

```bash
(venv) $ pip-licenses --format-markdown
| Name   | Version | License |
|--------|---------|---------|
| Django | 2.0.2   | BSD     |
| pytz   | 2017.3  | MIT     |
```

When inserted in a markdown document, it is rendered as follows:

| Name   | Version | License |
|--------|---------|---------|
| Django | 2.0.2   | BSD     |
| pytz   | 2017.3  | MIT     |

### More Information

Other, please make sure to execute the `--help` option.

## License

[MIT License](https://github.com/raimon49/pip-licenses/blob/master/LICENSE)

### Dependencies

* [PTable](https://pypi.python.org/pypi/PTable) by Luke Maurits and maintainer of fork version Kane Blueriver under the BSD-3-Clause License

`pip-licenses` has been implemented in the policy to minimize the dependence on external package.
