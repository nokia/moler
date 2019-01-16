# -*- coding: utf-8 -*-

__author__ = 'Agnieszka Bylica, Tomasz Krol'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, tomasz.krol@nokia.com'


import re
from moler.events.lineevent import LineEvent
from moler.exceptions import CommandFailure


class Wait4Ping(LineEvent):
    def __init__(self, connection, options, till_occurs_times=-1):
        """
        Event for 'Wait for ping.'.
        :param connection: moler connection to device, terminal when command is executed
        :param options: up - waits for correct answer; down - waits for 'no answer'
        :param till_occurs_times: number of event occurrence
        """
        super(Wait4Ping, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.connection = connection
        self.options = options
        if self.options == "up":
            self.detect_pattern = r'\d+\s+bytes\s+from.+'
        elif self.options == "down":
            self.detect_pattern = r'no\s+answer\s+yet\s+for.*'
        else:
            self.set_exception(CommandFailure(self, "Wrong option used: {}, available options: up down.".format(
                self.options)))

    def on_new_line(self, line, is_full_line):
        """
         Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line or not self.process_full_lines_only:
            match_obj = re.search(self.detect_pattern, line)

            if match_obj:
                self.event_occurred(event_data=line)
                return
