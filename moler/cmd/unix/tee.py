# -*- coding: utf-8 -*-
"""
Tee command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
import six


class Tee(GenericUnixCommand):

    """Unix tee command"""

    def __init__(self, connection, path, content, prompt=None, newline_chars=None, runner=None):
        """
        Unix tee command

        :param connection: Moler connection to device, terminal when command is executed.
        :param path: path to file to save.
        :param content: content of file. A string or list of strings.
        :param prompt: Prompt of the starting shell
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Tee, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.path = path
        if isinstance(content, six.string_types):
            self._content = [content]
        else:
            self._content = list(content)  # copy of list of content to modify
        self.end_sent = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "tee {}".format(self.path)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                line_to_save = self._content.pop(0)
                self.connection.sendline(line_to_save)
            except IndexError:
                if not self.end_sent:
                    self.connection.send(chr(4))
                    self.connection.send(chr(3))
                    self.end_sent = True
        super(Tee, self).on_new_line(line=line, is_full_line=is_full_line)


COMMAND_OUTPUT_string = """tee file.txt
line 1
line 2
moler-bash#"""

COMMAND_KWARGS_string = {
    "path": "file.txt",
    "content": "line 1\nline 2"
}

COMMAND_RESULT_string = {}

COMMAND_OUTPUT_list = """tee file.txt
line a
line b
moler-bash#"""

COMMAND_KWARGS_list = {
    "path": "file.txt",
    "content": ("line a", "line b")
}

COMMAND_RESULT_list = {}
