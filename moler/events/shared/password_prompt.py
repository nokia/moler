# -*- coding: utf-8 -*-
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'michal.ernst@nokia.com'

import datetime
import re
from moler.events.shared.genericshared_textualevent import GenericSharedTextualEvent
from moler.exceptions import ParsingDone


class PasswordPrompt(GenericSharedTextualEvent):
    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for 'Password:'

        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(PasswordPrompt, self).__init__(connection=connection, runner=runner, till_occurs_times=till_occurs_times)

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._parse_password_prompt(line=line)
        except ParsingDone:
            pass

    # Password:
    _re_password = re.compile(r"password:", re.IGNORECASE)

    def _parse_password_prompt(self, line):
        """
        Parses line and tries to find password prompt.

        :param line: Line from device.
        :return: None
        :raise: ParsingDone if regex matches the line.
        """
        if self._regex_helper.search_compiled(PasswordPrompt._re_password, line):
            current_ret = dict()
            current_ret["time"] = self._last_recv_time_data_read_from_connection
            current_ret["line"] = line
            self.event_occurred(event_data=current_ret)

            raise ParsingDone()


EVENT_OUTPUT = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48),
        'line': 'Password:'
    }
]
