# -*- coding: utf-8 -*-
"""
Run moler_serial_proxy command
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import re

from moler.cmd.unix.run_script import RunScript
from moler.exceptions import CommandFailure


class RunSerialProxy(RunScript):

    def __init__(self, connection, serial_devname, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param serial_devname: name of serial device to be proxied (f.ex. COM5, ttyS4).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        # Note: prompt parameter is ignored (new prompt calculated below)
        #       however, that parameter is required to fit in API of TextualDevice.get_cmd()
        proxy_prompt = "{}>".format(serial_devname)
        proxy_command = "python -i moler_serial_proxy.py {}".format(serial_devname)
        # TODO: investigate error_regex=re.compile("error", re.I) param - no proxy on remote, serial device already occupied,
        # error in python code of proxy - will see stack trace on python shell (should exit that shell)
        super(RunSerialProxy, self).__init__(connection=connection, script_command=proxy_command, prompt=proxy_prompt,
                                             newline_chars=newline_chars, runner=runner)
        self.ret_required = False

    # def on_new_line(self, line, is_full_line):
    #     """
    #     Put your parsing code here.
    #     :param line: Line to process, can be only part of line. New line chars are removed from line.
    #     :param is_full_line: True if line had new line chars, False otherwise
    #     :return: Nothing
    #     """
    #     if self.error_regex and self._regex_helper.search_compiled(self.error_regex, line):
    #         self.set_exception(CommandFailure(self, "Found error regex in line '{}'".format(line)))
    #     return super(RunSerialProxy, self).on_new_line(line, is_full_line)


COMMAND_OUTPUT = """
python -i moler_serial_proxy.py COM5
starting COM5 proxy at PC10 ...
PC10  opening serial port COM5
ATE1
OK
PC10:COM5> """

COMMAND_KWARGS = {"serial_devname": "COM5"}

COMMAND_RESULT = {}
