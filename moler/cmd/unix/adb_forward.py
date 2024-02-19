"""
Module for command adb forward.
"""

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2022, Nokia"
__email__ = "marcin.usielski@nokia.com"

from moler.cmd.unix.genericunix import GenericUnixCommand


class AdbForward(GenericUnixCommand):
    def __init__(
        self, options, connection=None, prompt=None, newline_chars=None, runner=None
    ):
        """
        Create instance of adb forward class.
        :param options: Options for command.
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(AdbForward, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.current_ret["LINES"] = []

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = f"adb forward {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            self.current_ret["LINES"].append(line)

        super(AdbForward, self).on_new_line(line=line, is_full_line=is_full_line)


COMMAND_OUTPUT = """adb forward tcp:5678 localfilesystem:/dev/socket/adb_atci_socket
5678
$"""

COMMAND_RESULT = {"LINES": ["5678"]}

COMMAND_KWARGS = {"options": "tcp:5678 localfilesystem:/dev/socket/adb_atci_socket"}
