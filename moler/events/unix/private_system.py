# -*- coding: utf-8 -*-
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import datetime
import re

from moler.events.lineevent import LineEvent


class PrivateSystem(LineEvent):
    # There were 2 failed login attempts since the last successful login
    _re_warning = re.compile(
        r'You are about to access a private system. This system is for the use of authorized users only. '
        r'All connections are logged to the extent and by means acceptable by the local legislation. '
        r'Any unauthorized access or access attempts may be punished to the fullest extent possible under '
        r'the applicable local legislation.', re.I)

    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for check failed login attempts.

        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(PrivateSystem, self).__init__(connection=connection,
                                            runner=runner,
                                            till_occurs_times=till_occurs_times,
                                            detect_patterns=[PrivateSystem._re_warning, ],
                                            match='any')

        self.process_full_lines_only = True


EVENT_OUTPUT = """
You are about to access a private system. This system is for the use of authorized users only. All connections are logged to the extent and by means acceptable by the local legislation. Any unauthorized access or access attempts may be punished to the fullest extent possible under the applicable local legislation.
"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {'groups': (),
     'line': 'You are about to access a private system. This system is for the use of authorized users only. '
             'All connections are logged to the extent and by means acceptable by the local legislation. '
             'Any unauthorized access or access attempts may be punished to the fullest extent possible under '
             'the applicable local legislation.',
     'matched': 'You are about to access a private system. This system is for the use of authorized users only. '
                'All connections are logged to the extent and by means acceptable by the local legislation. '
                'Any unauthorized access or access attempts may be punished to the fullest extent possible under '
                'the applicable local legislation.',
     'named_groups': {},
     'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)}
]
