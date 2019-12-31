# -*- coding: utf-8 -*-
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import datetime
import re

from moler.events.unix.genericunix_lineevent import GenericUnixLineEvent


class FailedLoginCounter(GenericUnixLineEvent):
    # There were 2 failed login attempts since the last successful login
    _re_attempts = re.compile(
        r'There (?:were|was|have been) (?P<ATTEMPTS_NR>\d+) (?:failed|unsuccessful) login attempts? '
        r'since the last successful login', re.I)

    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for check failed login attempts.

        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(FailedLoginCounter, self).__init__(connection=connection,
                                                 runner=runner,
                                                 till_occurs_times=till_occurs_times,
                                                 detect_patterns=[FailedLoginCounter._re_attempts, ],
                                                 match='any')

        self.process_full_lines_only = True


EVENT_OUTPUT = """
There were 2 failed login attempts since the last successful login.
"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {'groups': (2,),
     'line': 'There were 2 failed login attempts since the last successful login.',
     'matched': 'There were 2 failed login attempts since the last successful login',
     'named_groups': {'ATTEMPTS_NR': 2},
     'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)}
]

EVENT_OUTPUT_one = """
There was 1 failed login attempts since the last successful login.
"""

EVENT_KWARGS_one = {
    "till_occurs_times": 1
}

EVENT_RESULT_one = [
    {'groups': (1,),
     'line': 'There was 1 failed login attempts since the last successful login.',
     'matched': 'There was 1 failed login attempts since the last successful login',
     'named_groups': {'ATTEMPTS_NR': 1},
     'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)}
]
