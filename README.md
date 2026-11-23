# pip-licenses

[![Build Status](https://github.com/raimon49/pip-licenses/workflows/Python%20package/badge.svg)](https://github.com/raimon49/pip-licenses/actions?query=workflow%3A%22Python+package%22) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pip-licenses.svg)](https://pypi.org/project/pip-licenses/) [![PyPI version](https://badge.fury.io/py/pip-licenses.svg)](https://badge.fury.io/py/pip-licenses) [![GitHub Release](https://img.shields.io/github/release/raimon49/pip-licenses.svg)](https://github.com/raimon49/pip-licenses/releases) [![Codecov](https://codecov.io/gh/raimon49/pip-licenses/branch/master/graph/badge.svg)](https://codecov.io/gh/raimon49/pip-licenses) [![GitHub contributors](https://img.shields.io/github/contributors/raimon49/pip-licenses)](https://github.com/raimon49/pip-licenses/graphs/contributors) [![MIT License](http://img.shields.io/badge/license-MIT-green.svg)](https://github.com/raimon49/pip-licenses/blob/master/LICENSE) [![PyPI - Downloads](https://img.shields.io/pypi/dm/pip-licenses)](https://pypistats.org/packages/pip-licenses)

Dump the software license list of Python packages installed with pip.

> [!IMPORTANT]
> ## Version 6 series is coming soon
>
> The [next](https://github.com/raimon49/pip-licenses/tree/next) version will bring breaking changes!
> You may notice documentation has begun to describe the version `6`-series already. A living
> document to assist with migrating to the v`6`-series is now available, while some of the
> more custodial work wraps up for the release of the v`6.0.0` release in December 2026.
>
> [v6 Migration Document](https://github.com/raimon49/pip-licenses/wiki/Migration-Guide-(v5.4–v5.5-→-v6.x)-(DRAFT)#support-and-release-notes)

<img width="785" height="265" alt="demo_preview" src="https://github.com/user-attachments/assets/910cae21-dd6e-4ee3-9861-171b7c454dc6" />

<details><summary>Table of Contents</summary>

* [Description](#description)
* [Installation](#installation)
* [Usage](#usage)
* [Command\-Line Options](#command-line-options)
    * [Common options](#common-options)
        * [Option: python](#option-python)
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
        * [Option: packages](#option-packages)
    * [Format options](#format-options)
        * [Option: with\-system](#option-with-system)
        * [Option: with\-authors](#option-with-authors)
        * [Option: with\-maintainers](#option-with-maintainers)
        * [Option: with\-urls](#option-with-urls)
        * [Option: with\-description](#option-with-description)
        * [Option: no\-version](#option-no-version)
        * [Option: with\-license\-file](#option-with-license-file)
        * [Option: filter\-strings](#option-filter-strings)
        * [Option: filter\-code\-page](#option-filter-code-page)
    * [Verify options](#verify-options)
        * [Option: fail\-on](#option-fail-on)
        * [Option: warn\-on](#option-warn-on)
        * [Option: allow\-only](#option-allow-only)
        * [Option: partial\-match](#option-partial-match)
    * [pyproject.toml support](#pyprojecttoml-support)
    * [More Information](#more-information)
* [Dockerfile](#dockerfile)
* [About UnicodeEncodeError](#about-unicodeencodeerror)
* [License](#license)
    * [Dependencies](#dependencies)
* [Uninstallation](#uninstallation)
* [Contributing](#contributing)

</details>

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

<details>
<summary>Legacy Python Hints</summary>

**Note for Python 3.8 users:** pip-licenses 5.x discontinued support for Python 3.8. If you want to use it with Python 3.8 anyway, install pip-licenses 4.5.x.

```bash
# Using old version for the Python 3.8 environment
$ pip install 'pip-licenses<5.0'

# If upgrading from pip-licenses 3.x, remove PTable
$ pip uninstall -y PTable
```

**Note for Python 3.7 users:** pip-licenses 4.x discontinued support earlier than the Python 3.7 EOL schedule. If you want to use it with Python 3.7, install pip-licenses 3.x.

```bash
# Using old version for the Python 3.7 environment
$ pip install 'pip-licenses<4.0'
```

**Note:** If you are still using Python 2.7, install version less than 2.0. No new features will be provided for version 1.x.

```bash
$ pip install 'pip-licenses<2.0'
```

</details>

## Usage

Simply invoke the command to scan the current environment:

`pip-licenses`

[Example 01](./docs/examples/01-basic/01-basic-usage.md)

```console
demo$ pip-licenses
 Name       Version  License                    
 cffi       2.1.1    MIT-0                      
 packaging  26.3     Apache-2.0 OR BSD-2-Clause 
 pycparser  3.0      BSD-3-Clause               


```

> [!TIP]
> Alternatively execute the command within `virtualenv` (or the legacy `venv`) environment.

## Command-Line Options

### Common options

| Option | Argument(s) | Default | Description |
| --- | --- | --- | --- |
| `--python` | path | current interpreter | Python executable whose `sys.path` is searched for packages. |
| `--from` | `meta`, `classifier`, `mixed`, `all` | `mixed` | Source used to look up license information. |
| `--order` | `name`, `license`, `author`, `url`, `count` | `name` | Column used to sort the output. |
| `--format` | `plain`, `plain-vertical`, `markdown`, `rst`, `confluence`, `html`, `json`, `json-license-finder`, `csv` | `plain` | Output format of the report. |
| `--summary` | None (_flag takes no values_) | off | Output a count summary per license instead of a package list. |
| `--output-file` | path | stdout | Write the result to the given file path. |
| `--ignore-packages` | package names | none | Exclude the listed packages from the output. |
| `--packages` | package names | all | Limit the output to the listed packages only. |

#### Option: python

By default, this tools finds the packages from the environment pip-licenses is launched from, by searching in current python's `sys.path` folders. In the case you want to search for packages in an other environment (e.g. if you want to run pip-licenses from its own isolated environment), you can specify a path to a python executable. The packages will be searched for in the given python's `sys.path`, free of pip-licenses dependencies.

[Example 56](./docs/examples/50-option-packages/56-option-packages-system.md)

```console
demo$ pip-licenses --with-system | grep pip 
 pip           26.3      MIT                        
 pip-licenses  6.0.0rc24 MIT                        


```

```bash
(venv) $ pip-licenses --python=</path/to/other/env>/bin/python --with-system | grep pip
 pip           26.3     MIT
```

#### Option: from

By default, this tool finds the license from [Trove Classifiers](https://pypi.org/classifiers/) or package Metadata. Some Python packages declare their license only in Trove Classifiers.

(See also): [Set license to MIT in setup.py by alisianoi ・ Pull Request #1058 ・ pypa/setuptools](https://github.com/pypa/setuptools/pull/1058), [PEP 314\#License](https://www.python.org/dev/peps/pep-0314/#license)

For example, even if you check with the `pip show` command, the license is displayed as `UNKNOWN` or simply empty.

[Example 32](./docs/examples/30-option/32-option-from-mixed.md)

```console
demo$ # this is what pip shows: 

demo$ pip show aniso8601
Name: aniso8601
Version: 10.0.1
Summary: A library for parsing ISO 8601 strings.
Home-page: https://codeberg.org/nielsenb-jf/aniso8601
Author: Brandon Nielsen
Author-email: nielsenb@jetfuse.net
License: 
Requires: 
Required-by: 

demo$ # this is what pip-licenses shows: 

demo$ pip-licenses -p aniso8601 --from=mixed --with-system 
 Name       Version  License     
 aniso8601  10.0.1   BSD License 


```

The mixed mode (`--from=mixed`) of this tool works well and looks for licenses.

In mixed mode, it first tries to look for licenses in the Trove Classifiers. When not found in the Trove Classifiers, the license declared in Metadata is displayed.

If you want to look only in metadata, use `--from=meta`. If you want to look only in Trove Classifiers, use `--from=classifier`.

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

[Example 20](./docs/examples/20-format/20-format-markdown.md)

```console
demo$ pip-licenses --format=markdown 
| Name              | Version | License                    |
|-------------------|---------|----------------------------|
| aniso8601         | 10.0.1  | BSD License                |
| cffi              | 2.1.1   | MIT-0                      |
| dependency-groups | 1.3.2   | MIT                        |
| packaging         | 26.3    | Apache-2.0 OR BSD-2-Clause |
| pycparser         | 3.12    | BSD-3-Clause               |


```

When inserted in a markdown document, it is rendered as follows:

| Name              | Version | License                    |
|-------------------|---------|----------------------------|
| aniso8601         | 10.0.1  | BSD License                |
| cffi              | 2.1.1   | MIT-0                      |
| dependency-groups | 1.3.2   | MIT                        |
| packaging         | 26.3    | Apache-2.0 OR BSD-2-Clause |
| pycparser         | 3.12    | BSD-3-Clause               |

When executed with the `--format=rst` option, you can output list in "[Grid tables](http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#grid-tables)" of reStructuredText format. The `r` `rest` keyword is prepared as alias of `rst`.

[Example 21](./docs/examples/20-format/21-format-rst.md)

```console
demo$ pip-licenses --format=rst 
+-------------------+---------+----------------------------+
| Name              | Version | License                    |
+-------------------+---------+----------------------------+
| aniso8601         | 10.0.1  | BSD License                |
+-------------------+---------+----------------------------+
| cffi              | 2.1.1   | MIT-0                      |
+-------------------+---------+----------------------------+
| dependency-groups | 1.3.2   | MIT                        |
+-------------------+---------+----------------------------+
| packaging         | 26.3    | Apache-2.0 OR BSD-2-Clause |
+-------------------+---------+----------------------------+
| pycparser         | 3.12    | BSD-3-Clause               |
+-------------------+---------+----------------------------+


```

##### Confluence

When executed with the `--format=confluence` option, you can output list in [Confluence (or JIRA) Wiki markup](https://confluence.atlassian.com/doc/confluence-wiki-markup-251003035.html#ConfluenceWikiMarkup-Tables) format. The `c` keyword is prepared as alias of `confluence`.

[Example 22](./docs/examples/20-format/22-format-confluence.md)

```console
demo$ pip-licenses --format=confluence 
| Name              | Version | License                    |
| aniso8601         | 10.0.1  | BSD License                |
| cffi              | 2.1.1   | MIT-0                      |
| dependency-groups | 1.3.2   | MIT                        |
| packaging         | 26.3    | Apache-2.0 OR BSD-2-Clause |
| pycparser         | 3.12    | BSD-3-Clause               |


```

##### HTML

When executed with the `--format=html` option, you can output list in HTML table format. The `h` keyword is prepared as alias of `html`.

[Example 23](./docs/examples/20-format/23-format-html.md)

```console
demo$ pip-licenses --format=html 
<table id="pipl_tbl_3657857384001fcf17695fbdc591f6577e87ebe58b83277bb4a1c494b0380308" class="pip_licenses_table">
    <thead>
        <tr>
            <th>Name</th>
            <th>Version</th>
            <th>License</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>aniso8601</td>
            <td>10.0.1</td>
            <td>BSD License</td>
        </tr>
        <tr>
            <td>cffi</td>
            <td>2.1.1</td>
            <td>MIT-0</td>
        </tr>
        <tr>
            <td>dependency-groups</td>
            <td>1.3.2</td>
            <td>MIT</td>
        </tr>
        <tr>
            <td>packaging</td>
            <td>26.3</td>
            <td>Apache-2.0 OR BSD-2-Clause</td>
        </tr>
        <tr>
            <td>pycparser</td>
            <td>3.12</td>
            <td>BSD-3-Clause</td>
        </tr>
    </tbody>
</table>


```

##### JSON

When executed with the `--format=json` option, you can output list in JSON format easily allowing post-processing. The `j` keyword is prepared as alias of `json`.

[Example 24](./docs/examples/20-format/24-format-json.md)

```console
demo$ pip-licenses --format=json --with-urls --with-authors 
[
  {
    "Author": [
      "Brandon Nielsen",
      "nielsenb@jetfuse.net"
    ],
    "License": "BSD License",
    "Name": "aniso8601",
    "URL": "https://codeberg.org/nielsenb-jf/aniso8601",
    "Version": "10.0.1"
  },
  {
    "Author": [
      "Armin Rigo, Maciej Fijalkowski"
    ],
    "License": "MIT-0",
    "Name": "cffi",
    "URL": "https://cffi.readthedocs.io/en/latest/whatsnew.html",
    "Version": "2.1.1"
  },
  {
    "Author": [
      "Stephen Rosen"
    ],
    "License": "MIT",
    "Name": "dependency-groups",
    "URL": "https://github.com/pypa/dependency-groups",
    "Version": "1.3.2"
  },
  {
    "Author": [
      "Donald Stufft"
    ],
    "License": "Apache-2.0 OR BSD-2-Clause",
    "Name": "packaging",
    "URL": "https://github.com/pypa/packaging",
    "Version": "26.3"
  },
  {
    "Author": [
      "Eli Bendersky"
    ],
    "License": "BSD-3-Clause",
    "Name": "pycparser",
    "URL": "https://github.com/eliben/pycparser",
    "Version": "3.12"
  }
]


```

##### JSON LicenseFinder

When executed with the `--format=json-license-finder` option, you can output list in JSON format that is identical to [LicenseFinder](https://github.com/pivotal/LicenseFinder). The `jlf` keyword is prepared as alias of `jlf`.
This makes pip-licenses a drop-in replacement for LicenseFinder.

[Example 25](./docs/examples/20-format/25-format-json-licensefinder.md)

```console
demo$ pip-licenses --format=json-license-finder 
[{"licenses": ["BSD License"], "name": "aniso8601", "version": "10.0.1"}, {"licenses": ["MIT-0"], "name": "cffi", "version": "2.1.1"}, {"licenses": ["MIT"], "name": "dependency-groups", "version": "1.3.2"}, {"licenses": ["Apache-2.0 OR BSD-2-Clause"], "name": "packaging", "version": "26.3"}, {"licenses": ["BSD-3-Clause"], "name": "pycparser", "version": "3.12"}]


```

##### CSV

When executed with the `--format=csv` option, you can output list in quoted CSV format. Useful when you want to copy/paste the output to an Excel sheet.

[Example 26](./docs/examples/20-format/26-format-csv.md)

```console
demo$ pip-licenses --format=csv 
"Name","Version","License"
"aniso8601","10.0.1","BSD License"
"cffi","2.1.1","MIT-0"
"dependency-groups","1.3.2","MIT"
"packaging","26.3","Apache-2.0 OR BSD-2-Clause"
"pycparser","3.12","BSD-3-Clause"


```

##### Plain Vertical

When executed with the `--format=plain-vertical` option, you can output a simple plain vertical output that is similar to Angular CLI's
[--extractLicenses flag](https://angular.io/cli/build#options). This format minimizes rightward drift.

[Example 27](./docs/examples/20-format/27-format-plain-vertical.md)

```console
demo$ pip-licenses --packages cffi --format=plain-vertical --with-license-files --no-license-path 
cffi
2.1.1
MIT-0

Except when otherwise stated (look for LICENSE files in directories or
information at the beginning of each file) all software and
documentation is licensed as follows: 

    MIT No Attribution

    Permission is hereby granted, free of charge, to any person 
    obtaining a copy of this software and associated documentation 
    files (the "Software"), to deal in the Software without 
    restriction, including without limitation the rights to use, 
    copy, modify, merge, publish, distribute, sublicense, and/or 
    sell copies of the Software, and to permit persons to whom the 
    Software is furnished to do so.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
    DEALINGS IN THE SOFTWARE.






```

#### Option: summary

When executed with the `--summary` option, you can output a summary of each license.

[Example 30](./docs/examples/30-option/30-option-summary.md)

```console
demo$ pip-licenses --summary --include-system 
 Count  License                    
 1      Apache-2.0 OR BSD-2-Clause 
 1      BSD License                
 2      BSD-3-Clause               
 3      MIT                        
 1      MIT License                
 1      MIT-0                      


```

**Note:** When using this option, only `--order=count` or `--order=license` has an effect for the `--order` option. And using `--with-authors` and `--with-urls` will be ignored.

#### Option: output\-file

When executed with the `--output-file` option, write the result to the path specified by the argument.

[Example 31](./docs/examples/30-option/31-option-output-file.md)

```console
demo$ pip-licenses --format=rst --output-file="/var/folders/cl/sgmjy2fj4p5fz5nctcypkf2c0000gp/T/tmp.2OwIjz9YGk/output.rst" 
created path: /var/folders/cl/sgmjy2fj4p5fz5nctcypkf2c0000gp/T/tmp.2OwIjz9YGk/output.rst

demo$ cat "/var/folders/cl/sgmjy2fj4p5fz5nctcypkf2c0000gp/T/tmp.2OwIjz9YGk/output.rst" 
+-------------------+---------+----------------------------+
| Name              | Version | License                    |
+-------------------+---------+----------------------------+
| aniso8601         | 10.0.1  | BSD License                |
+-------------------+---------+----------------------------+
| cffi              | 2.1.1   | MIT-0                      |
+-------------------+---------+----------------------------+
| dependency-groups | 1.3.2   | MIT                        |
+-------------------+---------+----------------------------+
| packaging         | 26.3    | Apache-2.0 OR BSD-2-Clause |
+-------------------+---------+----------------------------+
| pycparser         | 3.12    | BSD-3-Clause               |
+-------------------+---------+----------------------------+


```


#### Option: ignore-packages

When executed with the `--ignore-packages` option, ignore the package specified by argument from list output.

[Example 40](./docs/examples/40-option-ignore/40-option-ignore-single.md)

```console
demo$ pip-licenses --ignore-packages cffi 
 Name               Version  License                    
 aniso8601          10.0.1   BSD License                
 dependency-groups  1.3.2    MIT                        
 packaging          26.3     Apache-2.0 OR BSD-2-Clause 
 pycparser          3.12     BSD-3-Clause               


```

Package names of arguments can be separated by spaces.

[Example 41](./docs/examples/40-option-ignore/41-option-ignore-multiple.md)

```console
demo$ pip-licenses --with-system --ignore-packages cffi pip pip-licenses 
 Name               Version  License                    
 aniso8601          10.0.1   BSD License                
 dependency-groups  1.3.2    MIT                        
 packaging          26.3     Apache-2.0 OR BSD-2-Clause 
 prettytable        3.19.0   BSD-3-Clause               
 pycparser          3.12     BSD-3-Clause               
 wcwidth            0.9.5    MIT License                


```

Packages can also be specified with a version, only ignoring that specific version.

[Example 42](./docs/examples/40-option-ignore/42-option-ignore-with-version.md)

```console
demo$ pip-licenses --with-system --ignore-packages cffi packaging:26.3 
 Name               Version    License      
 aniso8601          10.0.1     BSD License  
 dependency-groups  1.3.2      MIT          
 pip                26.3       MIT          
 pip-licenses       6.0.0rc24  MIT          
 prettytable        3.19.0     BSD-3-Clause 
 pycparser          3.12       BSD-3-Clause 
 wcwidth            0.9.5      MIT License  


```

#### Option: packages

When executed with the `packages` option, look at the package specified by argument from list output.

[Example 50](./docs/examples/50-option-packages/50-option-packages-single.md)

```console
demo$ pip-licenses --packages cffi 
 Name  Version  License 
 cffi  2.1.1    MIT-0   


```

Package names of arguments can be separated by spaces.

[Example 51](./docs/examples/50-option-packages/51-option-packages-multiple.md)

```console
demo$ pip-licenses --with-system --packages prettytable packaging 
 Name         Version  License                    
 packaging    26.3     Apache-2.0 OR BSD-2-Clause 
 prettytable  3.19.0   BSD-3-Clause               


```

### Format options

#### Option: with-system

By default, a few common system packages such as `pip`, `setuptools`, and `wheel` are ignored.

Further, `pip-licenses` and the implicit dependencies `prettytable` and `wcwidth` will also be ignored.

If you want to output _all_, including system packages, use the `--with-system` option.

[Example 56](./docs/examples/50-option-packages/56-option-packages-system.md)

```console
demo$ pip-licenses --with-system | grep pip 
 pip                26.3       MIT                        
 pip-licenses       6.0.0rc24  MIT                        


```

> [!TIP]
> ##### Configure by default
> It is also possible to configure `pip-licenses` (as of v6.0.0rc23) to include system packages
> via the configuration overrides. To do this include the following in your `pyproject.toml`
> ```toml
>     [tools.pip-licenses]
>     include_from_system = true
> ```

#### Option: with-authors

When executed with the `--with-authors` option, output with author of the package.

[Example 61](./docs/examples/60-format-with/61-format-with-authors.md)

```console
demo$ pip-licenses --with-authors 
 Name               Version  License                     Author                                      
 aniso8601          10.0.1   BSD License                 ['Brandon Nielsen', 'nielsenb@jetfuse.net'] 
 cffi               2.1.1    MIT-0                       ['Armin Rigo, Maciej Fijalkowski']          
 dependency-groups  1.3.2    MIT                         ['Stephen Rosen']                           
 packaging          26.3     Apache-2.0 OR BSD-2-Clause  ['Donald Stufft']                           
 pycparser          3.12     BSD-3-Clause                ['Eli Bendersky']                           


```

#### Option: with-maintainers

When executed with the `--with-maintainers` option, output with maintainer of the package.

**Note:** This option is available for users who want information about the maintainer as well as the author. See [#144](https://github.com/raimon49/pip-licenses/issues/144)

#### Option: with-urls

For packages without Metadata, the license is output as `UNKNOWN`. To get more package information, use the `--with-urls` option.

[Example 62](./docs/examples/60-format-with/62-format-with-urls.md)

```console
demo$ pip-licenses --with-urls 
 Name               Version  License                     URL                                                 
 aniso8601          10.0.1   BSD License                 https://codeberg.org/nielsenb-jf/aniso8601          
 cffi               2.1.1    MIT-0                       https://cffi.readthedocs.io/en/latest/whatsnew.html 
 dependency-groups  1.3.2    MIT                         https://github.com/pypa/dependency-groups           
 packaging          26.3     Apache-2.0 OR BSD-2-Clause  https://github.com/pypa/packaging                   
 pycparser          3.12     BSD-3-Clause                https://github.com/eliben/pycparser                 


```

#### Option: with-description

When executed with the `--with-description` option, output with short description of the package.

[Example 63](./docs/examples/60-format-with/63-format-with-description.md)

```console
demo$ pip-licenses --with-description 
 Name               Version  License                     Description                                           
 aniso8601          10.0.1   BSD License                 A library for parsing ISO 8601 strings.               
 cffi               2.1.1    MIT-0                       Foreign Function Interface for Python calling C code. 
 dependency-groups  1.3.2    MIT                         A tool for resolving PEP 735 Dependency Group data    
 packaging          26.3     Apache-2.0 OR BSD-2-Clause  Core utilities for Python packages                    
 pycparser          3.12     BSD-3-Clause                C parser in Python                                    


```

#### Option: no-version

When executed with the `--without-version` option, output without the version number.

[Example 64](./docs/examples/60-format-with/64-format-with-noversion.md)

```console
demo$ pip-licenses --without-version 
 Name               License                    
 aniso8601          BSD License                
 cffi               MIT-0                      
 dependency-groups  MIT                        
 packaging          Apache-2.0 OR BSD-2-Clause 
 pycparser          BSD-3-Clause               


```

#### Option: with-license-file

When executed with the `--with-license-file` option, output the location of the package's license file on disk and the full contents of that file. Due to the length of these fields, this option is best paired with `--format=json`.

If you also want to output the file `NOTICE` distributed under Apache License etc., specify the `--with-notice-file` option additionally.

**Note:** If you want to keep the license file path secret, specify `--no-license-path` option together.

**Note:** When using `--with-license-file` with structured formats like CSV, Markdown, reST, or Confluence, the multi-line license file contents can break the formatting. For documentation workflows (like Sphinx), consider using separate commands:

```bash
# Generate clean RST table for documentation
$ pip-licenses --from=mixed --format=rst --output-file summary.rst

# Generate license file contents in plain-vertical format for inclusion
$ pip-licenses --from=mixed --format=plain-vertical --with-license-file --no-license-path --output-file with_license.txt
```

The RST file can be rendered nicely in Sphinx, while the plain-vertical format preserves the license file contents as monospace text.

#### Option: filter\-strings

Some package data contains Unicode characters which might cause problems for certain output formats (in particular ReST tables). If this filter is enabled, all characters which cannot be encoded with a given code page (see `--filter-code-page`) will be removed from any input strings (e.g. package name, description).

#### Option: filter\-code\-page

If the input strings are filtered (see `--filter-strings`), you can specify the applied code page (default `latin-1`). A list of all available code pages can be found [codecs module document](https://docs.python.org/3/library/codecs.html#standard-encodings).


### Verify options

#### Option: fail\-on

Fail (exit with code 1) on the first occurrence of the licenses of the semicolon-separated list. The license name
matching is case-insensitive.

If `--from=all`, the option will apply to the metadata license field.

[Example 70](./docs/examples/70-verify/70-verify-fail-on.md)

```console
demo$ pip-licenses --fail-on="MIT License;BSD License" 2>&1 
fail-on license BSD License was found for package aniso8601:10.0.1
('fail-on license BSD License was found for package aniso8601:10.0.1\n', 1)


```

**Note:** Packages with multiple licenses will fail if at least one license is included in the fail-on list. For example:
```console
# keyring library has 2 licenses
$ pip-licenses --package keyring
 Name     Version  License
 keyring  25.7.0   MIT License; Python Software Foundation License

# If just "Python Software Foundation License" is specified, it will fail.
$ pip-licenses --package keyring --fail-on="Python Software Foundation License;"
$ echo $?
1

# Matching is case-insensitive. Following check will fail:
$ pip-licenses --fail-on="mit license"
```

#### Option: warn\-on

Warn (write to stderr, without failing) on every occurrence of the licenses of the
semicolon-separated list. The license name matching is case-insensitive. This keeps `--allow-only`
runs green while making obligations that need follow-up visible, for example licences that require
attribution in the documentation.

```bash
(venv) $ pip-licenses --allow-only="MIT License;Python Software Foundation License" --warn-on="Python Software Foundation License"
```
**Note:** Unlike `--fail-on` and `--allow-only`, the run does not stop at the first occurrence:
one warning line is printed per package, and the exit code stays 0.

#### Option: allow\-only

Fail (exit with code 1) if none of the package licenses are in the semicolon-separated list. The license name
matching is case-insensitive.

If `--from=all`, the option will apply to the metadata license field.

[Example 71](./docs/examples/70-verify/71-verify-allow-only.md)

```console
demo$ pip-licenses --allow-only="MIT License;BSD License" 2>&1 
license Apache-2.0 OR BSD-2-Clause not in allow-only licenses was found for package packaging:26.3
Allowed licenses must be one of:
	BSD License
	MIT License

('license Apache-2.0 OR BSD-2-Clause not in allow-only licenses was found for package packaging:26.3\nAllowed licenses must be one of:\n\tBSD License\n\tMIT License\n\n', 1)


```

**Note:** Packages with multiple licenses will only be allowed if at least one license is included in the allow-only list. For example:
```
# keyring library has 2 licenses
$ pip-licenses --package keyring
 Name     Version  License
 keyring  25.7.0   MIT License; Python Software Foundation License

# One or both licenses must be specified (order and case does not matter). Following checks will pass:
$ pip-licenses --package keyring --allow-only="MIT License"
$ pip-licenses --package keyring --allow-only="mit License"
$ pip-licenses --package keyring --allow-only="BSD License;MIT License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License;MIT License"

# If none of the license in the allow list match, the check will fail.
$ pip-licenses --package keyring  --allow-only="BSD License"
$ echo $?
1
```

#### Option: partial\-match

If set, enables partial (substring) matching for `--fail-on`, `--warn-on` or `--allow-only`. Default is unset (False).

[Example 72](./docs/examples/70-verify/72-verify-partial-match.md)

```console
demo$ pip-licenses --partial-match --allow-only="MIT;BSD" 
 Name               Version  License                    
 aniso8601          10.0.1   BSD License                
 cffi               2.1.1    MIT-0                      
 dependency-groups  1.3.2    MIT                        
 packaging          26.3     Apache-2.0 OR BSD-2-Clause 
 pycparser          3.12     BSD-3-Clause               


```

**Note:** Semantics are the same as with `--fail-on` or `--allow-only`. This only enables substring matching.
```
# keyring library has 2 licenses
$ pip-licenses --package keyring
 Name     Version  License
 keyring  25.7.0   MIT License; Python Software Foundation License

# One or both licenses must be specified (order and case does not matter). Following checks will pass:
$ pip-licenses --package keyring --allow-only="MIT License"
$ pip-licenses --package keyring --allow-only="mit License"
$ pip-licenses --package keyring --allow-only="BSD License;MIT License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License"
$ pip-licenses --package keyring --allow-only="Python Software Foundation License;MIT License"

# These won't pass, as they're not a full match against one of the licenses
$ pip-licenses --package keyring --allow-only="MIT"
$ echo $?
1
$ pip-licenses --package keyring --allow-only="mit"
$ echo $?
1

# with --partial-match, they pass
$ pip-licenses --package keyring --partial-match --allow-only="MIT"
$ echo $?
0
$ pip-licenses --package keyring --partial-match --allow-only="mit"
$ echo $?
0
```

### pyproject.toml support

All command-line options for `pip-licenses` can be configured using the `pyproject.toml` file under the `[tool.pip-licenses]` section.
The `pyproject.toml` file is searched in the directory where the `pip-licenses` script is executed.
Command-line options specified during execution will override the corresponding options in `pyproject.toml`.

Example `pyproject.toml` configuration:

```toml
[tool.pip-licenses]
from = "classifier"
ignore-packages = [
  "scipy"
]
fail-on = "MIT;"
```

If you run `pip-licenses` without any command-line options, all options will be taken from the `pyproject.toml` file.
For instance, if you run `pip-licenses --from=mixed`, the `from` option will be overridden to `mixed`, while all other options will be sourced from `pyproject.toml`.

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

**Note:** This Docker image can not check package licenses with C and C++ Extensions. It only works with pure Python package dependencies.

If you want to resolve build environment issues, try using not slim image and more.

```diff
diff --git a/Dockerfile b/Dockerfile
index bfc4edc..81f9264 100644
--- a/Dockerfile
+++ b/Dockerfile
@@ -1,4 +1,4 @@
-FROM python:3.14-slim-trixie
+FROM python:3.14-trixie
```

## About UnicodeEncodeError

If a `UnicodeEncodeError` occurs, check your environment variables `LANG` and `LC_TYPE`. Additionally, you can set `PYTHONIOENCODING` to override the encoding used for `stdout`.

Often occurs in isolated environments such as Docker and tox.

See useful reports:

* [#35](https://github.com/raimon49/pip-licenses/issues/35)
* [#45](https://github.com/raimon49/pip-licenses/issues/45)

## License

[MIT License](https://github.com/raimon49/pip-licenses/blob/master/LICENSE)

### Dependencies

* [prettytable](https://pypi.org/project/prettytable/) by Luke Maurits and maintainer of fork version Jazzband team under the BSD-3-Clause License
    * **Note:** This package implicitly requires [wcwidth](https://pypi.org/project/wcwidth/).

* [tomli](https://pypi.org/project/tomli/) by Taneli Hukkinen under the MIT License

`pip-licenses` has been implemented in the policy to minimize the dependence on external package.

## Uninstallation

Uninstall package and dependent package with `pip` command.

```bash
$ pip uninstall pip-licenses prettytable wcwidth
```

## Contributing

See [contribution guidelines](https://github.com/raimon49/pip-licenses/blob/master/CONTRIBUTING.md).
