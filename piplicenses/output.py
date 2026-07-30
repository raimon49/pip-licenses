# reduce to relevant parts to ensure Stefan is credited
# for content from https://github.com/stefan6419846/pip-licenses-cli/commit/0b1c2ae56d0d8bd0bac078bf758cc770da5527b0
# From Stefan's Pip-liceses-cli:
# Copyright (c) 2025 stefan6419846
# with MIT License (See LICENSE.txt; but this file had no included content, assumed not substantial portion?)

# But let's reduce further to what is of interest
# a big thank you to Stefan AKA stefan6419846 for their work on this!





_MULTI_VALUE_KEYS = None

if TYPE_CHECKING:  # pragma: no cover
    pass


def _handle_multiple_value_field(key: str, value: Iterator[str]) -> str | list[str]:
    if key.endswith("s"):
        return list(value) or ["UNKNOWN"]
    return cast(str, next(value, LICENSE_UNKNOWN))


def create_licenses_table(
    args: CustomNamespace,
    output_fields: Sequence[str] = DEFAULT_OUTPUT_FIELDS,
) -> PrettyTable:
    table = factory_styled_table_with_args(args, output_fields)

    for pkg in get_packages(args):
        row: list[str | list[str]] = []
        for field in output_fields:
            if field == "License":
                license_set = pkg.license_names
                license_str = "; ".join(sorted(license_set))
                row.append(license_str)
            elif field == "License-Classifier":
                row.append("; ".join(sorted(pkg.license_classifiers)) or LICENSE_UNKNOWN)
            elif hasattr(pkg, field.lower()):
                row.append(cast(str, getattr(pkg, field.lower())))
            else:
                value = getattr(pkg, FIELDS_TO_METADATA_KEYS[field])
                if field in _MULTI_VALUE_KEYS:
                    row.append(_handle_multiple_value_field(field, value))
                else:
                    row.append(cast(str, value))
        table.add_row(row)

    return table




class PlainVerticalTable(PrettyTable):
    """PrettyTable for outputting to a simple non-column based style.

    When used with --with-license-file, this style is similar to the default
    style generated from Angular CLI's --extractLicenses flag.
    """

    def get_string(self, **kwargs: str | list[str]) -> str:
        options = self._get_options(kwargs)
        rows = self._get_rows(options)
        show_paths = "LicenseFiles" in kwargs["fields"]

        output = ""
        for row in rows:
            index = 0
            while index < len(row):
                v = row[index]
                if isinstance(v, list):
                    if show_paths:
                        for first_entry, second_entry in zip(v, row[index + 1]):
                            output += "{}\n{}\n".format(first_entry, second_entry)
                        index += 1
                    else:
                        for entry in v:
                            output += "{}\n".format(entry)
                else:
                    output += "{}\n".format(v)
                index += 1
            output += "\n"

        return output
