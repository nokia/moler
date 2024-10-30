# -*- coding: utf-8 -*-
"""
Tests for helpers functions/classes.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2024, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import copy
import sys

import mock
import pytest
import re
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
    val2 = converter.to_number(value="abc", raise_exception=False,
                               none_if_cannot_convert=True)
    assert val2 is None


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


def test_converterhelper_bytes():
    from moler.util.converterhelper import ConverterHelper
    converter = ConverterHelper.get_converter_helper()
    bytes_value, value_in_units, unit = converter.to_bytes("0.00 Bytes")
    assert 0.0 == bytes_value
    assert 0.0 == value_in_units
    assert 'b' == unit


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
        regex_helper.search_compiled(None, '123', True)
    assert "search_compiled is None" in str(exc)


def test_match_compiled_none():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    with pytest.raises(WrongUsage) as exc:
        regex_helper.match_compiled(None, '123', True)
    assert "match_compiled is None" in str(exc)


def test_search_compiled_none_passed_compiled_none():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    assert None is regex_helper.search_compiled(None, '123')


def test_match_compiled_none_passed_compiled_none():
    from moler.cmd import RegexHelper
    regex_helper = RegexHelper()
    assert None is regex_helper.match_compiled(None, '123')


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
    source = f'a\n\rb{chr(3)}{chr(5)}'
    expected_output = r"\x61\x0a\x0d\x62\x03\x05"
    output = all_chars_to_hex(source=source)
    assert output == expected_output


def test_non_printable_chars_to_hex():
    from moler.helpers import non_printable_chars_to_hex
    source = f'a\n\rb{chr(3)}{chr(5)}'
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
    result = convert_to_number(f"{expected}")
    assert expected == result


def test_convert_to_number_float():
    from moler.helpers import convert_to_number
    expected = 3.2
    result = convert_to_number(f"{expected}")
    assert expected == result


def test_convert_to_number_str():
    from moler.helpers import convert_to_number
    expected = "not a number"
    result = convert_to_number(expected)
    assert expected == result


def test_convert_to_number_str_none():
    from moler.helpers import convert_to_number
    expected = "not a number"
    result1 = convert_to_number(expected, False)
    assert expected == result1
    result2 = convert_to_number(expected, True)
    assert result2 is None


def test_escape_cursors():
    from moler.helpers import remove_escape_codes
    raw_line = "\x1B7\x1B[0;100r\x1B8\x1B[1A\x1B[Jmoler_bash#"
    expected_line = "moler_bash#"
    line = remove_escape_codes(raw_line)
    assert expected_line == line


def test_regexp_without_anchors():
    from moler.helpers import regexp_without_anchors
    expected = "abc"
    assert expected == regexp_without_anchors(re.compile(expected)).pattern


def test_regexp_with_both_anchors():
    from moler.helpers import regexp_without_anchors
    expected = "abc"
    regex = re.compile(r"^abc$")
    assert expected == regexp_without_anchors(regex).pattern


def test_regexp_with_left_anchor():
    from moler.helpers import regexp_without_anchors
    expected = "abc"
    regex = re.compile(r"^abc")
    assert expected == regexp_without_anchors(regex).pattern


def test_regexp_with_right_anchor():
    from moler.helpers import regexp_without_anchors
    expected = "abc"
    regex = re.compile(r"abc$")
    assert expected == regexp_without_anchors(regex).pattern


def test_diff_the_same_structure():
    from moler.helpers import diff_data
    a = ['a', 3, 4.0, True, False, ['abc', 'def'], (2.5, 3.6, 4.2), {1, 2, 3},
         {'a': 3, 'b': {'c': 5, 'd': 6.3}}]
    b = copy.deepcopy(a)
    msg = diff_data(first_object=a, second_object=b)
    assert "" == msg


def test_diff_different_types():
    from moler.helpers import diff_data
    a = ['a', 3, 4.0, True, False, ['abc', 'def'], (2.5, 3.6, 4.2), {1, 2, 3},
         {'a': 3, 'b': {'c': 5, 'd': 6.3}}]
    b = copy.deepcopy(a)
    b[3] = 4
    msg = diff_data(first_object=a, second_object=b)
    if sys.version_info < (3, 0):
        assert "root -> [3] True is type of <type 'bool'> but 4 is type of <type 'int'>" \
               == msg
    else:
        assert "root -> [3] True is type of <class 'bool'> but 4 is type of <class 'int'>"\
               == msg


def test_diff_different_values():
    from moler.helpers import diff_data
    a = ['a', 3, 4.0, True, False, ['abc', 'def'], (2.5, 3.6, 4.2), {1, 2, 3},
         {'a': 3, 'b': {'c': 5, 'd': 6.3}}]
    b = copy.deepcopy(a)
    b[-1] = {'a': 3, 'b': {'c': 5, 'd': 6.2}}
    msg = diff_data(first_object=a, second_object=b)
    assert "root -> [8] -> [b] -> [d] the first value 6.3 is different from the" \
           " second value 6.2." == msg


def test_date_parser_cest():
    from moler.util.converterhelper import ConverterHelper
    from datetime import datetime
    from dateutil.tz import tzoffset

    date_str = "Wed 22 May 2024 11:21:34 AM CEST"
    date_parsed = ConverterHelper.parse_date(date_str)
    date_expected = datetime(year=2024, month=5, day=22, hour=11, minute=21, second=34, tzinfo=tzoffset('CEST', 7200))
    assert date_parsed == date_expected


def test_date_parser_cet():
    from moler.util.converterhelper import ConverterHelper
    from datetime import datetime
    from dateutil.tz import tzoffset

    date_str = "Wed 22 May 2024 11:21:34 AM CET"
    date_parsed = ConverterHelper.parse_date(date_str)
    date_expected = datetime(year=2024, month=5, day=22, hour=11, minute=21, second=34, tzinfo=tzoffset('CET', 3600))
    assert date_parsed == date_expected


def test_date_parser_utc():
    from moler.util.converterhelper import ConverterHelper
    from datetime import datetime
    from dateutil.tz import tzoffset

    date_str = " Wed May 22 09:11:48 UTC 2024"
    date_parsed = ConverterHelper.parse_date(date_str)
    date_expected = datetime(year=2024, month=5, day=22, hour=9, minute=11, second=48, tzinfo=tzoffset('UTC', 0))
    assert date_parsed == date_expected


def test_remove_state_from_sm_dict():
    from moler.device.unixremote import UnixRemote
    from moler.helpers import remove_state_from_sm
    source_sm = {
        UnixRemote.unix_local: {
            UnixRemote.proxy_pc: {
                "execute_command": "ssh",
                "command_params": {
                    "target_newline": "\n"
                },
                "required_command_params": [
                    "host",
                    "login",
                    "password",
                    "expected_prompt"
                ]
            },
        },
        UnixRemote.proxy_pc: {  # from
            UnixRemote.unix_remote: {  # to
                "execute_command": "ssh",  # using command
                "command_params": {  # with parameters
                    "target_newline": "\n"
                },
                "required_command_params": [
                    "host",
                    "login",
                    "password",
                    "expected_prompt"
                ]
            },
            UnixRemote.unix_local: { # to
                "execute_command": "exit",  # using command
                "command_params": {  # with parameters
                    "target_newline": "\n"
                },
                "required_command_params": [    # with parameters
                    "expected_prompt"
                ]
            },
        },
        UnixRemote.unix_remote: {  # from
            UnixRemote.proxy_pc: {  # to
                "execute_command": "exit",  # using command
                "command_params": {  # with parameters
                    "target_newline": "\n"
                },
                "required_command_params": [
                    "expected_prompt"
                ]
            },
            UnixRemote.unix_remote_root: {  # to
                "execute_command": "su",  # using command
                "command_params": {  # with parameters
                    "password": "root_password",
                    "expected_prompt": r'remote_root_prompt',
                    "target_newline": "\n"
                },
                "required_command_params": [
                ]
            },
        },
        UnixRemote.unix_remote_root: {  # from
            UnixRemote.unix_remote: {  # to
                "execute_command": "exit",  # using command
                "command_params": {  # with parameters
                    "target_newline": "\n",
                    "expected_prompt": r'remote_user_prompt'
                },
                "required_command_params": [
                ]
            }
        }
    }

    expected_sm = {
        UnixRemote.unix_local: {
            UnixRemote.unix_remote: {  # to
                "execute_command": "ssh",  # using command
                "command_params": {  # with parameters
                    "target_newline": "\n"
                },
                "required_command_params": [
                    "host",
                    "login",
                    "password",
                    "expected_prompt"
                ]
            },
        },
        UnixRemote.unix_remote: {  # from
            UnixRemote.unix_local: {  # to
                "execute_command": "exit",  # using command
                "command_params": {  # with parameters
                    "target_newline": "\n"
                },
                "required_command_params": [
                    "expected_prompt"
                ]
            },
            UnixRemote.unix_remote_root: {  # to
                "execute_command": "su",  # using command
                "command_params": {  # with parameters
                    "password": "root_password",
                    "expected_prompt": r'remote_root_prompt',
                    "target_newline": "\n"
                },
                "required_command_params": [
                ]
            },
        },
        UnixRemote.unix_remote_root: {  # from
            UnixRemote.unix_remote: {  # to
                "execute_command": "exit",  # using command
                "command_params": {  # with parameters
                    "target_newline": "\n",
                    "expected_prompt": r'remote_user_prompt'
                },
                "required_command_params": [
                ]
            }
        }
    }

    source_transitions = {
        UnixRemote.unix_local: {
            UnixRemote.proxy_pc: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            }
        },
        UnixRemote.proxy_pc: {
            UnixRemote.unix_local: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            },
        },
        UnixRemote.proxy_pc: {
            UnixRemote.unix_remote: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            }
        },
        UnixRemote.unix_remote: {
            UnixRemote.proxy_pc: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            },
            UnixRemote.unix_remote_root: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            }
        },
        UnixRemote.unix_remote_root: {
            UnixRemote.unix_remote: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            }
        }
    }

    expected_transitions = {
        UnixRemote.unix_remote: {
            UnixRemote.unix_local: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            },
            UnixRemote.unix_remote_root: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            }
        },
        UnixRemote.unix_local: {
            UnixRemote.unix_remote: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            }
        },
        UnixRemote.unix_remote_root: {
            UnixRemote.unix_remote: {
                "action": [
                    "_execute_command_to_change_state"
                ],
            }
        }
    }

    (current_sm, current_transitions) = remove_state_from_sm(source_sm=source_sm, source_transitions=source_transitions, state_to_remove=UnixRemote.proxy_pc)
    assert expected_sm == current_sm
    assert expected_transitions == current_transitions


def test_remove_state_hops_from_sm():
    from moler.device.unixremote import UnixRemote
    from moler.helpers import remove_state_hops_from_sm
    source_hops = {
        UnixRemote.not_connected: {
            UnixRemote.unix_remote: UnixRemote.unix_local,
            UnixRemote.proxy_pc: UnixRemote.unix_local,
            UnixRemote.unix_local_root: UnixRemote.unix_local,
            UnixRemote.unix_remote_root: UnixRemote.unix_local
        },
        UnixRemote.unix_remote: {
            UnixRemote.not_connected: UnixRemote.proxy_pc,
            UnixRemote.unix_local: UnixRemote.proxy_pc,
            UnixRemote.unix_local_root: UnixRemote.proxy_pc
        },
        UnixRemote.unix_local_root: {
            UnixRemote.not_connected: UnixRemote.unix_local,
            UnixRemote.unix_remote: UnixRemote.unix_local,
            UnixRemote.unix_remote_root: UnixRemote.unix_local
        },
        UnixRemote.proxy_pc: {
            UnixRemote.not_connected: UnixRemote.unix_local,
            UnixRemote.unix_local_root: UnixRemote.unix_local,
            UnixRemote.unix_remote_root: UnixRemote.unix_remote
        },
        UnixRemote.unix_local: {
            UnixRemote.unix_remote: UnixRemote.proxy_pc,
            UnixRemote.unix_remote_root: UnixRemote.proxy_pc
        },
        UnixRemote.unix_remote_root: {
            UnixRemote.not_connected: UnixRemote.unix_remote,
            UnixRemote.unix_local: UnixRemote.unix_remote,
            UnixRemote.unix_local_root: UnixRemote.unix_remote,
            UnixRemote.proxy_pc: UnixRemote.unix_remote,
        }
    }
    expected_hops = {
        UnixRemote.not_connected: {
            UnixRemote.unix_remote: UnixRemote.unix_local,
            UnixRemote.unix_local_root: UnixRemote.unix_local,
            UnixRemote.unix_remote_root: UnixRemote.unix_local,
        },
        UnixRemote.unix_local: {
            UnixRemote.unix_remote_root: UnixRemote.unix_remote
        },
        UnixRemote.unix_local_root: {
            UnixRemote.not_connected: UnixRemote.unix_local,
            UnixRemote.unix_remote: UnixRemote.unix_local,
            UnixRemote.unix_remote_root: UnixRemote.unix_local
        },
        UnixRemote.unix_remote: {
            UnixRemote.not_connected: UnixRemote.unix_local,
            UnixRemote.unix_local_root: UnixRemote.unix_local
        },
        UnixRemote.unix_remote_root: {
            UnixRemote.not_connected: UnixRemote.unix_remote,
            UnixRemote.unix_local: UnixRemote.unix_remote,
            UnixRemote.unix_local_root: UnixRemote.unix_remote,
        }
    }

    current_hops = remove_state_hops_from_sm(source_hops, UnixRemote.proxy_pc)
    assert expected_hops == current_hops


def test_remove_state_hops_from_sm_adb():
    from moler.helpers import remove_state_hops_from_sm
    source_hops = {
        'ADB_SHELL': {
            'NOT_CONNECTED': 'UNIX_REMOTE',
            'PROXY_PC': 'UNIX_REMOTE',
            'UNIX_LOCAL': 'UNIX_REMOTE',
            'UNIX_LOCAL_ROOT': 'UNIX_REMOTE',
            'UNIX_REMOTE_ROOT': 'UNIX_REMOTE'
        },
        'ADB_SHELL_ROOT': {
            'NOT_CONNECTED': 'ADB_SHELL',
            'PROXY_PC': 'ADB_SHELL',
            'UNIX_LOCAL': 'ADB_SHELL',
            'UNIX_LOCAL_ROOT': 'ADB_SHELL',
            'UNIX_REMOTE': 'ADB_SHELL',
            'UNIX_REMOTE_ROOT': 'ADB_SHELL'
        },
        'NOT_CONNECTED': {
            'ADB_SHELL': 'UNIX_LOCAL',
            'ADB_SHELL_ROOT': 'UNIX_LOCAL',
            'PROXY_PC': 'UNIX_LOCAL',
            'UNIX_LOCAL_ROOT': 'UNIX_LOCAL',
            'UNIX_REMOTE': 'UNIX_LOCAL',
            'UNIX_REMOTE_ROOT': 'UNIX_LOCAL'
        },
        'PROXY_PC': {
            'ADB_SHELL': 'UNIX_REMOTE',
            'ADB_SHELL_ROOT': 'UNIX_REMOTE',
            'NOT_CONNECTED': 'UNIX_LOCAL',
            'UNIX_LOCAL_ROOT': 'UNIX_LOCAL',
            'UNIX_REMOTE_ROOT': 'UNIX_REMOTE'
        },
        'UNIX_LOCAL': {
            'ADB_SHELL': 'PROXY_PC',
            'ADB_SHELL_ROOT': 'PROXY_PC',
            'UNIX_REMOTE': 'PROXY_PC',
            'UNIX_REMOTE_ROOT': 'PROXY_PC'
        },
        'UNIX_LOCAL_ROOT': {
            'ADB_SHELL': 'UNIX_LOCAL',
            'ADB_SHELL_ROOT': 'UNIX_LOCAL',
            'NOT_CONNECTED': 'UNIX_LOCAL',
            'PROXY_PC': 'UNIX_LOCAL',
            'UNIX_REMOTE': 'UNIX_LOCAL',
            'UNIX_REMOTE_ROOT': 'UNIX_LOCAL'
        },
        'UNIX_REMOTE': {
            'ADB_SHELL_ROOT': 'ADB_SHELL',
            'NOT_CONNECTED': 'PROXY_PC',
            'UNIX_LOCAL': 'PROXY_PC',
            'UNIX_LOCAL_ROOT': 'PROXY_PC'
        },
        'UNIX_REMOTE_ROOT': {
            'ADB_SHELL': 'UNIX_REMOTE',
            'ADB_SHELL_ROOT': 'UNIX_REMOTE',
            'NOT_CONNECTED': 'UNIX_REMOTE',
            'PROXY_PC': 'UNIX_REMOTE',
            'UNIX_LOCAL': 'UNIX_REMOTE',
            'UNIX_LOCAL_ROOT': 'UNIX_REMOTE'
        }
    }

    expected_hops = {
        'ADB_SHELL': {
            'NOT_CONNECTED': 'UNIX_REMOTE',
            'UNIX_LOCAL': 'UNIX_REMOTE',
            'UNIX_LOCAL_ROOT': 'UNIX_REMOTE',
            'UNIX_REMOTE_ROOT': 'UNIX_REMOTE'
        },
        'ADB_SHELL_ROOT': {
            'NOT_CONNECTED': 'ADB_SHELL',
            'UNIX_LOCAL': 'ADB_SHELL',
            'UNIX_LOCAL_ROOT': 'ADB_SHELL',
            'UNIX_REMOTE': 'ADB_SHELL',
            'UNIX_REMOTE_ROOT': 'ADB_SHELL'
        },
        'NOT_CONNECTED': {
            'ADB_SHELL': 'UNIX_LOCAL',
            'ADB_SHELL_ROOT': 'UNIX_LOCAL',
            'UNIX_LOCAL_ROOT': 'UNIX_LOCAL',
            'UNIX_REMOTE': 'UNIX_LOCAL',
            'UNIX_REMOTE_ROOT': 'UNIX_LOCAL'
        },
        'UNIX_LOCAL': {
            'ADB_SHELL': 'UNIX_REMOTE',
            'ADB_SHELL_ROOT': 'UNIX_REMOTE',
            'UNIX_REMOTE_ROOT': 'UNIX_REMOTE'
        },
        'UNIX_LOCAL_ROOT': {
            'ADB_SHELL': 'UNIX_LOCAL',
            'ADB_SHELL_ROOT': 'UNIX_LOCAL',
            'NOT_CONNECTED': 'UNIX_LOCAL',
            'UNIX_REMOTE': 'UNIX_LOCAL',
            'UNIX_REMOTE_ROOT': 'UNIX_LOCAL'
        },
        'UNIX_REMOTE': {
            'ADB_SHELL_ROOT': 'ADB_SHELL',
            'NOT_CONNECTED': 'UNIX_LOCAL',
            'UNIX_LOCAL_ROOT': 'UNIX_LOCAL'
        },
        'UNIX_REMOTE_ROOT': {
            'ADB_SHELL': 'UNIX_REMOTE',
            'ADB_SHELL_ROOT': 'UNIX_REMOTE',
            'NOT_CONNECTED': 'UNIX_REMOTE',
            'UNIX_LOCAL': 'UNIX_REMOTE',
            'UNIX_LOCAL_ROOT': 'UNIX_REMOTE'
        }
    }

    current_hops = remove_state_hops_from_sm(source_hops, "PROXY_PC")
    assert expected_hops == current_hops
