# -*- coding: utf-8 -*-
"""
AT+CGPADDR

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


class GetIp(GenericAtCommand):
    """
    Command to get IP. Example output:

    +CGPADDR: 1,0.0.0.0,0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0

    OK
    """

    def __init__(
        self,
        context_identifier,
        connection=None,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        """Create instance of GetIp class"""
        super(GetIp, self).__init__(
            connection,
            operation="execute",
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.context_identifier = context_identifier
        self.current_ret = {}

    def build_command_string(self):
        return f"AT+CGPADDR={self.context_identifier}"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        +CGPADDR: 1,"40.1.1.105"

        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_ip(line)
            except ParsingDone:
                pass
        return super(GetIp, self).on_new_line(line, is_full_line)

    # +CGPADDR: 1,"40.1.1.105"
    _re_apn = re.compile(
        r"^\s*\+CGPADDR:\s[0-9]+,\"?(?P<ip>(([0-9]{1,3}\.){3}[0-9]{1,3}))\"?.*$"
    )

    def _parse_ip(self, line):
        """
        Parse IP that should look like:

        +CGPADDR: 1,"40.1.1.105"
        or
        +CGPADDR: 1,0.0.0.0,0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0
        """
        if self._regex_helper.match_compiled(self._re_apn, line):
            ip = self._regex_helper.group("ip")
            self.current_ret["ip"] = ip
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

COMMAND_OUTPUT_no_ip = """
AT+CGPADDR=1
+CGPADDR: 1,0.0.0.0,0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0

OK
"""

COMMAND_KWARGS_no_ip = {"context_identifier": 1}

COMMAND_RESULT_no_ip = {"ip": "0.0.0.0"}

COMMAND_OUTPUT_ip = """
AT+CGPADDR=1
+CGPADDR: 1,"40.1.1.105"

OK
"""

COMMAND_KWARGS_ip = {"context_identifier": 1}

COMMAND_RESULT_ip = {"ip": "40.1.1.105"}
