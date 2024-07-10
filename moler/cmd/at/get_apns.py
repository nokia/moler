# -*- coding: utf-8 -*-
"""
AT+CGDCONT

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


class GetApns(GenericAtCommand):
    """
    Command to get APNs. Example output:

    +CGDCONT: 1,"IPV4V6","apnscp1","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
    +CGDCONT: 2,"IPV4V6","","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
    +CGDCONT: 3,"IPV4V6","ims","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
    +CGDCONT: 4,"IPV4V6","sos","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,1
    +CGDCONT: 5,"IPV4V6","xcap","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0

    OK
    """

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetApns class"""
        super(GetApns, self).__init__(
            connection,
            operation="execute",
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.current_ret = []

    def build_command_string(self):
        return "AT+CGDCONT?"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +CGDCONT: 1,"IPV4V6","apnscp1","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
        +CGDCONT: 2,"IPV4V6","","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
        +CGDCONT: 3,"IPV4V6","ims","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
        +CGDCONT: 4,"IPV4V6","sos","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,1
        +CGDCONT: 5,"IPV4V6","xcap","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_apns(line)
            except ParsingDone:
                pass
        return super(GetApns, self).on_new_line(line, is_full_line)

    # +CGDCONT: 1,"IPV4V6","apnscp1","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
    # +CGDCONT: 1,"IPV4V6","apn1-ips-05","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0,,,,,,,,,"",,,,0
    _re_apn = re.compile(
        r"^\s*\+CGDCONT\:\s(?P<apn_num>([0-9]+)),\"(?P<apn_ip_name>(IP(V4V6)?))\",\""
        '(?P<apn_name>([a-zA-Z0-9-]*))".*$'
    )

    def _parse_apns(self, line):
        """
        Parse APN that should look like:

        +CGDCONT: 1,"IPV4V6","apnscp1","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
        """
        if self._regex_helper.match_compiled(self._re_apn, line):
            apn_num = self._regex_helper.group("apn_num")
            apn_ip_name = self._regex_helper.group("apn_ip_name")
            apn_name = self._regex_helper.group("apn_name")
            apn_dict = {
                "apn_num": apn_num,
                "apn_ip_name": apn_ip_name,
                "apn_name": apn_name,
            }
            self.current_ret.append(apn_dict)
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

COMMAND_OUTPUT_ipv4v6 = """
AT+CGDCONT?
+CGDCONT: 1,"IPV4V6","apnscp1","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
+CGDCONT: 2,"IPV4V6","","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
+CGDCONT: 3,"IPV4V6","ims","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
+CGDCONT: 4,"IPV4V6","sos","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,1
+CGDCONT: 5,"IPV4V6","xcap","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
+CGDCONT: 6,"IPV4V6","apn1-ips-05","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0,,,,,,,,,"",,,,0

OK
"""

COMMAND_KWARGS_ipv4v6 = {}

COMMAND_RESULT_ipv4v6 = [
    {"apn_num": "1", "apn_ip_name": "IPV4V6", "apn_name": "apnscp1"},
    {"apn_num": "2", "apn_ip_name": "IPV4V6", "apn_name": ""},
    {"apn_num": "3", "apn_ip_name": "IPV4V6", "apn_name": "ims"},
    {"apn_num": "4", "apn_ip_name": "IPV4V6", "apn_name": "sos"},
    {"apn_num": "5", "apn_ip_name": "IPV4V6", "apn_name": "xcap"},
    {"apn_num": "6", "apn_ip_name": "IPV4V6", "apn_name": "apn1-ips-05"},
]

COMMAND_OUTPUT_ip = """
AT+CGDCONT?
+CGDCONT: 1,"IP","","0.0.0.0",0,0,0,0
+CGDCONT: 2,"IPV4V6","","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0
+CGDCONT: 3,"IPV4V6","","0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0",0,0,0,0

OK
"""

COMMAND_KWARGS_ip = {}

COMMAND_RESULT_ip = [
    {"apn_num": "1", "apn_ip_name": "IP", "apn_name": ""},
    {"apn_num": "2", "apn_ip_name": "IPV4V6", "apn_name": ""},
    {"apn_num": "3", "apn_ip_name": "IPV4V6", "apn_name": ""},
]
