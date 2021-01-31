from piplicenses.argparse import CompatibleArgumentParser
from piplicenses.table import factory_styled_table_with_args, RULE_FRAME


def test_format_plain(parser: CompatibleArgumentParser):
    format_plain_args = ['--format=plain']
    args = parser.parse_args(format_plain_args)
    table = factory_styled_table_with_args(args)

    assert 'l' in table.align.values()
    assert table.border is False
    assert table.header is True
    assert table.junction_char == '+'
    assert table.hrules == RULE_FRAME
