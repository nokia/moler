# -*- coding: utf-8 -*-
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import datetime
import re

from moler.events.unix.genericunix_textualevent import GenericUnixTextualEvent
from moler.exceptions import ParsingDone


class AdviseToChangeYourPassword(GenericUnixTextualEvent):
    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for advise to change password.

        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(AdviseToChangeYourPassword, self).__init__(connection=connection, runner=runner, till_occurs_times=till_occurs_times)
        self.current_ret = dict()

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_advise(line=line)
            except ParsingDone:
                pass

    # Warning: you are advised to change your password (more than 90 days old)
    _re_advise = re.compile(
        r'Warning: you are advised to change your password \(more than\s+(?P<DAYS>\d+)\s+days old\)', re.I)

    def _parse_advise(self, line):
        if self._regex_helper.search(AdviseToChangeYourPassword._re_advise, line):
            self.current_ret["time"] = self._last_recv_time_data_read_from_connection
            self.current_ret["days"] = int(self._regex_helper.group("DAYS"))
            self.event_occurred(event_data=self.current_ret)
            self.current_ret = dict()
            raise ParsingDone()


EVENT_OUTPUT = """
Warning: you are advised to change your password (more than 90 days old)
"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48),
        'days': 90
    }
]
