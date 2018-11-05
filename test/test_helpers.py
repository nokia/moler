# -*- coding: utf-8 -*-
"""
Tests for helpers functions/classes.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import mock


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
