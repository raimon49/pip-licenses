from codecs import open
from os import path

from setuptools import setup

from piplicenses.const import __author__ as AUTHOR
from piplicenses.const import __license__ as LICENSE
from piplicenses.const import __pkgname__ as PKG_NAME
from piplicenses.const import __summary__ as SUMMARY
from piplicenses.const import __url__ as URL
from piplicenses.const import __version__ as VERSION

here = path.abspath(path.dirname(__file__))


def read_file(filename):
    content = ''
    with open(path.join(here, filename), encoding='utf-8') as f:
        content = f.read()

    return content


LONG_DESC = ''
try:
    from pypandoc import convert_file

    about_this = convert_file('README.md', 'rst', format='markdown_github')
    separate = '\n\n'
    change_log = convert_file('CHANGELOG.md', 'rst', format='markdown_github')

    LONG_DESC = about_this + separate + change_log
except (IOError, ImportError):
    LONG_DESC = read_file('README.md')


setup(
    name=PKG_NAME,
    version=VERSION,
    description=SUMMARY,
    long_description=LONG_DESC,
    url=URL,
    author=AUTHOR,
    license=LICENSE,
    entry_points={
        'console_scripts': [
            PKG_NAME + '=piplicenses.__main__:main',
        ],
    },
)
