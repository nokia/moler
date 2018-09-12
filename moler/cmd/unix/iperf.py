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
        self._connection_dict = dict()
        self.current_ret['CONNECTIONS'] = dict()
        self.current_ret['INFO'] = list()
        self._list_of_connections = dict()

    def build_command_string(self):
        cmd = 'iperf ' + str(self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse_connection_name_and_id(line)
                self._parse_headers(line)
                self._parse_connection_info(line)
                self._parse_connection_headers(line)
            except ParsingDone:
                pass
        return super(Iperf, self).on_new_line(line, is_full_line)

    _re_command_failure = re.compile(r"(?P<FAILURE_MSG>.*failed.*|.*error.*|.*command not found.*|.*iperf:.*)")

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Iperf._re_command_failure, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("FAILURE_MSG"))))
            raise ParsingDone

    _re_connection_name_and_id = re.compile(r"(?P<ID>\[\s*\d*\])\s*(?P<ID_NAME>.*port\s*\d*\s*connected with.*)")

    def _parse_connection_name_and_id(self, line):
        if self._regex_helper.search_compiled(Iperf._re_connection_name_and_id, line):
            connection_id = self._regex_helper.group("ID")
            connection_name = self._regex_helper.group("ID_NAME")
            connection_dict = {connection_id: connection_name}
            self._connection_dict.update(connection_dict)
            raise ParsingDone

    _re_headers = re.compile(r"(?P<HEADERS>\[\s+ID\].*)")

    def _parse_headers(self, line):
        if self._regex_helper.search_compiled(Iperf._re_headers, line):
            matched = line.split()[2:]
            self._list_of_connections = [header.strip() for header in matched]
            raise ParsingDone

    _re_connection_info = re.compile(r"(?P<CONNECTION_ID>\[\s*\d*\])\s*(?P<CONNECTION_REPORT>.*)")

    def _parse_connection_info(self, line):
        if self._regex_helper.search_compiled(Iperf._re_connection_info, line):
            connection_id = self._regex_helper.group("CONNECTION_ID")
            connection_report = self._regex_helper.group("CONNECTION_REPORT").split('  ')
            connection_report = [report.strip() for report in connection_report]
            connection_name = self._connection_dict[connection_id]
            info_dict = dict(zip(self._list_of_connections, connection_report))
            self._update_current_ret(connection_name, info_dict)
            raise ParsingDone

    def _update_current_ret(self, connection_name, info_dict):
        if connection_name in self.current_ret['CONNECTIONS']:
            self.current_ret['CONNECTIONS'][connection_name].append(info_dict)
        else:
            connection_dict = {connection_name: [info_dict]}
            self.current_ret['CONNECTIONS'].update(connection_dict)

    _re_ornaments = re.compile(r"(?P<ORNAMENTS>----*|\[\s*ID\].*)", re.IGNORECASE)

    def _parse_connection_headers(self, line):
        if not self._regex_helper.search_compiled(Iperf._re_ornaments, line):
            self.current_ret['INFO'].append(line.strip())
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
    'CONNECTIONS':
        {'local 192.168.0.102 port 49597 connected with 192.168.0.100 port 5001': [
              {'Bandwidth': '240 Mbits/sec', 'Transfer': '28.6 MBytes', 'Interval': '0.0- 1.0 sec'},
              {'Bandwidth': '217 Mbits/sec', 'Transfer': '25.9 MBytes', 'Interval': '1.0- 2.0 sec'},
              {'Bandwidth': '222 Mbits/sec', 'Transfer': '26.5 MBytes', 'Interval': '2.0- 3.0 sec'},
              {'Bandwidth': '223 Mbits/sec', 'Transfer': '26.6 MBytes', 'Interval': '3.0- 4.0 sec'},
              {'Bandwidth': '218 Mbits/sec', 'Transfer': '26.0 MBytes', 'Interval': '4.0- 5.0 sec'},
              {'Bandwidth': '220 Mbits/sec', 'Transfer': '26.2 MBytes', 'Interval': '5.0- 6.0 sec'},
              {'Bandwidth': '224 Mbits/sec', 'Transfer': '26.8 MBytes', 'Interval': '6.0- 7.0 sec'},
              {'Bandwidth': '218 Mbits/sec', 'Transfer': '26.0 MBytes', 'Interval': '7.0- 8.0 sec'},
              {'Bandwidth': '216 Mbits/sec', 'Transfer': '25.8 MBytes', 'Interval': '8.0- 9.0 sec'},
              {'Bandwidth': '221 Mbits/sec', 'Transfer': '26.4 MBytes', 'Interval': '9.0-10.0 sec'},
              {'Bandwidth': '222 Mbits/sec', 'Transfer': '265 MBytes', 'Interval': '0.0-10.0 sec'}]},
    'INFO': ['Client connecting to 10.1.1.1, TCP port 5001', 'TCP window size: 16384 Byte (default)']
}


COMMAND_OUTPUT_basic_server = """
xyz@debian:~$ iperf -u
------------------------------------------------------------ 
Server listening on UDP port 5001 
Receiving 1470 byte datagrams 
UDP buffer size: 8.00 KByte (default) 
------------------------------------------------------------ 
[904] local 10.1.1.1 port 5001 connected with 10.6.2.5 port 32781 
[ ID]   Interval         Transfer        Bandwidth         Jitter        Lost/Total Datagrams 
[904]   0.0- 1.0 sec   1.17 MBytes   9.84 Mbits/sec   1.830 ms   0/ 837   (0%) 
[904]   1.0- 2.0 sec   1.18 MBytes   9.94 Mbits/sec   1.846 ms   5/ 850   (0.59%) 
[904]   2.0- 3.0 sec   1.19 MBytes   9.98 Mbits/sec   1.802 ms   2/ 851   (0.24%) 
[904]   3.0- 4.0 sec   1.19 MBytes   10.0 Mbits/sec   1.830 ms   0/ 850   (0%) 
[904]   4.0- 5.0 sec   1.19 MBytes   9.98 Mbits/sec   1.846 ms   1/ 850   (0.12%) 
[904]   5.0- 6.0 sec   1.19 MBytes   10.0 Mbits/sec   1.806 ms   0/ 851   (0%) 
[904]   6.0- 7.0 sec   1.06 MBytes   8.87 Mbits/sec   1.803 ms   1/ 755   (0.13%) 
[904]   7.0- 8.0 sec   1.19 MBytes   10.0 Mbits/sec   1.831 ms   0/ 850   (0%) 
[904]   8.0- 9.0 sec   1.19 MBytes   10.0 Mbits/sec   1.841 ms   0/ 850   (0%) 
[904]   9.0-10.0 sec   1.19 MBytes   10.0 Mbits/sec   1.801 ms   0/ 851   (0%) 
[904]   0.0-10.0 sec   11.8 MBytes   9.86 Mbits/sec   2.618 ms   9/ 8409  (0.11%) 
xyz@debian:~$"""

COMMAND_KWARGS_basic_server = {
    'options': '-u'
}

COMMAND_RESULT_basic_server = {
    'CONNECTIONS':
        {'local 10.1.1.1 port 5001 connected with 10.6.2.5 port 32781 ': [
            {'Datagrams': '(0%)', 'Transfer': '1.17 MBytes', 'Lost/Total': '0/ 837', 'Jitter': '1.830 ms',
             'Bandwidth': '9.84 Mbits/sec', 'Interval': '0.0- 1.0 sec'},
            {'Datagrams': '(0.59%)', 'Transfer': '1.18 MBytes', 'Lost/Total': '5/ 850', 'Jitter': '1.846 ms',
             'Bandwidth': '9.94 Mbits/sec', 'Interval': '1.0- 2.0 sec'},
            {'Datagrams': '(0.24%)', 'Transfer': '1.19 MBytes', 'Lost/Total': '2/ 851', 'Jitter': '1.802 ms',
             'Bandwidth': '9.98 Mbits/sec', 'Interval': '2.0- 3.0 sec'},
            {'Datagrams': '(0%)', 'Transfer': '1.19 MBytes', 'Lost/Total': '0/ 850', 'Jitter': '1.830 ms',
             'Bandwidth': '10.0 Mbits/sec', 'Interval': '3.0- 4.0 sec'},
            {'Datagrams': '(0.12%)', 'Transfer': '1.19 MBytes', 'Lost/Total': '1/ 850', 'Jitter': '1.846 ms',
             'Bandwidth': '9.98 Mbits/sec', 'Interval': '4.0- 5.0 sec'},
            {'Datagrams': '(0%)', 'Transfer': '1.19 MBytes', 'Lost/Total': '0/ 851', 'Jitter': '1.806 ms',
             'Bandwidth': '10.0 Mbits/sec', 'Interval': '5.0- 6.0 sec'},
            {'Datagrams': '(0.13%)', 'Transfer': '1.06 MBytes', 'Lost/Total': '1/ 755', 'Jitter': '1.803 ms',
             'Bandwidth': '8.87 Mbits/sec', 'Interval': '6.0- 7.0 sec'},
            {'Datagrams': '(0%)', 'Transfer': '1.19 MBytes', 'Lost/Total': '0/ 850', 'Jitter': '1.831 ms',
             'Bandwidth': '10.0 Mbits/sec', 'Interval': '7.0- 8.0 sec'},
            {'Datagrams': '(0%)', 'Transfer': '1.19 MBytes', 'Lost/Total': '0/ 850', 'Jitter': '1.841 ms',
             'Bandwidth': '10.0 Mbits/sec', 'Interval': '8.0- 9.0 sec'},
            {'Datagrams': '(0%)', 'Transfer': '1.19 MBytes', 'Lost/Total': '0/ 851', 'Jitter': '1.801 ms',
             'Bandwidth': '10.0 Mbits/sec', 'Interval': '9.0-10.0 sec'},
            {'Datagrams': '(0.11%)', 'Transfer': '11.8 MBytes', 'Lost/Total': '9/ 8409', 'Jitter': '2.618 ms',
             'Bandwidth': '9.86 Mbits/sec', 'Interval': '0.0-10.0 sec'}]},
    'INFO': ['Server listening on UDP port 5001', 'Receiving 1470 byte datagrams',
             'UDP buffer size: 8.00 KByte (default)']
}
