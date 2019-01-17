# -*- coding: utf-8 -*-

__author__ = 'Agnieszka Bylica, Tomasz Krol'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, tomasz.krol@nokia.com'


import re
import datetime
from moler.events.lineevent import LineEvent


class PingResponse(LineEvent):
    def __init__(self, connection, till_occurs_times=-1):
        """
        Event for 'Wait for response from ping.'.
        :param connection: moler connection to device, terminal when command is executed
        :param till_occurs_times: number of event occurrence
        """
        super(PingResponse, self).__init__(connection=connection, till_occurs_times=till_occurs_times)
        self.connection = connection
        self.detect_pattern = r'\d+\s+bytes\s+from.+'
        self.current_ret = dict()

    def on_new_line(self, line, is_full_line):
        """
         Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line or not self.process_full_lines_only:
            match_obj = re.search(self.detect_pattern, line)

            if match_obj:
                print(line)
                self.current_ret['time'] = datetime.datetime.now()
                self.current_ret['line'] = line
                self.event_occurred(event_data=self.current_ret)
                self.current_ret = dict()


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

EVENT_RESULT = {
    'line': '64 bytes from 192.168.255.129: icmp_seq=43 ttl=64 time=0.638 ms',
    'time': datetime.datetime.now()
}
