# -*- coding: utf-8 -*-
"""
Units converter
"""

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2018-2024, Nokia"
__email__ = "marcin.usielski@nokia.com"

import re
import warnings
from datetime import datetime

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from dateutil import parser  # https://github.com/aws/jsii/issues/4406


class ConverterHelper:
    _instance = None
    # examples of matched strings: 1K 1 .5M  3.2G
    _re_to_bytes = re.compile(r"(?P<VALUE>\d+\.?\d*|\.\d+)\s*(?P<UNIT>\w?)")

    # 'b' stands for no decimal and binary prefix
    _binary_multipliers = {
        "b": 1,
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
        "b": 1,
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

    _time_zones = {
        "ACDT": "UTC+10:30",
        "ACST": "UTC+09:30",
        "ACT": "UTC-05",  # "UTC+08:00",  # ACT has two different meanings
        "ACWST": "UTC+08:45",
        "ADT": "UTC-03",
        "AEDT": "UTC+11",
        "AEST": "UTC+10",
        "AET": "UTC+10",  # "UTC+11",  # AET has two different meanings
        "AFT": "UTC+04:30",
        "AKDT": "UTC-08",
        "AKST": "UTC-09",
        "ALMT": "UTC+06",
        "AMST": "UTC-03",
        "AMT": "UTC-04",  # "UTC+04",  # AMT has two different meanings
        "ANAT": "UTC+12",
        "AQTT": "UTC+05",
        "ART": "UTC-03",
        "AST": "UTC+03",  # "UTC-04",  # AST has two different meanings
        "AWST": "UTC+08",
        "AZOST": "UTC±00",
        "AZOT": "UTC-01",
        "AZT": "UTC+04",
        "BNT": "UTC+08",
        "BIOT": "UTC+06",
        "BIT": "UTC-12",
        "BOT": "UTC-04",
        "BRST": "UTC-02",
        "BRT": "UTC-03",
        "BST": "UTC+06",  # "UTC+11", "UTC+01",  # BST has three different meanings
        "BTT": "UTC+06",
        "CAT": "UTC+02",
        "CCT": "UTC+06:30",
        "CDT": "UTC-05",  # "UTC-04",  # CDT has two different meanings
        "CEST": "UTC+02",
        "CET": "UTC+01",
        "CHADT": "UTC+13:45",
        "CHAST": "UTC+12:45",
        "CHOT": "UTC+08",
        "CHOST": "UTC+09",
        "CHST": "UTC+10",
        "CHUT": "UTC+10",
        "CIST": "UTC-08",
        "CKT": "UTC-10",
        "CLST": "UTC-03",
        "CLT": "UTC-04",
        "COST": "UTC-04",
        "COT": "UTC-05",
        "CST": "UTC-06",  # "UTC+08", "UTC-05"],  # CST has three different meanings
        "CT": "UTC-06",  # "UTC-05"],  # CT has two different meanings
        "CVT": "UTC-01",
        "CWST": "UTC+08:45",
        "CXT": "UTC+07",
        "DAVT": "UTC+07",
        "DDUT": "UTC+10",
        "DFT": "UTC+01",
        "EASST": "UTC-05",
        "EAST": "UTC-06",
        "EAT": "UTC+03",
        "ECT": "UTC-04",  # "UTC-05"],  # ECT has two different meanings
        "EDT": "UTC-04",
        "EEST": "UTC+03",
        "EET": "UTC+02",
        "EGST": "UTC±00",
        "EGT": "UTC-01",
        "EST": "UTC-05",
        "ET": "UTC-05",  # "UTC-04"],  # ET has two different meanings
        "FET": "UTC+03",
        "FJT": "UTC+12",
        "FKST": "UTC-03",
        "FKT": "UTC-04",
        "FNT": "UTC-02",
        "GALT": "UTC-06",
        "GAMT": "UTC-09",
        "GET": "UTC+04",
        "GFT": "UTC-03",
        "GILT": "UTC+12",
        "GIT": "UTC-09",
        "GMT": "UTC±00",
        "GST": "UTC-02",  # "UTC+04"],  # GST has two different meanings
        "GYT": "UTC-04",
        "HDT": "UTC-09",
        "HAEC": "UTC+02",
        "HST": "UTC-10",
        "HKT": "UTC+08",
        "HMT": "UTC+05",
        "HOVST": "UTC+08",
        "HOVT": "UTC+07",
        "ICT": "UTC+07",
        "IDLW": "UTC-12",
        "IDT": "UTC+03",
        "IOT": "UTC+06",
        "IRDT": "UTC+04:30",
        "IRKT": "UTC+08",
        "IRST": "UTC+03:30",
        "IST": "UTC+05:30",  # "UTC+01", "UTC+02"],  # IST has three different meanings
        "JST": "UTC+09",
        "KALT": "UTC+02",
        "KGT": "UTC+06",
        "KOST": "UTC+11",
        "KRAT": "UTC+07",
        "KST": "UTC+09",
        "LHST": "UTC+10:30",  # "UTC+11"],  # LHST has two different meanings
        "LINT": "UTC+14",
        "MAGT": "UTC+12",
        "MART": "UTC-09:30",
        "MAWT": "UTC+05",
        "MDT": "UTC-06",
        "MET": "UTC+01",
        "MEST": "UTC+02",
        "MHT": "UTC+12",
        "MIST": "UTC+11",
        "MIT": "UTC-09:30",
        "MMT": "UTC+06:30",
        "MSK": "UTC+03",
        "MST": "UTC+08",  # "UTC-07"],  # MST has two different meanings
        "MT": "UTC-07",  # "UTC-06"],  # MT has two different meanings
        "MUT": "UTC+04",
        "MVT": "UTC+05",
        "MYT": "UTC+08",
        "NCT": "UTC+11",
        "NDT": "UTC-02:30",
        "NFT": "UTC+11",
        "NOVT": "UTC+07",
        "NPT": "UTC+05:45",
        "NST": "UTC-03:30",
        "NT": "UTC-03:30",
        "NUT": "UTC-11",
        "NZDT": "UTC+13",
        "NZST": "UTC+12",
        "OMST": "UTC+06",
        "ORAT": "UTC+05",
        "PDT": "UTC-07",
        "PET": "UTC-05",
        "PETT": "UTC+12",
        "PGT": "UTC+10",
        "PHOT": "UTC+13",
        "PHT": "UTC+08",
        "PHST": "UTC+08",
        "PKT": "UTC+05",
        "PMDT": "UTC-02",
        "PMST": "UTC-03",
        "PONT": "UTC+11",
        "PST": "UTC-08",
        "PT": "UTC-08",  # "UTC-07"],  # PT has two different meanings
        "PWT": "UTC+09",
        "PYST": "UTC-03",
        "PYT": "UTC-04",
        "RET": "UTC+04",
        "ROTT": "UTC-03",
        "SAKT": "UTC+11",
        "SAMT": "UTC+04",
        "SAST": "UTC+02",
        "SBT": "UTC+11",
        "SCT": "UTC+04",
        "SDT": "UTC-10",
        "SGT": "UTC+08",
        "SLST": "UTC+05:30",
        "SRET": "UTC+11",
        "SRT": "UTC-03",
        "SST": "UTC-11",  # "UTC+08"],  # SST has two different meanings
        "SYOT": "UTC+03",
        "TAHT": "UTC-10",
        "THA": "UTC+07",
        "TFT": "UTC+05",
        "TJT": "UTC+05",
        "TKT": "UTC+13",
        "TLT": "UTC+09",
        "TMT": "UTC+05",
        "TRT": "UTC+03",
        "TOT": "UTC+13",
        "TST": "UTC+08",
        "TVT": "UTC+12",
        "ULAST": "UTC+09",
        "ULAT": "UTC+08",
        "UTC": "UTC±00",
        "UYST": "UTC-02",
        "UYT": "UTC-03",
        "UZT": "UTC+05",
        "VET": "UTC-04",
        "VLAT": "UTC+10",
        "VOLT": "UTC+03",
        "VOST": "UTC+06",
        "VUT": "UTC+11",
        "WAKT": "UTC+12",
        "WAST": "UTC+02",
        "WAT": "UTC+01",
        "WEST": "UTC+01",
        "WET": "UTC±00",
        "WIB": "UTC+07",
        "WIT": "UTC+09",
        "WITA": "UTC+08",
        "WGST": "UTC-02",
        "WGT": "UTC-03",
        "WST": "UTC+08",
        "YAKT": "UTC+09",
        "YEKT": "UTC+05",
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
                raise ValueError(
                    f"Unsupported unit '{value_unit}' in passed value: '{str_bytes}'"
                )
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
            raise ValueError(f"Unsupported unit '{unit}' for passed value: '{value}'")
        return ConverterHelper._seconds_multipliers[unit] * value

    def to_number(self, value, raise_exception: bool = True, none_if_cannot_convert: bool = False):
        """
        Convert number to int or float.

        :param value: string with number inside
        :param raise_exception: if True then raise exception if cannot convert to number, If False then return 0.
        :param none_if_cannot_convert: If True and obj is not int then return None
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
                if none_if_cannot_convert:
                    ret_val = None
        return ret_val

    @staticmethod
    def get_converter_helper():
        if ConverterHelper._instance is None:
            ConverterHelper._instance = ConverterHelper()
        return ConverterHelper._instance

    @classmethod
    def parse_date(cls, date: str, tzinfos=None) -> datetime:
        """
        Parse date string to datetime object.

        :param date: date string
        :param tzinfos: dict with time zones
        :return: datetime object
        """
        if tzinfos is None:
            tzinfos = cls._time_zones
        return parser.parse(date, tzinfos=tzinfos)
