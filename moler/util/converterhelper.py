# -*- coding: utf-8 -*-
"""
Units converter
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re


class ConverterHelper(object):
    _instance = None
    # examples of matched strings: 1K 1 .5M  3.2G
    _re_to_bytes = re.compile(r"(?P<VALUE>\d+\.?\d*|\.\d+)\s*(?P<UNIT>\w?)")
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

    _seconds_multipliers = {
        "h": 3600,
        "m": 60,
        "s": 1,
        "ms": 0.001,
        "us": 0.000001,
        "ns": 0.000000001,
    }

    def to_bytes(self, str_bytes, binary_multipliers=True):
        """
        Method to convert size with unit to size in bytes
        :param str_bytes: String with bytes and optional unit
        :param binary_multipliers: If True then binary multipliers will be used, if False then decimal
        :return: 3 values: int value in bytes, float value in units (parsed form string), String unit
        """
        m = re.search(ConverterHelper._re_to_bytes, str_bytes)
        value_str = m.group("VALUE")
        value_unit = m.group("UNIT")
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

    def to_seconds_str(self, str_time):
        """
        Method to convert string time with unit to seconds.
        :param str_time: String with time and unit.
        :return: 3 values: float value in seconds, float value in units (parsed form string), String unit
        """
        m = re.search(ConverterHelper._re_to_bytes, str_time)
        value_str = m.group("VALUE")
        value_unit = m.group("UNIT")
        value_in_units = float(value_str)
        value_in_seconds = value_in_units  # Default when not unit provided
        if value_unit:
            value_in_seconds = self.to_seconds(value_in_units, value_unit)
        return value_in_seconds, value_in_units, value_unit

    def to_seconds(self, value, unit):
        """
        Method to convert number of
        :param value: numeric value in units
        :param unit: Unit of time, h for hour
        :return: number of seconds
        """
        if unit not in ConverterHelper._seconds_multipliers:
            raise ValueError("Unsupported unit '{}' for passed value: '{}'".format(unit, value))
        return ConverterHelper._seconds_multipliers[unit] * value

    def to_number(self, value, raise_exception=True):
        """
        Convert number to int or float.

        :param value: string with number inside
        :param raise_exception: if True then raise exception if cannot convert to number, If False then return 0.
        :return: int or float with value.
        """
        ret_val = 0
        try:
            ret_val = int(value)
        except ValueError:
            try:
                ret_val = float(value)
            except ValueError as ex:
                if raise_exception:
                    raise ex
        return ret_val

    @staticmethod
    def get_converter_helper():
        if ConverterHelper._instance is None:
            ConverterHelper._instance = ConverterHelper()
        return ConverterHelper._instance
