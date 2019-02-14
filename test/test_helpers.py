# -*- coding: utf-8 -*-
"""
Tests for helpers functions/classes.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import mock
import pytest


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
