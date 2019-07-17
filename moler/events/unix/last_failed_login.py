# -*- coding: utf-8 -*-
__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import datetime
import re

from moler.events.unix.last_login import LastLogin


class LastFailedLogin(LastLogin):

    # Last failed login: Tue Jun 12 08:54:44 2018 from 127.0.0.1
    _re_last_login = re.compile(r'Last failed login:\s+(?P<DATE>\S.*\S)\s+from\s+(?P<HOST>\S+)', re.I)

    def _get_re_line(self):
        """
        Returns regex object with groups: DATE and HOST.

        :return: regex object with groups: DATE and HOST.
        """
        return LastFailedLogin._re_last_login


EVENT_OUTPUT = """
Last failed login: Tue Jun 12 08:54:44 2018 from 127.0.0.1
"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48),
        'host': '127.0.0.1',
        'date_raw': 'Tue Jun 12 08:54:44 2018',
        'date': datetime.datetime(2018, 6, 12, 8, 54, 44),
    }
]
