import pytest

import piplicenses.__main__
from piplicenses.argparse import create_parser


@pytest.fixture(scope='package')
def parser():
    return create_parser()


UNICODE_APPENDIX = ""
with open('tests/fixtures/unicode_characters.txt', encoding='utf-8') as f:
    # Read from external file considering a terminal that cannot handle "emoji"
    UNICODE_APPENDIX = f.readline().replace("\n", "")


def get_installed_distributions_mocked(*args, **kwargs):
    packages = get_installed_distributions_orig(*args, **kwargs)
    if not packages[-1].project_name.endswith(UNICODE_APPENDIX):
        packages[-1].project_name += " "+UNICODE_APPENDIX
    return packages


get_installed_distributions_orig = piplicenses.__main__.get_installed_distributions  # noqa
piplicenses.__main__.get_installed_distributions = get_installed_distributions_mocked  # noqa
