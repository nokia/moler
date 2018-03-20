# -*- coding: utf-8 -*-
"""
Generic Unix/Linux module
"""
import re
import abc

from moler.textualgeneric import TextualGeneric

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class GenericUnix(TextualGeneric):
    _re_fail = re.compile(r'command not found|No such file or directory|running it may require superuser privileges')

    def __init__(self, connection, prompt=None, new_line_chars=None):
        """
        :param connection: connection to device
        :param prompt: expected prompt sending by device after command execution. String or re.compile
        :param new_line_chars:  new line chars on device, if None default value will be used
        """
        super(GenericUnix, self).__init__(connection, prompt, new_line_chars)

    @abc.abstractmethod
    def get_cmd(self, cmd=None):
        """
        :param cmd:  If provided then parameters form command will not be used
        :return:  String with command
        """
        pass

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.
        Write your own implementation but don't forget to call on_new_line from base class
        :param line: Line to parse, new lines are trimmed
        :param is_full_line: True if new line character was removed from line, False otherwise
        :return: Nothing
        """
        if is_full_line and self._regex_helper.search_compiled(GenericUnix._re_fail, line):
                self.set_exception(Exception("command failed in line '{}'".format(line)))
        return super(GenericUnix, self).on_new_line(line, is_full_line)
