# -*- coding: utf-8 -*-
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import datetime
import re

from moler.events.unix.genericunix_lineevent import GenericUnixLineEvent


class PrivateSystem(GenericUnixLineEvent):
    # There were 2 failed login attempts since the last successful login
    _re_warning = [
        re.compile(r"You are about to access a private system. This system is for the use of"),
        re.compile(r"authorized users only. All connections are logged to the extent and by means"),
        re.compile(r"acceptable by the local legislation. Any unauthorized access or access"),
        re.compile(r"attempts may be punished to the fullest extent possible under the applicable"),
        re.compile(r"local legislation."),
    ]

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
                                            detect_patterns=PrivateSystem._re_warning,
                                            match='all')

        self.process_full_lines_only = True


EVENT_OUTPUT = """
You are about to access a private system. This system is for the use of
authorized users only. All connections are logged to the extent and by means
acceptable by the local legislation. Any unauthorized access or access
attempts may be punished to the fullest extent possible under the applicable
local legislation.
"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}
EVENT_RESULT = [
    [
        {
            'line': 'You are about to access a private system. This system is for the use of',
            'matched': 'You are about to access a private system. This system is for the use of',
            'groups': (),
            'named_groups': {},
            'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)
        },
        {
            'line': 'authorized users only. All connections are logged to the extent and by means',
            'matched': 'authorized users only. All connections are logged to the extent and by means',
            'groups': (),
            'named_groups': {},
            'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)
        },
        {
            'line': 'acceptable by the local legislation. Any unauthorized access or access',
            'matched': 'acceptable by the local legislation. Any unauthorized access or access',
            'groups': (),
            'named_groups': {},
            'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)
        },
        {
            'line': 'attempts may be punished to the fullest extent possible under the applicable',
            'matched': 'attempts may be punished to the fullest extent possible under the applicable',
            'groups': (),
            'named_groups': {},
            'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)
        },
        {
            'line': 'local legislation.',
            'matched': 'local legislation.',
            'groups': (),
            'named_groups': {},
            'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)
        },
    ]
]
