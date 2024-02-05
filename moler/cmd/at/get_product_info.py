# -*- coding: utf-8 -*-
"""
ATI

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = "Adam Klekowski"
__copyright__ = "Copyright (C) 2020, Nokia"
__email__ = "adam.klekowski@nokia.com"

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class GetProductInfo(GenericAtCommand):
    """
    Command to get product information. Example output:

    Manufacturer: QUALCOMM INCORPORATED
    Model: 334
    Revision:
    OEM_VER: RTL6300_NOKIA_V0.0.3_201116.1_m
    OEM_BLD: master@dailybuild2, 11/16/2020 05:56:34
    QC_VER: MPSS.HI.2.0.c3-00246-SDX55_CPEALL_PACK-1
    IMEI: 352569090027192
    +GCAP: +CGSM

    OK
    """

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetProductInfo class"""
        super(GetProductInfo, self).__init__(
            connection,
            operation="execute",
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.current_ret = {}

    def build_command_string(self):
        return "ATI"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        Manufacturer: QUALCOMM INCORPORATED
        Model: 334
        Revision:
        OEM_VER: RTL6300_NOKIA_V0.0.3_201116.1_m
        OEM_BLD: master@dailybuild2, 11/16/2020 05:56:34
        QC_VER: MPSS.HI.2.0.c3-00246-SDX55_CPEALL_PACK-1
        IMEI: 352569090027192
        +GCAP: +CGSM

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_product_information(line)
            except ParsingDone:
                pass
        return super(GetProductInfo, self).on_new_line(line, is_full_line)

    # Manufacturer: QUALCOMM INCORPORATED
    _re_product_information = re.compile(
        r"^(?P<key>([^\:\n]+))\:( )*(?P<value>([^\n]+))$"
    )

    def _parse_product_information(self, line):
        """
        Parse product information that should look like:

        Manufacturer: QUALCOMM INCORPORATED
        Model: 334
        Revision:
        OEM_VER: RTL6300_NOKIA_V0.0.3_201116.1_m
        OEM_BLD: master@dailybuild2, 11/16/2020 05:56:34
        QC_VER: MPSS.HI.2.0.c3-00246-SDX55_CPEALL_PACK-1
        IMEI: 352569090027192
        +GCAP: +CGSM
        """
        if self._regex_helper.match_compiled(self._re_product_information, line):
            self.current_ret[
                self._regex_helper.group("key")
            ] = self._regex_helper.group("value")
            raise ParsingDone


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
#
# Moreover, it documents what will be COMMAND_RESULT when command
# is run with COMMAND_KWARGS on COMMAND_OUTPUT data coming from connection.
#
# When you need to show parsing of multiple outputs just add suffixes:
# COMMAND_OUTPUT_suffix
# COMMAND_KWARGS_suffix
# COMMAND_RESULT_suffix
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_askey = """
ATI
Manufacturer: QUALCOMM INCORPORATED
Model: 334
Revision:
OEM_VER: RTL6300_NOKIA_V0.0.3_201116.1_m
OEM_BLD: master@dailybuild2, 11/16/2020 05:56:34
QC_VER: MPSS.HI.2.0.c3-00246-SDX55_CPEALL_PACK-1
IMEI: 352569090027192
+GCAP: +CGSM

OK
"""

COMMAND_KWARGS_askey = {}

COMMAND_RESULT_askey = {
    "Manufacturer": "QUALCOMM INCORPORATED",
    "Model": "334",
    "OEM_VER": "RTL6300_NOKIA_V0.0.3_201116.1_m",
    "OEM_BLD": "master@dailybuild2, 11/16/2020 05:56:34",
    "QC_VER": "MPSS.HI.2.0.c3-00246-SDX55_CPEALL_PACK-1",
    "IMEI": "352569090027192",
    "+GCAP": "+CGSM",
}

COMMAND_OUTPUT_nokia = """
ATI
Manufacturer: QUALCOMM INCORPORATED
Model: 334
Revision: MPSS.HI.2.0.5-00162.3-SAIPAN_GEN_PACK-1  1  [May 15 2020 07:00:00]
SVN: 01
IMEI: 353139110019915
+GCAP: +CGSM,+DS,+ES

OK
"""

COMMAND_KWARGS_nokia = {}

COMMAND_RESULT_nokia = {
    "Manufacturer": "QUALCOMM INCORPORATED",
    "Model": "334",
    "Revision": "MPSS.HI.2.0.5-00162.3-SAIPAN_GEN_PACK-1  1  [May 15 2020 07:00:00]",
    "SVN": "01",
    "IMEI": "353139110019915",
    "+GCAP": "+CGSM,+DS,+ES",
}

COMMAND_OUTPUT_inseego = """
ATI
Manufacturer: Inseego Corp.
Model: M2000A
Revision: 1.36  SVN 1 [2020-07-31 18:38:02] (Release Build - nvtl)
SVN: 01
IMEI: 990016250011564
+GCAP: +CLTE3, +MS, +ES, +DS

OK
"""

COMMAND_KWARGS_inseego = {}

COMMAND_RESULT_inseego = {
    "Manufacturer": "Inseego Corp.",
    "Model": "M2000A",
    "Revision": "1.36  SVN 1 [2020-07-31 18:38:02] (Release Build - nvtl)",
    "SVN": "01",
    "IMEI": "990016250011564",
    "+GCAP": "+CLTE3, +MS, +ES, +DS",
}
