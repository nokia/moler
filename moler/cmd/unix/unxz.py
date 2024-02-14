# -*- coding: utf-8 -*-
__author__ = 'Aleksander Lagierski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'aleksander.lagierski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand


class Unxz(GenericUnixCommand):
    """Unxz command class."""

    def __init__(self, connection, xz_file, options="", prompt=None,
                 newline_chars=None, runner=None):
        """
        Unxz command.
        :param connection: Moler connection to device, terminal when command is executed.
        :param xz_file: Name of a file which shall be extracted.
        :param options: Options of command unxz.
        :param prompt: Expected prompt that has been sent by device after command execution.
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Unxz, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.xz_file = xz_file
        self.ret_required = False

    def build_command_string(self):
        """
        Build command string from parameters passed to object.
        :return: String representation of the command to send over a connection to the device.
        """
        if self.options:
            cmd = f"unxz {self.options} {self.xz_file}"
        else:
            cmd = f"unxz {self.xz_file}"
        return cmd


COMMAND_OUTPUT = """unxz file.xz
host:~>"""

COMMAND_RESULT = {

}

COMMAND_KWARGS = {
    "xz_file": "file.xz"
}

COMMAND_OUTPUT_options = """unxz -c file.xz
Content of the xz file
host:~> """

COMMAND_RESULT_options = {

}

COMMAND_KWARGS_options = {
    "xz_file": "file.xz",
    "options": "-c"
}
