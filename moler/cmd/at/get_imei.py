# -*- coding: utf-8 -*-
"""
AT+CGSN .

AT commands specification:
google for: 3gpp specification 27.007
(always check against latest version of standard)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re

from moler.cmd.at.genericat import GenericAtCommand
from moler.exceptions import ParsingDone


class GetImei(GenericAtCommand):
    """
    Command to get product serial number identification. Example output:

    AT+CGSN
    490154203237518

    AT+CGSN=1
    +CGSN: "490154203237518"
    OK
    """

    def __init__(self, connection=None, sn_type="default", prompt=None, newline_chars=None, runner=None):
        """
        Create instance of GetImei class

        See 3gpp documentation for SN type values:

        <snt>: integer type indicating the serial number type that has been requested.
        0 returns <sn> Serial Number as defined by manufacturer, typically it is IMEI
        1 returns the IMEI (International Mobile station Equipment Identity)
        2 returns the IMEISV (International Mobile station Equipment Identity and Software Version number)
        3 returns the SVN (Software Version Number)

        :param sn_type: "default", "imei", "imeisv", "svn"
        """
        super(GetImei, self).__init__(connection, operation='execute', prompt=prompt,
                                      newline_chars=newline_chars, runner=runner)
        self.sn_type = sn_type

    _serial_variants = {"default": "AT+CGSN",
                        "imei": "AT+CGSN=1",
                        "imeisv": "AT+CGSN=1",
                        "svn": "AT+CGSN=2"}

    def build_command_string(self):
        cmd = self._serial_variants[self.sn_type]
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        490154203237518

        or

        +CGSN: "490154203237518"
        OK

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_imei(line)
            except ParsingDone:
                pass
        return super(GetImei, self).on_new_line(line, is_full_line)

    _re_sn = re.compile(r'^\s*(?P<sn>\S.*)\s*$')
    _re_imei = re.compile(r'^\s*\+CGSN: "(?P<tac>\d{8})(?P<snr>\d{6})(?P<cd>\d{1})"\s*$')  # taken from standard
    _re_imeisv = re.compile(r'(?P<tac>\d{8})(?P<snr>\d{6})(?P<svn>\d{2})')  # TODO: need real output example
    _re_svn = re.compile(r'(?P<svn>\d{2})')  # TODO: need real output example

    def _parse_imei(self, line):
        """
        Parse serial_number identification that may look like:

        490154203237518

        or

        +CGSN: "490154203237518"
        """
        if self.sn_type == 'default':
            if self._regex_helper.match_compiled(self._re_sn, line):
                sn = self._regex_helper.group("sn")
                self.current_ret['imei'] = sn
                raise ParsingDone

        elif self.sn_type == 'imei':
            if self._regex_helper.match_compiled(self._re_imei, line):
                imei_parts = self._regex_helper.groupdict()
                self.current_ret.update(imei_parts)
                self.current_ret["imei"] = "{}{}{}".format(imei_parts["tac"], imei_parts["snr"], imei_parts["cd"])
                raise ParsingDone

        # TODO: 'imeisv' and 'svn' taken from latest AT standard; need real life examples to put into COMMAND_OUTPUT
        #
        # elif self.sn_type == 'imeisv':
        #     if self._regex_helper.match_compiled(self._re_imeisv, line):
        #         imei_parts = self._regex_helper.groupdict()
        #         self.current_ret.update(imei_parts)
        #         self.current_ret["imeisv"] = "{}{}{}".format(imei_parts["tac"], imei_parts["snr"], imei_parts["svn"])
        #         raise ParsingDone
        #
        # elif self.sn_type == 'svn':
        #     if self._regex_helper.match_compiled(self._re_svn, line):
        #         svn = self._regex_helper.group("svn")
        #         self.current_ret["svn"] = svn
        #         raise ParsingDone

    def is_end_of_cmd_output(self, line):
        """
        Checks if end of command is reached.

        AT+CGSN and AT+CGSN=0 are not finished by OK, so such cmd is finished when it detects serial_number

        :param line: Line from device.
        :return:
        """
        if self.sn_type == 'default':
            return 'imei' in self.current_ret
        return super(GetImei, self).is_end_of_cmd_output(line)


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

COMMAND_OUTPUT_ver_default = """
AT+CGSN
490154203237518
"""

COMMAND_KWARGS_ver_default = {}

COMMAND_RESULT_ver_default = {
    'imei': '490154203237518'
}

# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_imei = '''
AT+CGSN=1
+CGSN: "490154203237518"
OK
'''

COMMAND_KWARGS_ver_imei = {'sn_type': 'imei'}

COMMAND_RESULT_ver_imei = {
    'imei': '490154203237518',
    'tac': '49015420',
    'snr': '323751',
    'cd': '8',
}

# -----------------------------------------------------------------------------
