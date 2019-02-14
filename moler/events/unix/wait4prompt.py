# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'
import datetime

from moler.events.lineevent import LineEvent


class Wait4prompt(LineEvent):
    def __init__(self, connection, prompt, till_occurs_times=-1):
        super(Wait4prompt, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.connection = connection
        self.detect_pattern = prompt


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
    "prompt": r'host:.*#',
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'line': "host:~ #",
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
    }
]
