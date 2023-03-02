## CHANGELOG

### 4.1.0

* Support case-insensitive license name matching around `--fail-on` and `--allow-only` parameters

### 4.0.3

* Escape unicode output (to e.g. `&#123;`) in the html output

### 4.0.2

* Add type annotations and code formatter

### 4.0.1

* Fix "pip-licenses" is missing in output of `pip-licenses --with-system` option

### 4.0.0

* Support for Python 3.11
* Dropped support Python 3.7
* Migrate Docker base image from Alpine to Debian 11-slim
* Breaking changes
    * Does not work with PTable and depends on prettytable
    * Depend on importlib\_metadata rather than pip

### 3.5.5

* Search for path defined in [PEP 639](https://peps.python.org/pep-0639/) with `--with-license-file` option
* Dropped support Python 3.6

### 3.5.4

* Skip directories when detecting license files

### 3.5.3

* Support pip 21.3 or later

### 3.5.2

* Ignore spaces around `--fail-on` and `--allow-only` parameters

### 3.5.1

* Fix the order in which multiple licenses are output

### 3.5.0

* Handle multiple licenses better with options `--fail-on` and `--allow-only`
* Small change in output method for multiple licenses, change the separator from comma to semicolon
    * Up to 3.4.0: `Python Software Foundation License, MIT License`
    * 3.5.0 or later: `Python Software Foundation License; MIT License`

### 3.4.0

* Implement new option `--packages`

### 3.3.1

* Fix license summary refer to `--from` option

### 3.3.0

* Improves the readability of the help command

### 3.2.0

* Implement new option `--from=all`
* Change license notation under [SPDX license identifier](https://spdx.org/licenses/) style

### 3.1.0

* Implement new option for use in continuous integration
    * `--fail-on`
    * `--allow-only`

### 3.0.0

* Dropped support Python 3.5
* Clarified support for Python 3.9
* Migrate package metadata to `setup.cfg`
* Breaking changes
    * Change default behavior to `--from=mixed`

### 2.3.0

* Implement new option for manage unicode characters
    * `--filter-strings`
    * `--filter-code-page`

### 2.2.1

* Fixed the file that is selected when multiple matches are made with `LICENSE*` with run `--with-license-file`

### 2.2.0

* Implement new option `--with-notice-file`
* Added to find British style file name `LICENCE` with run `--with-license-file`

### 2.1.1

* Suppress errors when opening license files

### 2.1.0

* Implement new option `--format=plain-vertical`
* Support for outputting license file named `COPYING *`

### 2.0.1

* Better license file open handling in Python 3

### 2.0.0

* Dropped support Python 2.7
* Breaking changes
    * Removed migration path to obsolete options
        * `--from-classifier`
        * `--format-markdown`
        * `--format-rst`
        * `--format-confluence`
        * `--format-html`
        * `--format-json`
* Implement new option `--no-license-path`

### 1.18.0

* Supports compatibility to work with either PTable or prettytable

### 1.17.0

* Implement new option `--output-file`
* Clarified support for Python 3.8

### 1.16.1

* Add a help text for `--format=json-license-finder` option

### 1.16.0

* Implement new option `--format=json-license-finder`

### 1.15.2

* Read license file works well with Windows

### 1.15.1

* Skip parsing of license file for packages specified with `--ignore-packages` option

### 1.15.0

* Implement new option `--format=csv`

### 1.14.0

* Implement new option `--from=mixed` as a mixed mode

### 1.13.0

* Implement new option `--from=meta`, `from=classifier`
* Dropped support Python 3.4

### 1.12.1

* Fix bug
    * Change warning output to standard error

### 1.12.0

* Supports execution within Docker container
* Warning of deprecated options
* Fix bug
    * Ignore `OSI Approved` string with multiple licenses

### 1.11.0

* Implement new option `--with-license-file`

### 1.10.0

* Implement new option `--with-description`

### 1.9.0

* Implement new option `--summary`

### 1.8.0

* Implement new option `--format-json`
* Dropped support Python 3.3

### 1.7.1

* Fix bug
    * Support pip 10.x

### 1.7.0

* Implement new option `--format-confluence`

### 1.6.1

* Fix bug
    * Support display multiple license with `--from-classifier` option
* Improve document
    * Add section of 'Uninstallation' in README

### 1.6.0

* Implement new option `--format-html`

### 1.5.0

* Implement new option `--format-rst`

### 1.4.0

* Implement new option `--format-markdown`
* Include LICENSE file in distribution package

### 1.3.0

* Implement new option `--ignore-packages`

### 1.2.0

* Implement new option `--from-classifier`

### 1.1.0

* Improve document
    * Add ToC to README document
    * Add a information of dependencies

### 1.0.0

* First stable release version

### 0.2.0
* Implement new option `--order`
    * Default behavior is `--order=name`

### 0.1.0

* First implementation version
    * Support options
        * `--with-system`
        * `--with-authors`
        * `--with-urls`
