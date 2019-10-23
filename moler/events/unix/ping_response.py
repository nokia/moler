# -*- coding: utf-8 -*-

__author__ = 'Agnieszka Bylica, Tomasz Krol, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, tomasz.krol@nokia.com, marcin.usielski@nokia.com'


import re
import datetime
from moler.events.unix.genericunix_lineevent import GenericUnixLineEvent


class PingResponse(GenericUnixLineEvent):

    _re_detect_pattern = re.compile(r'\d+\s+bytes\s+from.+')

    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for 'Wait for response from ping.'.
        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(PingResponse, self).__init__(connection=connection, runner=runner, till_occurs_times=till_occurs_times,
                                           detect_patterns=[PingResponse._re_detect_pattern], match='any')


EVENT_OUTPUT = """
ute@SC5G-HUB-079:~$ ping -O 192.168.255.129
PING 192.168.255.129 (192.168.255.129) 56(84) bytes of data.
no answer yet for icmp_seq=22
no answer yet for icmp_seq=23
no answer yet for icmp_seq=24
no answer yet for icmp_seq=25
no answer yet for icmp_seq=26
no answer yet for icmp_seq=27
no answer yet for icmp_seq=28
no answer yet for icmp_seq=29
no answer yet for icmp_seq=30
no answer yet for icmp_seq=31
no answer yet for icmp_seq=32
no answer yet for icmp_seq=33
no answer yet for icmp_seq=34
no answer yet for icmp_seq=35
no answer yet for icmp_seq=36
no answer yet for icmp_seq=37
no answer yet for icmp_seq=38
no answer yet for icmp_seq=39
no answer yet for icmp_seq=40
no answer yet for icmp_seq=41
no answer yet for icmp_seq=42
64 bytes from 192.168.255.129: icmp_seq=43 ttl=64 time=0.638 ms
64 bytes from 192.168.255.129: icmp_seq=44 ttl=64 time=0.375 ms
64 bytes from 192.168.255.129: icmp_seq=45 ttl=64 time=0.297 ms
ute@SC5G-HUB-079:~$"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [
    {
        'line': '64 bytes from 192.168.255.129: icmp_seq=43 ttl=64 time=0.638 ms',
        "groups": (),
        "named_groups": {},
        "matched": "64 bytes from 192.168.255.129: icmp_seq=43 ttl=64 time=0.638 ms",
        'time': datetime.datetime.now()
    }
]
