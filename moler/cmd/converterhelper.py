# -*- coding: utf-8 -*-
"""
Units converter
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re


class ConverterHelper(object):
    instance = None
    # examples of matched strings: 1K 1 .5M  3.2G
    _re_to_bytes = re.compile(r"(\d+\.?\d*|\.\d+)\s*(\w?)")
    _binary_multipliers = {
        "k": 1024,
        "m": 1024 * 1024,
        "g": 1024 * 1024 * 1024,
        "t": 1024 * 1024 * 1024 * 1024,
        "p": 1024 * 1024 * 1024 * 1024 * 1024,
        "e": 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
        "z": 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
        "j": 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
    }
    _dec_multipliers = {
        "k": 1000,
        "m": 1000 * 1000,
        "g": 1000 * 1000 * 1000,
        "t": 1000 * 1000 * 1000 * 1000,
        "p": 1000 * 1000 * 1000 * 1000 * 1000,
        "e": 1000 * 1000 * 1000 * 1000 * 1000 * 1000,
        "z": 1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000,
        "j": 1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000,
    }

    def to_bytes(self, str_bytes, binary_multipliers=True):
        """
        Method to convert size with unit to size in bytes
        :param str_bytes: String with bytes and optional unit
        :param binary_multipliers: If True then binary multipliers will be used, if False then decimal
        :return: 3 values: int value in bytes, float value in units (parsed form string), String unit
        """
        m = re.search(ConverterHelper._re_to_bytes, str_bytes)
        value_str = m.group(1)
        value_unit = m.group(2)
        value_in_units = float(value_str)
        value_in_bytes = int(value_in_units)  # Default when not unit provided
        if value_unit:
            multipliers = ConverterHelper._binary_multipliers
            if not binary_multipliers:
                multipliers = ConverterHelper._dec_multipliers
            value_unit = value_unit.lower()
            if value_unit in multipliers:
                value_in_bytes = int(multipliers[value_unit] * value_in_units)
            else:
                raise ValueError("Unsupported unit '{}' in passed value: '{}'".format(value_unit, str_bytes))
        return value_in_bytes, value_in_units, value_unit

    @staticmethod
    def get_converter_helper():
        if ConverterHelper.instance is None:
            ConverterHelper.instance = ConverterHelper()
        return ConverterHelper.instance
