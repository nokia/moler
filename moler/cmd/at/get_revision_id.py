# -*- coding: utf-8 -*-
"""
AT+CGMR .

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


class GetRevisionId(GenericAtCommand):
    """
    Command to get revision identification. Example output:

    AT+CGMR
    MPSS.HE.1.5.2-00368-SM8150_GENFUSION_PACK-1  1  [Aug 07 2019 21:00:00]
    """
    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None):
        """Create instance of GetRevisionId class"""
        super(GetRevisionId, self).__init__(connection, operation='execute', prompt=prompt,
                                            newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        return "AT+CGMR"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.

        MPSS.HE.1.5.2-00368-SM8150_GENFUSION_PACK-1  1  [Aug 07 2019 21:00:00]

        Write your own implementation but don't forget to call on_new_line from base class

        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            try:
                self._parse_revision(line)
            except ParsingDone:
                pass
        return super(GetRevisionId, self).on_new_line(line, is_full_line)

    _re_revision = re.compile(r'^\s*(?P<revision>\S.*)\s*$')

    def _parse_revision(self, line):
        """
        Parse revision identification that may look like:

        MPSS.HE.1.5.2-00368-SM8150_GENFUSION_PACK-1  1  [Aug 07 2019 21:00:00]
        """
        if self._regex_helper.match_compiled(self._re_revision, line):
            revision = self._regex_helper.group("revision")
            self.current_ret['revision'] = revision
            raise ParsingDone

    def is_end_of_cmd_output(self, line):
        """
        Checks if end of command is reached.

        AT+CGMR is not finished by OK, so it is finished when it detects revision

        :param line: Line from device.
        :return:
        """
        return 'revision' in self.current_ret


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

COMMAND_OUTPUT_ver_execute = """
AT+CGMR
MPSS.HE.1.5.2-00368-SM8150_GENFUSION_PACK-1  1  [Aug 07 2019 21:00:00]
"""

COMMAND_KWARGS_ver_execute = {}

COMMAND_RESULT_ver_execute = {
    'revision': 'MPSS.HE.1.5.2-00368-SM8150_GENFUSION_PACK-1  1  [Aug 07 2019 21:00:00]'
}
