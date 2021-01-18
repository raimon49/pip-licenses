# pip-licenses

[![Build Status](https://github.com/raimon49/pip-licenses/workflows/Python%20package/badge.svg)](https://github.com/raimon49/pip-licenses/actions?query=workflow%3A%22Python+package%22) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pip-licenses.svg)](https://pypi.org/project/pip-licenses/) [![PyPI version](https://badge.fury.io/py/pip-licenses.svg)](https://badge.fury.io/py/pip-licenses) [![GitHub Release](https://img.shields.io/github/release/raimon49/pip-licenses.svg)](https://github.com/raimon49/pip-licenses/releases) [![Codecov](https://codecov.io/gh/raimon49/pip-licenses/branch/master/graph/badge.svg)](https://codecov.io/gh/raimon49/pip-licenses) [![GitHub contributors](https://img.shields.io/github/contributors/raimon49/pip-licenses)](https://github.com/raimon49/pip-licenses/graphs/contributors) [![BSD License](http://img.shields.io/badge/license-MIT-green.svg)](https://github.com/raimon49/pip-licenses/blob/master/LICENSE) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pip-licenses)](https://pypistats.org/packages/pip-licenses) [![Requirements Status](https://requires.io/github/raimon49/pip-licenses/requirements.svg?branch=master)](https://requires.io/github/raimon49/pip-licenses/requirements/?branch=master)

Dump the software license list of Python packages installed with pip.

## Table of Contents

* [Description](#description)
* [Installation](#installation)
* [Usage](#usage)
* [Command\-Line Options](#command-line-options)
    * [Common options](#common-options)
        * [Option: from](#option-from)
        * [Option: order](#option-order)
        * [Option: format](#option-format)
            * [Markdown](#markdown)
            * [reST](#rest)
            * [Confluence](#confluence)
            * [HTML](#html)
            * [JSON](#json)
            * [JSON LicenseFinder](#json-licensefinder)
            * [CSV](#csv)
            * [Plain Vertical](#plain-vertical)
        * [Option: summary](#option-summary)
        * [Option: output\-file](#option-output-file)
        * [Option: ignore\-packages](#option-ignore-packages)
    * [Format options](#format-options)
        * [Option: with\-system](#option-with-system)
        * [Option: with\-authors](#option-with-authors)
        * [Option: with\-urls](#option-with-urls)
        * [Option: with\-description](#option-with-description)
        * [Option: with\-license\-file](#option-with-license-file)
        * [Option: filter\-strings](#option-filter-strings)
        * [Option: filter\-code\-page](#option-filter-code-page)
    * [Verify options](#verify-options)
        * [Option: fail\-on](#option-fail-on)
        * [Option: allow\-only](#option-allow-only)
    * [More Information](#more-information)
* [Dockerfile](#dockerfile)
* [About UnicodeEncodeError](#about-unicodeencodeerror)
* [License](#license)
    * [Dependencies](#dependencies)
* [Uninstallation](#uninstallation)
* [Contributing](#contributing)

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

**Note:** If you are still using Python 2.7, install version less than 2.0. No new features will be provided for version 1.x.

```bash
$ pip install 'pip-licenses<2.0'
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

### Common options

#### Option: from

By default, this tool finds the license from [Trove Classifiers](https://pypi.org/classifiers/) or package Metadata. Some Python packages declare their license only in Trove Classifiers.

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

The mixed mode (`--from=mixed`) of this tool works well and looks for licenses.

```bash
(venv) $ pip-licenses --from=mixed --with-system | grep setuptools
 setuptools    38.5.0   MIT License
```

In mixed mode, it first tries to look for licenses in the Trove Classifiers. When not found in the Trove Classifiers, the license declared in Metadata is displayed.

If you want to looks only in metadata, use `--from=meta`. If you want to looks only in Trove Classifiers, use `--from=classifier`.

To list license information from both metadata and classifier, use `--from=all`.

**Note:** If neither can find license information, please check with the `with-authors` and `with-urls` options and contact the software author.

* The `m` keyword is prepared as alias of `meta`.
* The `c` keyword is prepared as alias of `classifier`.
* The `mix` keyword is prepared as alias of `mixed`.
    * Default behavior in this tool

#### Option: order

By default, it is ordered by package name.

If you give arguments to the `--order` option, you can output in other sorted order.

```bash
(venv) $ pip-licenses --order=license
```

#### Option: format

By default, it is output to the `plain` format.

##### Markdown

When executed with the `--format=markdown` option, you can output list in markdown format. The `m` `md` keyword is prepared as alias of `markdown`.

```bash
(venv) $ pip-licenses --format=markdown
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

##### reST

When executed with the `--format=rst` option, you can output list in "[Grid tables](http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#grid-tables)" of reStructuredText format. The `r` `rest` keyword is prepared as alias of `rst`.

```bash
(venv) $ pip-licenses --format=rst
+--------+---------+---------+
| Name   | Version | License |
+--------+---------+---------+
| Django | 2.0.2   | BSD     |
+--------+---------+---------+
| pytz   | 2017.3  | MIT     |
+--------+---------+---------+
```

##### Confluence

When executed with the `--format=confluence` option, you can output list in [Confluence (or JIRA) Wiki markup](https://confluence.atlassian.com/doc/confluence-wiki-markup-251003035.html#ConfluenceWikiMarkup-Tables) format. The `c` keyword is prepared as alias of `confluence`.

```bash
(venv) $ pip-licenses --format=confluence
| Name   | Version | License |
| Django | 2.0.2   | BSD     |
| pytz   | 2017.3  | MIT     |
```

##### HTML

When executed with the `--format=html` option, you can output list in HTML table format. The `h` keyword is prepared as alias of `html`.

```bash
(venv) $ pip-licenses --format=html
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

##### JSON

When executed with the `--format=json` option, you can output list in JSON format easily allowing post-processing. The `j` keyword is prepared as alias of `json`.

```json
[
  {
    "Author": "Django Software Foundation",
    "License": "BSD",
    "Name": "Django",
    "URL": "https://www.djangoproject.com/",
    "Version": "2.0.2"
  },
  {
    "Author": "Stuart Bishop",
    "License": "MIT",
    "Name": "pytz",
    "URL": "http://pythonhosted.org/pytz",
    "Version": "2017.3"
  }
]
```

##### JSON LicenseFinder

When executed with the `--format=json-license-finder` option, you can output list in JSON format that is identical to [LicenseFinder](https://github.com/pivotal/LicenseFinder). The `jlf` keyword is prepared as alias of `jlf`.
This makes pip-licenses a drop-in replacement for LicenseFinder.

```json
[
  {
    "licenses": ["BSD"],
    "name": "Django",
    "version": "2.0.2"
  },
  {
    "licenses": ["MIT"],
    "name": "pytz",
    "version": "2017.3"
  }
]

```

##### CSV

When executed with the `--format=csv` option, you can output list in quoted CSV format. Useful when you want to copy/paste the output to an Excel sheet.

```bash
(venv) $ pip-licenses --format=csv
"Name","Version","License"
"Django","2.0.2","BSD"
"pytz","2017.3","MIT"
```

##### Plain Vertical

When executed with the `--format=plain-vertical` option, you can output a simple plain vertical output that is similar to Angular CLI's
[--extractLicenses flag](https://angular.io/cli/build#options). This format minimizes rightward drift.

```bash
(venv) $ pip-licenses --format=plain-vertical --with-license-file --no-license-path
pytest
5.3.4
MIT license
The MIT License (MIT)

Copyright (c) 2004-2020 Holger Krekel and others

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### Option: summary

When executed with the `--summary` option, you can output a summary of each license.

```bash
(venv) $ pip-licenses --summary --from=classifier --with-system
 Count  License
 2      BSD License
 4      MIT License
```

**Note:** When using this option, only `--order=count` or `--order=license` has an effect for the `--order` option. And using `--with-authors` and `--with-urls` will be ignored.

#### Option: output\-file

When executed with the `--output-file` option, write the result to the path specified by the argument.

```
(venv) $ pip-licenses --format=rst --output-file=/tmp/output.rst
created path: /tmp/output.rst
```

#### Option: ignore-packages

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


### Format options

#### Option: with-system

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

#### Option: with-authors

When executed with the `--with-authors` option, output with author of the package.

```bash
(venv) $ pip-licenses --with-authors
 Name    Version  License  Author
 Django  2.0.2    BSD      Django Software Foundation
 pytz    2017.3   MIT      Stuart Bishop
```

#### Option: with-urls

For packages without Metadata, the license is output as `UNKNOWN`. To get more package information, use the `--with-urls` option.

```bash
(venv) $ pip-licenses --with-urls
 Name    Version  License  URL
 Django  2.0.2    BSD      https://www.djangoproject.com/
 pytz    2017.3   MIT      http://pythonhosted.org/pytz
```

#### Option: with-description

When executed with the `--with-description` option, output with short description of the package.

```bash
(venv) $ pip-licenses --with-description
 Name    Version  License  Description
 Django  2.0.2    BSD      A high-level Python Web framework that encourages rapid development and clean, pragmatic design.
 pytz    2017.3   MIT      World timezone definitions, modern and historical
```

#### Option: with-license-file

When executed with the `--with-license-file` option, output the location of the package's license file on disk and the full contents of that file. Due to the length of these fields, this option is best paired with `--format=json`.

If you also want to output the file `NOTICE` distributed under Apache License etc., specify the `--with-notice-file` option additionally.

**Note:** If you want to keep the license file path secret, specify `--no-license-path` option together.

#### Option: filter\-strings

Some package data contains Unicode characters which might cause problems for certain output formats (in particular ReST tables). If this filter is enabled, all characters which cannot be encoded with a given code page (see `--filter-code-page`) will be removed from any input strings (e.g. package name, description).

#### Option: filter\-code\-page

If the input strings are filtered (see `--filter-strings`), you can specify the applied code page (default `latin-1`). A list of all available code pages can be found [codecs module document](https://docs.python.org/3/library/codecs.html#standard-encodings).


### Verify options

#### Option: fail\-on

Fail (exit with code 1) on the first occurrence of the licenses of the semicolon-separated list

If `--from=all`, the option will apply to the metadata license field.

```
(venv) $ pip-licenses --fail-on="MIT License;BSD License"
```
**Note:** When using this option, pip-licenses looks for an exact match. Packages with multiple licenses will only fail if that license combination is included in the list. For example:
```
# keyring library has 2 licenses, separated by a comma
$ pip-licenses | grep keyring
 keyring             21.4.0     Python Software Foundation License, MIT License

# If just "Python Software Foundation License" is specified, it will succeed.
$ pip-licenses --fail-on="Python Software Foundation License;"
$ echo $?
0

# Both licenses must be specified together.
$ pip-licenses --fail-on="Python Software Foundation License, MIT License;"
```

#### Option: allow\-only

Fail (exit with code 1) on the first occurrence of the licenses not in the semicolon-separated list

If `--from=all`, the option will apply to the metadata license field.

```
(venv) $ pip-licenses --allow-only="MIT License;BSD License"
```
**Note:** When using this option, pip-licenses looks for an exact match. Packages with multiple licenses will only be allowed if that license combination is included in the list. For example:
```
# keyring library has 2 licenses, separated by a comma
$ pip-licenses | grep keyring
 keyring             21.4.0     Python Software Foundation License, MIT License

# Both licenses must be specified together.
$ pip-licenses --allow-only="Python Software Foundation License, MIT License;"
```


### More Information

Other, please make sure to execute the `--help` option.

## Dockerfile

You can check the package license used by your app in the isolated Docker environment.

```bash
# Clone this repository to local
$ git clone https://github.com/raimon49/pip-licenses.git
$ cd pip-licenses

# Create your app's requirements.txt file
# Other ways, pip freeze > docker/requirements.txt
$ echo "Flask" > docker/requirements.txt

# Build docker image
$ docker build . -t myapp-licenses

# Check the package license in container
$ docker run --rm myapp-licenses
 Name          Version  License
 Click         7.0      BSD License
 Flask         1.0.2    BSD License
 Jinja2        2.10     BSD License
 MarkupSafe    1.1.1    BSD License
 Werkzeug      0.15.2   BSD License
 itsdangerous  1.1.0    BSD License

# Check with options
$ docker run --rm myapp-licenses --summary
 Count  License
 4      BSD
 2      BSD-3-Clause

# When you need help
$ docker run --rm myapp-licenses --help
```

**Note:** This Docker image can not check package licenses with C and C ++ Extensions. It only works with pure Python package dependencies.

If you want to resolve build environment issues, try adding `build-base` packages and more.

```diff
--- a/Dockerfile
+++ b/Dockerfile
@@ -7,6 +7,8 @@ WORKDIR ${APPDIR}

 COPY ./docker/requirements.txt ${APPDIR}

+RUN set -ex && apk add --no-cache --update --virtual .py-deps \
+        build-base
 RUN python3 -m venv ${APPDIR}/myapp \
         && source ${APPDIR}/myapp/bin/activate
```

## About UnicodeEncodeError

If a `UnicodeEncodeError` occurs, check your environment variables `LANG` and `LC_TYPE`.

Often occurs in isolated environments such as Docker and tox.

See useful reports:

* [#35](https://github.com/raimon49/pip-licenses/issues/35)
* [#45](https://github.com/raimon49/pip-licenses/issues/45)

## License

[MIT License](https://github.com/raimon49/pip-licenses/blob/master/LICENSE)

### Dependencies

* [PTable](https://pypi.org/project/PTable/) by Luke Maurits and maintainer of fork version Kane Blueriver under the BSD-3-Clause License
    * **Note:** Alternatively, it works fine with the [PrettyTable](https://pypi.org/project/PrettyTable/) package. (See also): [Allow using prettytable #52](https://github.com/raimon49/pip-licenses/pull/52)

`pip-licenses` has been implemented in the policy to minimize the dependence on external package.

## Uninstallation

Uninstall package and dependent package with `pip` command.

```bash
$ pip uninstall pip-licenses PTable
```

## Contributing

See [contribution guidelines](https://github.com/raimon49/pip-licenses/blob/master/CONTRIBUTING.md).
