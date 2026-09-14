# -*- coding: utf-8 -*-
"""
AT+GTCCINFO?

AT commands specification:
google for: Fibocom AT Commands Manual MBB v2.4
(always check against latest version of standard)
"""

__author__ = "Jakub Kochaniak"
__copyright__ = "Copyright (C) 2026, Nokia"
__email__ = "jakub.kochaniak@nokia.com"

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class FibocomGetCellInfo(GenericAtCommand):
    class FibocomTechnology:
        NONE = None
        UMTS = "UMTS"
        LTE = "LTE"
        NR = "NR"
        LTE_NR_EN_DC = "LTE-NR EN-DC"

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Create instance of FibocomGetCellInfo class and command to get information about detected cell.
        Verify with the latest Fibocom AT Commands Manual MBB v2.4.

        Example output for no cell detected:

        +GTCCINFO:
        <is_service_cell=2>,0,0,00,FFFF,0,0,,127,,,,,,,,,,,,,,,,

        OK

        General template for output of cell information:

        +GTCCINFO:
        [<technology> service cell:
        <is_service_cell=1>,<rest_of_cell_info>]

        [<technology> neighbor cell:
        <is_service_cell=2>,<rest_of_cell_info>]

        OK

        NOTE: <technology> is one of the following: UMTS, LTE, NR, LTE-NR EN-DC.

        NOTE: <rest_of_cell_info> is a comma-separated list of values specified for the given <technology>.

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(FibocomGetCellInfo, self).__init__(
            connection,
            operation="execute",
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.current_ret["raw_output"] = (
            ""  # command output may vary and it is multiline
        )
        self.current_ret["cells"] = []
        self._technology = self.FibocomTechnology.NONE
        self._is_service_cell = None
        # Helpers for sequential parsing:
        self.__lte_nr_primary = (
            True  # when LTE-NR EN-DC is detected, the 1st cell is always primary
        )

    def build_command_string(self):
        return "AT+GTCCINFO?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +GTCCINFO:
        [<technology> service cell:]
        [<is_service_cell=1,2>,<rest_of_cell_info>]

        [<technology> neighbor cell:
        <is_service_cell=2>,<rest_of_cell_info>]

        OK

        :param line: Line to parse, new lines are trimmed
        :param is_full_line: False for chunk of line; True on full line
        :return: None
        """
        if is_full_line:
            try:
                self._parse_no_cells_data(line)
                self._parse_service_cell_technology(line)
                self._parse_raw_data(line)
            except ParsingDone:
                pass
        return super(FibocomGetCellInfo, self).on_new_line(line, is_full_line)

    # <technology> <detected_as=service|neighbor> cell:
    _re_service_cell_technology = re.compile(
        r"^\s*(?P<technology>[\dA-Za-z-\s]{2,})\s+(?P<detected_as>(service|neighbor))\s+cell\s*:\s*$"
    )

    # (<technology> <detected_as=service|neighbor> cell:)
    # <raw_output=<is_service_cell>,<rest_of_cell_info>>
    # or for empty cell (no cells detected):  <is_service_cell=2>,0,0,00,FFFF,0,0,,127,,,,,,,,,,,,,,,,
    _re_raw_data = re.compile(r"^\s*(?P<raw_output>([\d\w]*\,){10,}[\d\w]*)\s*$")

    def _parse_no_cells_data(self, line):
        """
        Parse information about no detected cells:
        +GTCCINFO:
        <is_service_cell=2>,0,0,00,FFFF,0,0,,127,,,,,,,,,,,,,,,,
        """
        # `results_keys` is a list of common ordered keys for all technologies,
        # it is shorter then the list from raw output, but in that case (no cells)
        # the values are guaranteed to be not provided (or empty values) in result.
        if (
            self._regex_helper.match_compiled(self._re_raw_data, line) and not self._technology
        ):
            result_keys = self.__get_result_keys_for_matched_cell_info_line()
            string_raw_output = self._regex_helper.groupdict().get("raw_output")
            self.current_ret["raw_output"] += string_raw_output
            cell_info_current_ret = self.__convert_raw_output_to_cell_info_dict(
                string_raw_output, result_keys
            )
            self.current_ret["cells"].append(cell_info_current_ret)
            raise ParsingDone

    def _parse_service_cell_technology(self, line):
        """
        Parse information about service cell:
        `<technology> <detected_as=service|neighbor> cell:`
        """
        if self._regex_helper.match_compiled(self._re_service_cell_technology, line):
            technology = self._regex_helper.groupdict().get("technology")
            detected_as = self._regex_helper.groupdict().get("detected_as")
            self._technology = technology
            self._is_service_cell = detected_as == "service"
            self.current_ret["raw_output"] += line + "\n"
            raise ParsingDone

    def _parse_raw_data(self, line):
        """
        Parse raw data for the current technology:

        - UMTS
        - LTE
        - NR
        - LTE-NR EN-DC

        and mode of operation:

        - service cell
        - neighbor cell
        """
        if (
            self._regex_helper.match_compiled(self._re_raw_data, line) and self._technology
        ):
            string_raw_output = self._regex_helper.groupdict().get("raw_output")
            self.current_ret["raw_output"] += string_raw_output + "\n"

            result_keys = self.__get_result_keys_for_matched_cell_info_line()
            cell_info_current_ret = self.__convert_raw_output_to_cell_info_dict(
                string_raw_output, result_keys
            )
            cell_info_current_ret["technology"] = self._technology
            self.current_ret["cells"].append(cell_info_current_ret)
            raise ParsingDone

    def __convert_raw_output_to_cell_info_dict(
        self, string_raw_output: str, result_keys: list
    ) -> dict:
        """
        Convert raw output to cell info dictionary.
        :param string_raw_output: Raw output string.
        :param result_keys: Result keys for the current technology and mode of operation.
        :return: Cell info dictionary.
        """
        force_str_keys = {"mcc", "mnc", "cell_id", "uarfcn", "earfcn", "narfcn"}
        list_output = string_raw_output.split(",")
        cell_info_current_ret = {}
        for index, item in enumerate(list_output):
            if not item:
                continue
            item = item.strip('"')
            try:
                keys = result_keys[index].split("|")  # Extra split uncommon keys
            except IndexError:
                break
            if item.isdigit() and not any(key in force_str_keys for key in keys):
                item = int(item)
            for key in keys:
                cell_info_current_ret[key] = item
        return cell_info_current_ret

    def __get_result_keys_for_matched_cell_info_line(self):
        """
        Get result keys for the current technology and mode of operation.
        """

        #  - UMTS service cell:
        #      <is_service_cell>,<rat>,<mcc>,<mnc>,<lac>,<cellid>,<uarfcn>,<psc>,<band>,<ecno>,
        #      <rscp>,<rac>,<rxlev>,<reserved>,<ec_io_lev>
        #  - UMTS neighbor cell:
        #      <is_service_cell>,<rat>,<mcc>,<mnc>,<lac>,<cellid>,<uarfcn>,<psc>,<cell_type>,
        #      <rank_pos>,<ranking_status>,<ecno>,<pathloss>,<rxlev>,<rscp>
        if self._technology == self.FibocomTechnology.UMTS:
            return (
                [
                    "is_service_cell",
                    "rat",
                    "mcc",
                    "mnc",
                    "lac",
                    "cell_id",
                    "uarfcn",
                    "psc",
                    "band",
                    "ecno",
                    "rscp",
                    "rac",
                    "rxlev",
                    "reserved",
                    "ec_io_lev",
                ]
                if self._is_service_cell
                else [
                    "is_service_cell",
                    "rat",
                    "mcc",
                    "mnc",
                    "lac",
                    "cell_id",
                    "uarfcn",
                    "psc",
                    "cell_type",
                    "rank_pos",
                    "ranking_status",
                    "ecno",
                    "pathloss",
                    "rxlev",
                    "rscp",
                ]
            )

        # - LTE service cell:
        #     <is_service_cell>,<rat>,<mcc>,<mnc>,<tac>,<cellid>,<earfcn>,<physicalcell_id>,
        #     <band>,<bandwidth>,<rssnr_value>,<rxlev>,<rsrp>,<rsrq>
        # - LTE neighbor cell:
        #     <is_service_cell>,<rat>,<mcc>,<mnc>,<tac>,<cellid>,<earfcn>,<physicalcell_id>,
        #     <bandwidth>,<rxlev>,<rsrp>,<rsrq>
        if self._technology == self.FibocomTechnology.LTE:
            return (
                [
                    "is_service_cell",
                    "rat",
                    "mcc",
                    "mnc",
                    "tac",
                    "cell_id",
                    "earfcn",
                    "physicalcell_id",
                    "band",
                    "bandwidth",
                    "rssnr_value",
                    "rxlev",
                    "rsrp",
                    "rsrq",
                ]
                if self._is_service_cell
                else [
                    "is_service_cell",
                    "rat",
                    "mcc",
                    "mnc",
                    "tac",
                    "cell_id",
                    "earfcn",
                    "physicalcell_id",
                    "bandwidth",
                    "rxlev",
                    "rsrp",
                    "rsrq",
                ]
            )

        # - NR service cell:
        #     <is_service_cell>,<rat>,<mcc>,<mnc>,<tac>,<cellid>,<narfcn>,<physicalcell_id>,
        #     <band>,<bandwidth>,<ss-sinr>,<rxlev>,<ss_rsrp>,<ss_rsrq>
        # - NR neighbor cell:
        #     <is_service_cell>,<rat>,<mcc>,<mnc>,<tac>,<cellid>,<narfcn>,<physicalcell_id>,
        #     <ss-sinr>,<rxlev>,<ss_rsrp>,<ss_rsrq>
        if self._technology == self.FibocomTechnology.NR:
            return (
                [
                    "is_service_cell",
                    "rat",
                    "mcc",
                    "mnc",
                    "tac",
                    "cell_id",
                    "narfcn",
                    "physicalcell_id",
                    "band",
                    "bandwidth",
                    "ss-sinr",
                    "rxlev",
                    "ss_rsrp",
                    "ss_rsrq",
                ]
                if self._is_service_cell
                else [
                    "is_service_cell",
                    "rat",
                    "mcc",
                    "mnc",
                    "tac",
                    "cell_id",
                    "narfcn",
                    "physicalcell_id",
                    "ss-sinr",
                    "rxlev",
                    "ss_rsrp",
                    "ss_rsrq",
                ]
            )

        # - LTE-NR EN-DC service cell:
        #     <is_service_cell>,<rat>,<mcc>,<mnc>,<tac>,<cellid>,<earfcn>,<physicalcell_id>,
        #     <band>,<bandwidth>,<rssnr_value>,<rxlev>,<rsrp>,<rsrq>
        #     <is_service_cell>,<rat>,<mcc>,<mnc>,<tac>,<cellid>,<narfcn>,<physicalcell_id>,
        #     <band>,<bandwidth>,<ss-sinr>,<rxlev>,<ss_rsrp>,<ss_rsrq>
        # - neighbor cell is detected as for LTE
        if self._technology == self.FibocomTechnology.LTE_NR_EN_DC:
            if self._is_service_cell:
                if self.__lte_nr_primary:
                    result_keys = [
                        "is_service_cell",
                        "rat",
                        "mcc",
                        "mnc",
                        "tac",
                        "cell_id",
                        "earfcn",
                        "physicalcell_id",
                        "band",
                        "bandwidth",
                        "rssnr_value",
                        "rxlev",
                        "rsrp",
                        "rsrq",
                    ]
                else:
                    result_keys = [
                        "is_service_cell",
                        "rat",
                        "mcc",
                        "mnc",
                        "tac",
                        "cell_id",
                        "narfcn",
                        "physicalcell_id",
                        "band",
                        "bandwidth",
                        "ss-sinr",
                        "rxlev",
                        "ss_rsrp",
                        "ss_rsrq",
                    ]
                self.__lte_nr_primary = not self.__lte_nr_primary
                return result_keys

        # - no cell detected (self._technology == self.FibocomTechnology.NONE)
        return [
            "is_service_cell",
            "rat",
            "mcc",
            "mnc",
            "tac|lac",
            "cell_id",
            "uarfcn|earfcn|narfcn",
            "physicalcell_id|psc",
        ]


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

COMMAND_OUTPUT_get_cell_info_no_cells = """
AT+GTCCINFO?
+GTCCINFO:
2,0,0,00,FFFF,0,0,,127,,,,,,,,,,,,,,,,

OK
"""

COMMAND_KWARGS_get_cell_info_no_cells = {}

COMMAND_RESULT_get_cell_info_no_cells = {
    "raw_output": "2,0,0,00,FFFF,0,0,,127,,,,,,,,,,,,,,,,",
    "cells": [
        {
            "is_service_cell": 2,
            "rat": 0,
            "mcc": "0",
            "mnc": "00",
            "lac": "FFFF",
            "tac": "FFFF",
            "cell_id": "0",
            "uarfcn": "0",
            "earfcn": "0",
            "narfcn": "0",
        },
    ],
}


COMMAND_OUTPUT_get_cell_info_nr_cells = """
AT+GTCCINFO?
+GTCCINFO:
NR service cell:
1,9,001,01,1,2FC001,1ECC5B,1,50258,100,109,112,112,64

NR neighbor cell:
2,9,001,01,1,2FC001,1ECC5B,1,109,112,112,64

OK
"""

COMMAND_KWARGS_get_cell_info_nr_cells = {}

COMMAND_RESULT_get_cell_info_nr_cells = {
    "raw_output": """NR service cell:
1,9,001,01,1,2FC001,1ECC5B,1,50258,100,109,112,112,64
NR neighbor cell:
2,9,001,01,1,2FC001,1ECC5B,1,109,112,112,64
""",
    "cells": [
        {
            "is_service_cell": 1,
            "rat": 9,
            "mcc": "001",
            "mnc": "01",
            "tac": 1,
            "cell_id": "2FC001",
            "narfcn": "1ECC5B",
            "physicalcell_id": 1,
            "band": 50258,
            "bandwidth": 100,
            "ss-sinr": 109,
            "rxlev": 112,
            "ss_rsrp": 112,
            "ss_rsrq": 64,
            "technology": "NR",
        },
        {
            "is_service_cell": 2,
            "rat": 9,
            "mcc": "001",
            "mnc": "01",
            "tac": 1,
            "cell_id": "2FC001",
            "narfcn": "1ECC5B",
            "physicalcell_id": 1,
            "ss-sinr": 109,
            "rxlev": 112,
            "ss_rsrp": 112,
            "ss_rsrq": 64,
            "technology": "NR",
        },
    ],
}


COMMAND_OUTPUT_get_cell_info_umts_cells = """
AT+GTCCINFO?
+GTCCINFO:
UMTS service cell:
1,3,551,01,1,2FC001,36410,1,900,100,109,112,112,64
UMTS neighbor cell:
2,3,551,02,1,2FC999,36411,1,1800,101,110,113,113,65

OK
"""

COMMAND_KWARGS_get_cell_info_umts_cells = {}

COMMAND_RESULT_get_cell_info_umts_cells = {
    "raw_output": """UMTS service cell:
1,3,551,01,1,2FC001,36410,1,900,100,109,112,112,64
UMTS neighbor cell:
2,3,551,02,1,2FC999,36411,1,1800,101,110,113,113,65
""",
    "cells": [
        {
            "is_service_cell": 1,
            "rat": 3,
            "mcc": "551",
            "mnc": "01",
            "lac": 1,
            "cell_id": "2FC001",
            "uarfcn": "36410",
            "psc": 1,
            "band": 900,
            "ecno": 100,
            "rscp": 109,
            "rac": 112,
            "rxlev": 112,
            "reserved": 64,
            "technology": "UMTS",
        },
        {
            "is_service_cell": 2,
            "rat": 3,
            "mcc": "551",
            "mnc": "02",
            "lac": 1,
            "cell_id": "2FC999",
            "uarfcn": "36411",
            "psc": 1,
            "cell_type": 1800,
            "rank_pos": 101,
            "ranking_status": 110,
            "ecno": 113,
            "pathloss": 113,
            "rxlev": 65,
            "technology": "UMTS",
        },
    ],
}


COMMAND_OUTPUT_get_cell_info_lte_cells = """
AT+GTCCINFO?
+GTCCINFO:
LTE service cell:
1,4,551,01,1,2FC001,46410,1,1025,100,109,112,112,64

LTE neighbor cell:
2,4,551,02,1,2FC999,46411,1,101,110,113,65
2,4,551,01,1,2FC555,46410,1,102,107,111,62

OK
"""

COMMAND_KWARGS_get_cell_info_lte_cells = {}

COMMAND_RESULT_get_cell_info_lte_cells = {
    "raw_output": """LTE service cell:
1,4,551,01,1,2FC001,46410,1,1025,100,109,112,112,64
LTE neighbor cell:
2,4,551,02,1,2FC999,46411,1,101,110,113,65
2,4,551,01,1,2FC555,46410,1,102,107,111,62
""",
    "cells": [
        {
            "is_service_cell": 1,
            "rat": 4,
            "mcc": "551",
            "mnc": "01",
            "tac": 1,
            "cell_id": "2FC001",
            "earfcn": "46410",
            "physicalcell_id": 1,
            "band": 1025,
            "bandwidth": 100,
            "rssnr_value": 109,
            "rxlev": 112,
            "rsrp": 112,
            "rsrq": 64,
            "technology": "LTE",
        },
        {
            "is_service_cell": 2,
            "rat": 4,
            "mcc": "551",
            "mnc": "02",
            "tac": 1,
            "cell_id": "2FC999",
            "earfcn": "46411",
            "physicalcell_id": 1,
            "bandwidth": 101,
            "rxlev": 110,
            "rsrp": 113,
            "rsrq": 65,
            "technology": "LTE",
        },
        {
            "is_service_cell": 2,
            "rat": 4,
            "mcc": "551",
            "mnc": "01",
            "tac": 1,
            "cell_id": "2FC555",
            "earfcn": "46410",
            "physicalcell_id": 1,
            "bandwidth": 102,
            "rxlev": 107,
            "rsrp": 111,
            "rsrq": 62,
            "technology": "LTE",
        },
    ],
}


COMMAND_OUTPUT_get_cell_info_lte_nr_en_dc_cells = """
AT+GTCCINFO?
+GTCCINFO:
LTE-NR EN-DC service cell:
1,12,551,01,1,2FC001,46410,1,1025,100,109,112,112,64
1,12,551,02,1,2FC999,1ECC5B,1,50258,100,109,112,112,64

OK
"""

COMMAND_KWARGS_get_cell_info_lte_nr_en_dc_cells = {}

COMMAND_RESULT_get_cell_info_lte_nr_en_dc_cells = {
    "raw_output": """LTE-NR EN-DC service cell:
1,12,551,01,1,2FC001,46410,1,1025,100,109,112,112,64
1,12,551,02,1,2FC999,1ECC5B,1,50258,100,109,112,112,64
""",
    "cells": [
        {
            "is_service_cell": 1,
            "rat": 12,
            "mcc": "551",
            "mnc": "01",
            "tac": 1,
            "cell_id": "2FC001",
            "earfcn": "46410",
            "physicalcell_id": 1,
            "band": 1025,
            "bandwidth": 100,
            "rssnr_value": 109,
            "rxlev": 112,
            "rsrp": 112,
            "rsrq": 64,
            "technology": "LTE-NR EN-DC",
        },
        {
            "is_service_cell": 1,
            "rat": 12,
            "mcc": "551",
            "mnc": "02",
            "tac": 1,
            "cell_id": "2FC999",
            "narfcn": "1ECC5B",
            "physicalcell_id": 1,
            "band": 50258,
            "bandwidth": 100,
            "ss-sinr": 109,
            "rxlev": 112,
            "ss_rsrp": 112,
            "ss_rsrq": 64,
            "technology": "LTE-NR EN-DC",
        },
    ],
}
