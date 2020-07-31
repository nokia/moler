# -*- coding: utf-8 -*-
__author__ = 'Aleksander Lagierski'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'aleksander.lagierski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


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
        self._is_overwritten = False
        self.current_ret['FILE_LIST'] = list()
        self.current_ret['FILE_DICT'] = dict()

    def build_command_string(self):
        """
        Build command string from parameters passed to object.
        :return: String representation of the command to send over a connection to the device.
        """
        if self.options:
            cmd = "{} {} {}".format("unxz",self.options,self.xz_file)
        else:
            cmd = "{} {}".format("unxz", self.xz_file)
        return cmd


