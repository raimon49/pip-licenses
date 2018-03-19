# pip-licenses

[![Build Status](https://travis-ci.org/raimon49/pip-licenses.svg?branch=master)](https://travis-ci.org/raimon49/pip-licenses) [![PyPI version](https://badge.fury.io/py/pip-licenses.svg)](https://badge.fury.io/py/pip-licenses) [![GitHub Release](https://img.shields.io/github/release/raimon49/pip-licenses.svg)](https://github.com/raimon49/pip-licenses/releases) [![Codecov](https://codecov.io/gh/raimon49/pip-licenses/branch/master/graph/badge.svg)](https://codecov.io/gh/raimon49/pip-licenses) [![BSD License](http://img.shields.io/badge/license-MIT-green.svg)](https://github.com/raimon49/pip-licenses/blob/master/LICENSE) [![Requirements Status](https://requires.io/github/raimon49/pip-licenses/requirements.svg?branch=master)](https://requires.io/github/raimon49/pip-licenses/requirements/?branch=master)

Dump the software license list of Python packages installed with pip.

## Table of Contents

* [Description](#description)
* [Installation](#installation)
* [Usage](#usage)
* [Command\-Line Options](#command-line-options)
    * [Option: from\-classifier](#option-from-classifier)
    * [Option: with\-system](#option-with-system)
    * [Option: with\-authors](#option-with-authors)
    * [Option: with\-urls](#option-with-urls)
    * [Option: ignore\-packages](#option-ignore-packages)
    * [Option: order](#option-order)
    * [Option: format\-markdown](#option-format-markdown)
    * [Option: format\-rst](#option-format-rst)
    * [Option: format\-confluence](#option-format-confluence)
    * [Option: format\-html](#option-format-html)
    * [More Information](#more-information)
* [License](#license)
    * [Dependencies](#dependencies)
* [Uninstallation](#uninstallation)

## Description

`pip-licenses` is a CLI tool for checking the software license of installed Python packages with pip.

Implemented with the idea inspired by `composer licenses` command in Composer (a.k.a PHP package management tool).

https://getcomposer.org/doc/03-cli.md#licenses

## Installation

Install it via PyPI using `pip` command.

```bash
# Install or Upgrade to newest available version
$ pip install -U pip-licenses
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

### Option: from-classifier

By default, this tool finds the license from package Metadata. However, depending on the type of package, it does not declare a license only in the Classifiers.

(See also): [Set license to MIT in setup.py by alisianoi ・ Pull Request #1058 ・ pypa/setuptools](https://github.com/pypa/setuptools/pull/1058), [PEP 314\#License](https://www.python.org/dev/peps/pep-0314/#license)

For example, even if you check with the `pip show` command, the license is displayed as `UNKNOWN`.

```bash
(venv) $ pip show setuptools
Name: setuptools
Version: 38.5.0
Summary: Easily download, build, install, upgrade, and uninstall Python packages
Home-page: https://github.com/pypa/setuptools
Author: Python Packaging Authority
Author-email: distutils-sig@python.org
License: UNKNOWN
```

If you want to refer to the license declared in [the Classifiers](https://pypi.python.org/pypi?%3Aaction=list_classifiers), use the `--from-classifier` option.

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

### Option: with-system

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

### Option: with-authors

When executed with the `--with-authors` option, output with author of the package.

```bash
(venv) $ pip-licenses --with-authors
 Name    Version  License  Author
 Django  2.0.2    BSD      Django Software Foundation
 pytz    2017.3   MIT      Stuart Bishop
```

### Option: with-urls

For packages without Metadata, the license is output as `UNKNOWN`. To get more package information, use the `--with-urls` option.

```bash
(venv) $ pip-licenses --with-urls
 Name    Version  License  URL
 Django  2.0.2    BSD      https://www.djangoproject.com/
 pytz    2017.3   MIT      http://pythonhosted.org/pytz
```

### Option: ignore-packages

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

### Option: order

By default, it is ordered by package name.

If you give arguments to the `--order` option, you can output in other sorted order.

```bash
(venv) $ pip-licenses --order=license
```

### Option: format-markdown

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

### Option: format-rst

When executed with the `--format-rst` option, you can output list in "[Grid tables](http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#grid-tables)" of reStructuredText format.

```bash
(venv) $ pip-licenses --format-rst
+--------+---------+---------+
| Name   | Version | License |
+--------+---------+---------+
| Django | 2.0.2   | BSD     |
+--------+---------+---------+
| pytz   | 2017.3  | MIT     |
+--------+---------+---------+
```

### Option: format-confluence

When executed with the `--format-confluence` option, you can output list in Confluence (or JIRA) Wiki markup format.

```bash
(venv) $ pip-licenses --format-confluence
| Name   | Version | License |
| Django | 2.0.2   | BSD     |
| pytz   | 2017.3  | MIT     |
```

### Option: format-html

When executed with the `--format-html` option, you can output list in HTML table format.

```bash
(venv) $ pip-licenses --format-html
<table>
    <tr>
        <th>Name</th>
        <th>Version</th>
        <th>License</th>
    </tr>
    <tr>
        <td>Django</td>
        <td>2.0.2</td>
        <td>BSD</td>
    </tr>
    <tr>
        <td>pytz</td>
        <td>2017.3</td>
        <td>MIT</td>
    </tr>
</table>
```

### More Information

Other, please make sure to execute the `--help` option.

## License

[MIT License](https://github.com/raimon49/pip-licenses/blob/master/LICENSE)

### Dependencies

* [PTable](https://pypi.python.org/pypi/PTable) by Luke Maurits and maintainer of fork version Kane Blueriver under the BSD-3-Clause License

`pip-licenses` has been implemented in the policy to minimize the dependence on external package.

## Uninstallation

Uninstall package and dependent package with `pip` command.

```bash
$ pip uninstall pip-licenses PTable
```
