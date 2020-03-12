# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com, michal.ernst@nokia.com'
import datetime

from moler.events.shared.wait4 import Wait4


class Wait4prompt(Wait4):
    def __init__(self, connection, prompt, till_occurs_times=-1, runner=None):
        """
        Event for waiting for prompt
        :param connection: moler connection to device, terminal when command is executed
        :param prompt: prompt regex
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(Wait4prompt, self).__init__(connection=connection, runner=runner, till_occurs_times=till_occurs_times,
                                          detect_patterns=[prompt], match='any')


EVENT_OUTPUT = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
f6 FCT-E019-0-SmaLite \ufffd\ufffd\x7f \ufffd\ufffd\ufffd}"\ufffd\x02\ufffd?\ufffd\ufffd\ufffd\x08\ufffd\x05o\x1c
CLIENT5 [] has just connected!
host:~ #"""

EVENT_KWARGS = {
    "prompt": r'host:.*#',
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'line': "host:~ #",
        "groups": (),
        "named_groups": {},
        "matched": "host:~ #",
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
    }
]
