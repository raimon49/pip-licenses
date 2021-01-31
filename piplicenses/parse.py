# ---------------------------------------------------------------------------
# Licensed under the MIT License. See LICENSE file for license information.
# ---------------------------------------------------------------------------
import glob
import os
from email import message_from_string
from email.parser import FeedParser

from .const import (
    LICENSE_UNKNOWN, METADATA_KEYS, CustomNamespace, FromArg)


def get_pkg_included_file(pkg, file_names):
    """
    Attempt to find the package's included file on disk and return the
    tuple (included_file_path, included_file_contents).
    """
    included_file = LICENSE_UNKNOWN
    included_text = LICENSE_UNKNOWN
    pkg_dirname = "{}-{}.dist-info".format(
        pkg.project_name.replace("-", "_"), pkg.version)
    patterns = []
    [patterns.extend(sorted(glob.glob(os.path.join(pkg.location,
                                                    pkg_dirname,
                                                    f))))
        for f in file_names]
    for test_file in patterns:
        if os.path.exists(test_file):
            included_file = test_file
            with open(test_file, encoding='utf-8',
                        errors='backslashreplace') as included_file_handle:
                included_text = included_file_handle.read()
            break
    return (included_file, included_text)


def find_license_from_classifier(message):
    licenses = []
    for k, v in message.items():
        if k == 'Classifier' and v.startswith('License'):
            license = v.split(' :: ')[-1]

            # Through the declaration of 'Classifier: License :: OSI Approved'
            if license != 'OSI Approved':
                licenses.append(license)

    return licenses


def select_license_by_source(from_source, license_classifier, license_meta):
    license_classifier_str = ', '.join(license_classifier) or LICENSE_UNKNOWN
    if (from_source == FromArg.CLASSIFIER or
            from_source == FromArg.MIXED and len(license_classifier) > 0):
        return license_classifier_str
    else:
        return license_meta


def get_pkg_info(pkg, args: CustomNamespace):
    (license_file, license_text) = get_pkg_included_file(
        pkg,
        ('LICENSE*', 'LICENCE*', 'COPYING*')
    )
    (notice_file, notice_text) = get_pkg_included_file(
        pkg,
        ('NOTICE*',)
    )
    pkg_info = {
        'name': pkg.project_name,
        'version': pkg.version,
        'namever': str(pkg),
        'licensefile': license_file,
        'licensetext': license_text,
        'noticefile': notice_file,
        'noticetext': notice_text,
    }
    metadata = None
    if pkg.has_metadata('METADATA'):
        metadata = pkg.get_metadata('METADATA')

    if pkg.has_metadata('PKG-INFO') and metadata is None:
        metadata = pkg.get_metadata('PKG-INFO')

    if metadata is None:
        for key in METADATA_KEYS:
            pkg_info[key] = LICENSE_UNKNOWN

        return pkg_info

    feed_parser = FeedParser()
    feed_parser.feed(metadata)
    parsed_metadata = feed_parser.close()

    for key in METADATA_KEYS:
        pkg_info[key] = parsed_metadata.get(key, LICENSE_UNKNOWN)

    if metadata is not None:
        message = message_from_string(metadata)
        pkg_info['license_classifier'] = \
            find_license_from_classifier(message)

    if args.filter_strings:
        for k in pkg_info:
            if isinstance(pkg_info[k], list):
                for i, item in enumerate(pkg_info[k]):
                    pkg_info[k][i] = item. \
                        encode(args.filter_code_page, errors="ignore"). \
                        decode(args.filter_code_page)
            else:
                pkg_info[k] = pkg_info[k]. \
                    encode(args.filter_code_page, errors="ignore"). \
                    decode(args.filter_code_page)

    return pkg_info
