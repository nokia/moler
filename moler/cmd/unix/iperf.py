# -*- coding: utf-8 -*-
"""
Iperf command module.
"""

__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Iperf(GenericUnixCommand):
    def __init__(self, connection, options):
        super(Iperf, self).__init__(connection=connection)
        self.options = options
        self.current_ret['RESULT'] = []
        self._list_of_connections = dict()

    def build_command_string(self):
        cmd = 'iperf ' + str(self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Iperf, self).on_new_line(line, is_full_line)

    _re_command_failure = re.compile(r"(?P<FAILURE_MSG>.*failed.*|.*error.*|.*command not found.*|.*iperf:.*)")

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Iperf._re_command_failure, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("FAILURE_MSG"))))
            raise ParsingDone

    _re_ornaments = re.compile(r"(?P<ORNAMENTS>----*|\[\s*ID\].*)", re.IGNORECASE)

    def _parse_line(self, line):
        if not self._regex_helper.search_compiled(Iperf._re_ornaments, line):
            self.current_ret['RESULT'].append(line)
            raise ParsingDone


COMMAND_OUTPUT_basic_client = """
xyz@debian:~$ iperf -c 10.1.1.1
------------------------------------------------------------
Client connecting to 10.1.1.1, TCP port 5001
TCP window size: 16384 Byte (default)
------------------------------------------------------------
[  3] local 192.168.0.102 port 49597 connected with 192.168.0.100 port 5001
[ ID] Interval       Transfer     Bandwidth
[  3]  0.0- 1.0 sec  28.6 MBytes   240 Mbits/sec
[  3]  1.0- 2.0 sec  25.9 MBytes   217 Mbits/sec
[  3]  2.0- 3.0 sec  26.5 MBytes   222 Mbits/sec
[  3]  3.0- 4.0 sec  26.6 MBytes   223 Mbits/sec
[  3]  4.0- 5.0 sec  26.0 MBytes   218 Mbits/sec
[  3]  5.0- 6.0 sec  26.2 MBytes   220 Mbits/sec
[  3]  6.0- 7.0 sec  26.8 MBytes   224 Mbits/sec
[  3]  7.0- 8.0 sec  26.0 MBytes   218 Mbits/sec
[  3]  8.0- 9.0 sec  25.8 MBytes   216 Mbits/sec
[  3]  9.0-10.0 sec  26.4 MBytes   221 Mbits/sec
[  3]  0.0-10.0 sec   265 MBytes   222 Mbits/sec
xyz@debian:~$"""

COMMAND_KWARGS_basic_client = {
    'options': '-c 10.1.1.1'
}

COMMAND_RESULT_basic_client = {
    'RESULT': ['Client connecting to 10.1.1.1, TCP port 5001', 'TCP window size: 16384 Byte (default)',
               '[  3] local 192.168.0.102 port 49597 connected with ''192.168.0.100 port 5001',
               '[  3]  0.0- 1.0 sec  28.6 MBytes   240 Mbits/sec', '[  3]  1.0- 2.0 sec  25.9 MBytes   217 Mbits/sec',
               '[  3]  2.0- 3.0 sec  26.5 MBytes   222 Mbits/sec', '[  3]  3.0- 4.0 sec  26.6 MBytes   223 Mbits/sec',
               '[  3]  4.0- 5.0 sec  26.0 MBytes   218 Mbits/sec', '[  3]  5.0- 6.0 sec  26.2 MBytes   220 Mbits/sec',
               '[  3]  6.0- 7.0 sec  26.8 MBytes   224 Mbits/sec', '[  3]  7.0- 8.0 sec  26.0 MBytes   218 Mbits/sec',
               '[  3]  8.0- 9.0 sec  25.8 MBytes   216 Mbits/sec', '[  3]  9.0-10.0 sec  26.4 MBytes   221 Mbits/sec',
               '[  3]  0.0-10.0 sec   265 MBytes   222 Mbits/sec']
}


COMMAND_OUTPUT_basic_server = """
xyz@debian:~$ iperf -s
------------------------------------------------------------
Server listening on TCP port 5001
TCP window size: 8.00 KByte (default)
------------------------------------------------------------
[852] local 10.1.1.1 port 5001 connected with 10.6.2.5 port 60270
xyz@debian:~$"""

COMMAND_KWARGS_basic_server = {
    'options': '-s'
}

COMMAND_RESULT_basic_server = {
    'RESULT': ['Server listening on TCP port 5001', 'TCP window size: 8.00 KByte (default)',
               '[852] local 10.1.1.1 port 5001 connected with 10.6.2.5 port 60270']
}
