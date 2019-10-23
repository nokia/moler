# -*- coding: utf-8 -*-

__author__ = 'Agnieszka Bylica, Tomasz Krol, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, tomasz.krol@nokia.com, marcin.usielski@nokia.com'


import re
import datetime
from moler.events.unix.genericunix_lineevent import GenericUnixLineEvent


class PingNoResponse(GenericUnixLineEvent):

    _re_detect_pattern = re.compile(r'(no\s+answer\s+yet\s+for.*)|(.*Destination\s+Host\s+Unreachable)')

    def __init__(self, connection, till_occurs_times=-1, runner=None):
        """
        Event for 'Wait for no response from ping '.
        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(PingNoResponse, self).__init__(connection=connection, runner=runner, till_occurs_times=till_occurs_times,
                                             detect_patterns=[PingNoResponse._re_detect_pattern], match='any')


EVENT_OUTPUT = """ute@SC5G-HUB-079:~$ ping -O 192.168.255.126
PING 192.168.255.129 (192.168.255.129) 56(84) bytes of data.
From 192.168.255.126 icmp_seq=1 Destination Host Unreachable
From 192.168.255.126 icmp_seq=2 Destination Host Unreachable
From 192.168.255.126 icmp_seq=3 Destination Host Unreachable
From 192.168.255.126 icmp_seq=4 Destination Host Unreachable
From 192.168.255.126 icmp_seq=5 Destination Host Unreachable
From 192.168.255.126 icmp_seq=6 Destination Host Unreachable
From 192.168.255.126 icmp_seq=7 Destination Host Unreachable
From 192.168.255.126 icmp_seq=8 Destination Host Unreachable
From 192.168.255.126 icmp_seq=9 Destination Host Unreachable
ute@SC5G-HUB-079:~$"""

EVENT_KWARGS = {
    "till_occurs_times": 1
}

EVENT_RESULT = [{
    "line": "From 192.168.255.126 icmp_seq=1 Destination Host Unreachable",
    "groups": (None, u"From 192.168.255.126 icmp_seq=1 Destination Host Unreachable"),
    "named_groups": {},
    "matched": "From 192.168.255.126 icmp_seq=1 Destination Host Unreachable",
    "time": datetime.datetime.now()
}]


EVENT_OUTPUT_2 = """
ute@SC5G-HUB-079:~$ ping -O 192.168.255.129
PING 192.168.255.129 (192.168.255.129) 56(84) bytes of data.
64 bytes from 192.168.255.129: icmp_seq=1 ttl=64 time=0.363 ms
64 bytes from 192.168.255.129: icmp_seq=2 ttl=64 time=0.354 ms
64 bytes from 192.168.255.129: icmp_seq=3 ttl=64 time=0.385 ms
64 bytes from 192.168.255.129: icmp_seq=4 ttl=64 time=0.374 ms
64 bytes from 192.168.255.129: icmp_seq=5 ttl=64 time=0.651 ms
64 bytes from 192.168.255.129: icmp_seq=6 ttl=64 time=0.373 ms
64 bytes from 192.168.255.129: icmp_seq=7 ttl=64 time=0.367 ms
64 bytes from 192.168.255.129: icmp_seq=8 ttl=64 time=0.398 ms
64 bytes from 192.168.255.129: icmp_seq=9 ttl=64 time=0.389 ms
64 bytes from 192.168.255.129: icmp_seq=10 ttl=64 time=0.347 ms
64 bytes from 192.168.255.129: icmp_seq=11 ttl=64 time=0.439 ms
64 bytes from 192.168.255.129: icmp_seq=12 ttl=64 time=0.389 ms
64 bytes from 192.168.255.129: icmp_seq=13 ttl=64 time=0.432 ms
64 bytes from 192.168.255.129: icmp_seq=14 ttl=64 time=0.343 ms
64 bytes from 192.168.255.129: icmp_seq=15 ttl=64 time=0.430 ms
64 bytes from 192.168.255.129: icmp_seq=16 ttl=64 time=0.354 ms
64 bytes from 192.168.255.129: icmp_seq=17 ttl=64 time=0.399 ms
64 bytes from 192.168.255.129: icmp_seq=18 ttl=64 time=0.436 ms
64 bytes from 192.168.255.129: icmp_seq=19 ttl=64 time=0.439 ms
64 bytes from 192.168.255.129: icmp_seq=20 ttl=64 time=0.366 ms
64 bytes from 192.168.255.129: icmp_seq=21 ttl=64 time=0.430 ms
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

EVENT_KWARGS_2 = {
    "till_occurs_times": 1
}

EVENT_RESULT_2 = [
    {
        "line": "no answer yet for icmp_seq=22",
        "groups": (u"no answer yet for icmp_seq=22", None),
        "named_groups": {},
        "matched": "no answer yet for icmp_seq=22",
        "time": datetime.datetime.now()
    }
]
