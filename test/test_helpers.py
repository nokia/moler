# -*- coding: utf-8 -*-
"""
Tests for helpers functions/classes.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2022, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import mock
import pytest
from moler.exceptions import WrongUsage


def test_instance_id_returns_id_in_hex_form_without_0x():
    from moler.helpers import instance_id
    from six.moves import builtins
    # 0xf0a1 == 61601 decimal
    with mock.patch.object(builtins, "id", return_value=61601):
        instance = "moler object"
        assert "0x" not in instance_id(instance)
        assert instance_id(instance) == "f0a1"


def test_converterhelper_k():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    bytes_value, value_in_units, unit = converter.to_bytes("2.5K")
    assert 2560 == bytes_value
    assert 2.5 == value_in_units
    assert 'k' == unit


def test_converterhelper_m():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    bytes_value, value_in_units, unit = converter.to_bytes(".3m", False)
    assert 300000 == bytes_value
    assert 0.3 == value_in_units
    assert 'm' == unit


def test_converterhelper_wrong_unit():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    with pytest.raises(ValueError):
        converter.to_bytes("3UU", False)


def test_converterhelper_seconds():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    value, value_in_units, unit = converter.to_seconds_str("3m")
    assert 180 == value
    assert 3 == value_in_units
    assert 'm' == unit


def test_converterhelper_number_wrong_format():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    with pytest.raises(ValueError):
        converter.to_number(value="abc", raise_exception=True)
    val = converter.to_number(value="abc", raise_exception=False)
    assert val == 0


def test_converterhelper_number():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    val = converter.to_number(value="1")
    assert 1 == val
    val = converter.to_number(value="0.1")
    assert val == 0.1


def test_converterhelper_seconds_ms():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    value = converter.to_seconds(0.408, "ms")
    assert pytest.approx(0.000408, 0.000001) == value


def test_converterhelper_seconds_wrong_unit():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    with pytest.raises(ValueError):
        converter.to_seconds_str("3UU")


def test_copy_list():
    from moler.helpers import copy_list
    src = [1]
    dst = copy_list(src, deep_copy=True)
    assert src == dst
    dst[0] = 2
    assert src != dst


def test_copy_dict():
    from moler.helpers import copy_dict
    src = {'a': 1}
    dst = copy_dict(src, deep_copy=True)
    assert src == dst
    dst['a'] = 2
    assert src != dst


def test_regex_helper():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    assert regex_helper is not None
    match = regex_helper.match(r"\d+(\D+)\d+", "111ABC222")
    assert match is not None
    assert match == regex_helper.get_match()
    assert regex_helper.group(1) == "ABC"


def test_groups_at_regex_helper():
    import re
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    if regex_helper.search_compiled(re.compile(r"(\d+)_([A-Z]+)(\w+),(\d+)"), "111_ABCef,222"):
        ones, uppers, lowers, twos = regex_helper.groups()
    assert ones == '111'
    assert uppers == 'ABC'
    assert lowers == 'ef'
    assert twos == '222'


def test_search_compiled_none():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    with pytest.raises(WrongUsage) as exc:
        regex_helper.search_compiled(None, '123')
    assert "search_compiled is None" in str(exc)


def test_match_compiled_none():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    with pytest.raises(WrongUsage) as exc:
        regex_helper.match_compiled(None, '123')
    assert "match_compiled is None" in str(exc)


def test_group_without_match_object():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    with pytest.raises(WrongUsage) as exc:
        regex_helper.group(1)
    assert "Nothing was matched before calling" in str(exc)


def test_groups_without_match_object():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    with pytest.raises(WrongUsage) as exc:
        regex_helper.groups()
    assert "Nothing was matched before calling" in str(exc)


def test_groupdict_without_match_object():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    with pytest.raises(WrongUsage) as exc:
        regex_helper.groupdict()
    assert "Nothing was matched before calling" in str(exc)


def test_all_chars_to_hex():
    from moler.helpers import all_chars_to_hex
    source = "a\n\rb" + chr(3) + chr(5)
    expected_output = r"\x61\x0a\x0d\x62\x03\x05"
    output = all_chars_to_hex(source=source)
    assert output == expected_output


def test_non_printable_chars_to_hex():
    from moler.helpers import non_printable_chars_to_hex
    source = "a\n\rb" + chr(3) + chr(5)
    expected_output = r"a\x0a\x0db\x03\x05"
    output = non_printable_chars_to_hex(source=source)
    assert output == expected_output


def test_removal_cursor_visibility_codes():
    from moler.helpers import remove_cursor_visibility_codes
    line = "\x1B[?25h\x1B[?25llogin\x1B[?25l :\x1B[?12h\x1B[?12l"
    output = remove_cursor_visibility_codes(multiline=line)
    assert "login :" == output
    multiline = "\x1B[?25h\x1B[?25llogin\x1B[?25l :\x1B[?12h\x1B[?12l\n\x1B[?25h\x1B[?25l>"
    output2 = remove_cursor_visibility_codes(multiline=multiline)
    assert "login :\n>" == output2


def test_removal_fill_spaces_right_codes():
    from moler.helpers import remove_fill_spaces_right_codes
    full_line = "login:\x1B[300X\x1B[24X\x1B[300C\n"
    multiline = "login:\x1B[300X\x1B[24X\x1B[300C\n\x1B[300X\x1B[300C\n"
    incomplete_line = "login:\x1B[300X\x1B[300C"
    output1 = remove_fill_spaces_right_codes(multiline=full_line)
    assert "login:\n" == output1
    output2 = remove_fill_spaces_right_codes(multiline=multiline)
    assert "login:\n\n" == output2
    output3 = remove_fill_spaces_right_codes(multiline=incomplete_line)
    assert incomplete_line == output3   # no conversion since no newline


def test_removal_left_wrights_that_were_overwritten():
    from moler.helpers import remove_overwritten_left_write
    line = "\x1B[300X\x1B[300C\x1B[11;1H\x1B[?25h\x1B[?25l\x1B[HLast login:"
    output = remove_overwritten_left_write(multiline=line)
    assert "Last login:" == output
    line2 = "\x1B[300X\x1B[300C\x1B[11;1H\x1B[?25h\x1B[?25l\x1B[H\x1B[32mLast login:"
    output2 = remove_overwritten_left_write(multiline=line2)
    assert "\x1B[32mLast login:" == output2
    line3 = "\x1B[300X\x1B[300C\x1B[11;1H\x1B[?25h\x1B[?25l\x1B[H login:"
    output3 = remove_overwritten_left_write(multiline=line3)
    assert " login:" == output3
    multiline = "\x1B[300X\x1B[300C\x1B[11;1H\x1B[?25h\x1B[?25l\x1B[H login:\nabc>\x1B[H\x1B[300X\nabc>\x1B[H password:"
    output4 = remove_overwritten_left_write(multiline=multiline)
    assert " login:\n\x1B[300X\n password:" == output4


def test_removal_text_formating_codes():
    from moler.helpers import remove_text_formatting_codes
    line = "\x1B[32muser-lab0@PLKR-SC5G-PC11 \x1B[33m~\x1B[m"
    output = remove_text_formatting_codes(multiline=line)
    assert "user-lab0@PLKR-SC5G-PC11 ~" == output
    multiline = "\x1B[32muser-lab0@PLKR-SC5G-PC11 \x1B[33m~\x1B[m$ adb shell\n\x1B[32mmsmnile:/ #\x1B[m"
    output2 = remove_text_formatting_codes(multiline=multiline)
    assert "user-lab0@PLKR-SC5G-PC11 ~$ adb shell\nmsmnile:/ #" == output2


def test_removal_window_title_codes():
    from moler.helpers import remove_window_title_codes
    line = "\x1B]0;~\x07"
    output = remove_window_title_codes(multiline=line)
    assert "" == output
    multiline = "\x1B]0;~\x07\n\x1B]2;~\x07"
    output2 = remove_window_title_codes(multiline=multiline)
    assert "\n" == output2


def test_convert_to_int():
    from moler.helpers import convert_to_int, compare_objects

    sample_input = {'KEY': [{'KEY1 ': {'contextInfoList': ['sample', '2', '4'],
                                       'someIds': '0'}},
                            {'KEY2': {'contextInfoList': [],
                                      'num': '20',
                                      'poolId': '1',
                                      'user': {
                                          'contextType': 'sample',
                                          'numContexts': '3',
                                          'num': '4'}}}]}

    expected_output = {'KEY': [{'KEY1 ': {'contextInfoList': ['sample', 2, 4],
                                          'someIds': 0}},
                               {'KEY2': {'contextInfoList': [],
                                         'num': 20,
                                         'poolId': 1,
                                         'user': {
                                             'contextType': 'sample',
                                             'numContexts': 3,
                                             'num': 4}}}]}

    assert not compare_objects(convert_to_int(sample_input), expected_output)


def test_convert_to_number_int():
    from moler.helpers import convert_to_number
    expected = 4
    result = convert_to_number("{}".format(expected))
    assert expected == result


def test_convert_to_number_float():
    from moler.helpers import convert_to_number
    expected = 3.2
    result = convert_to_number("{}".format(expected))
    assert expected == result


def test_convert_to_number_str():
    from moler.helpers import convert_to_number
    expected = "not a number"
    result = convert_to_number(expected)
    assert expected == result


def test_escape_cursors():
    from moler.helpers import remove_escape_codes
    raw_line = "\x1B7\x1B[0;100r\x1B8\x1B[1A\x1B[Jmoler_bash#"
    expected_line = "moler_bash#"
    line = remove_escape_codes(raw_line)
    assert expected_line == line
