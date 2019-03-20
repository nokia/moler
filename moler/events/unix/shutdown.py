# -*- coding: utf-8 -*-

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


import datetime
from moler.events.lineevent import LineEvent


class Shutdown(LineEvent):

    def __init__(self, connection, till_occurs_times=-1):
        """
        Event detecting system shutdown.

        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrences
        """
        super(Shutdown, self).__init__(connection=connection, till_occurs_times=till_occurs_times,
                                       detect_pattern=r"system is going down for (\w+) at (.+)")


EVENT_OUTPUT_SIMPLE = """
The system is going down for reboot at Tue 2019-03-19 12:15:16 CET!
"""

EVENT_KWARGS_SIMPLE = {
    "till_occurs_times": 1
}

EVENT_RESULT_SIMPLE = [
    {
        'line': 'The system is going down for reboot at Tue 2019-03-19 12:15:16 CET!',
        'time': datetime.datetime.now()
    }
]
