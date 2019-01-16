# -*- coding: utf-8 -*-

__author__ = 'Agnieszka Bylica, Tomasz Krol'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, tomasz.krol@nokia.com'


import re
from moler.events.lineevent import LineEvent


class Wait4PingNoResponse(LineEvent):
    def __init__(self, connection, till_occurs_times=-1):
        """
        Event for 'Wait for no response from ping '.
        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        """
        super(Wait4PingNoResponse, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.connection = connection
        self.detect_pattern = r'(no\s+answer\s+yet\s+for.*)|(.*Destination\s+Host\s+Unreachable)'

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
