# -*- coding: utf-8 -*-
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import datetime
import re

from moler.events.unix.genericunix_lineevent import GenericUnixLineEvent


class WarningDefaultPassword(GenericUnixLineEvent):
    # There were 2 failed login attempts since the last successful login
    _re_warning = re.compile(
        r'Warning: you are using default password, please change it as soon as possible', re.I)

    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for check failed login attempts.

        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(WarningDefaultPassword, self).__init__(connection=connection,
                                                     runner=runner,
                                                     till_occurs_times=till_occurs_times,
                                                     detect_patterns=[WarningDefaultPassword._re_warning, ],
                                                     match='any')

        self.process_full_lines_only = True


EVENT_OUTPUT = """
Warning: you are using default password, please change it as soon as possible.
"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {'groups': (),
     'line': 'Warning: you are using default password, please change it as soon as possible.',
     'matched': 'Warning: you are using default password, please change it as soon as possible',
     'named_groups': {},
     'time': datetime.datetime(2019, 5, 17, 12, 42, 38, 278418)}
]
