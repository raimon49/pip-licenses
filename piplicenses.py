# reduce to relevant parts to ensure Stefan is credited
# for content from https://github.com/stefan6419846/pip-licenses-cli/commit/0b1c2ae56d0d8bd0bac078bf758cc770da5527b0
# From Stefan's Pip-liceses-cli:
# Copyright (c) 2025 stefan6419846
# with MIT License (See LICENSE.txt; but this file had no included content, assumed not substantial portion?)

# But let's reduce further to what is of interest
# a big thank you to Stefan AKA stefan6419846 for their work on this!

from piplicenses import __pkgname__






# Mapping of FIELD_NAMES to METADATA_KEYS where they differ by more than case
FIELDS_TO_METADATA_KEYS = {
    "URL": "homepage",
    "License-Metadata": "license",
    "License-Classifier": "license_classifier",
    "LicenseFile": "license_files",
    "LicenseFiles": "license_files",
    "LicenseText": "license_texts",
    "LicenseTexts": "license_texts",
    "NoticeFile": "notice_files",
    "NoticeFiles": "notice_files",
    "NoticeText": "notice_texts",
    "NoticeTexts": "notice_texts",
    "OtherFiles": "other_files",
    "OtherTexts": "other_texts",
    "Description": "summary",
}

_MULTI_VALUE_KEYS = {
    "LicenseFile",
    "LicenseFiles",
    "LicenseText",
    "LicenseTexts",
    "NoticeFile",
    "NoticeFiles",
    "NoticeText",
    "NoticeTexts",
    "OtherFiles",
    "OtherTexts",
}

SYSTEM_PACKAGES = [
    __pkgname__,
]


# Not using __pkgname__ because we want to be backwards compatible
