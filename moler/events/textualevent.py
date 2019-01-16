# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'

import abc
from moler.event import Event
from moler.cmd import RegexHelper


class TextualEvent(Event):
    _default_newline_chars = ("\n", "\r")  # New line chars on device, not system with script!

    def __init__(self, connection=None, till_occurs_times=-1):
        super(TextualEvent, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self._last_not_full_line = None
        self._newline_chars = TextualEvent._default_newline_chars
        self._regex_helper = RegexHelper()  # Object to regular expression matching

    def event_occurred(self, event_data):
        self._consume_already_parsed_fragment()
        super(TextualEvent, self).event_occurred(event_data)

    @abc.abstractmethod
    def on_new_line(self, line, is_full_line):
        """
        Method to parse output from device.
        Write your own implementation to do something useful
        :param line: Line to parse, new lines are trimmed
        :param is_full_line: True if new line character was removed from line, False otherwise
        :return: Nothing
        """
        pass

    def data_received(self, data):
        """
        Called by framework when any data are sent by device
        :param data: List of strings sent by device
        :return: Nothing
        """
        lines = data.splitlines(True)
        for line in lines:
            if self._last_not_full_line is not None:
                line = self._last_not_full_line + line
                self._last_not_full_line = None
            is_full_line = self.is_new_line(line)
            if is_full_line:
                line = self._strip_new_lines_chars(line)
            else:
                self._last_not_full_line = line
            self.on_new_line(line, is_full_line)

    def is_new_line(self, line):
        """
        Method to check if line has chars of new line at the right side
        :param line: String to check
        :return: True if any new line char was found, False otherwise
        """
        if line.endswith(self._newline_chars):
            return True
        return False

    def _strip_new_lines_chars(self, line):
        """
        :param line: line from device
        :return: line without new lines chars
        """
        for char in self._newline_chars:
            line = line.rstrip(char)
        return line

    def _consume_already_parsed_fragment(self):
        """
        Clear already parsed fragment of line to not parse it twice when another fragment appears on device.
        :return: Nothing
        """
        self._last_not_full_line = None
