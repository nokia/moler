"""
Module for command adb root.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2022, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand


class AdbRoot(GenericUnixCommand):

    def __init__(self, connection=None, prompt=None, newline_chars=None, runner=None, options=None):
        """
        Create instance of adb root class.
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param options: Options for command.
        """
        super(AdbRoot, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                      runner=runner)
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "adb root" if not self.options else f"adb root {self.options}"
        return cmd


COMMAND_OUTPUT = """adb root
$"""

COMMAND_RESULT = {}

COMMAND_KWARGS = {}

COMMAND_OUTPUT_already = """adb root
adbd is already running as root
$"""

COMMAND_RESULT_already = {}

COMMAND_KWARGS_already = {}
