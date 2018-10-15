# -*- coding: utf-8 -*-
"""
Iperf command module.
"""

__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.util.converterhelper import ConverterHelper
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Iperf(GenericUnixCommand):
    def __init__(self, connection, options, prompt=None, newline_chars=None, runner=None):
        super(Iperf, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self.current_ret['CONNECTIONS'] = dict()
        self.current_ret['INFO'] = list()

        # private values
        self._connection_dict = dict()
        self._list_of_connections = dict()
        self._converter_helper = ConverterHelper()

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
            self._normalise_units(connection_report, info_dict)
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

    def _normalise_units(self, report, dictionary_to_update):
        for (index, item) in enumerate(report):
            if 'Bytes' in item or 'bits' in item:
                header = self._list_of_connections[index]
                raw_bites = self._converter_helper.to_bytes(item)[0]
                new_column_title = header + " Raw"
                read_bites = dictionary_to_update[header]
                dictionary_to_update[header] = raw_bites
                dictionary_to_update.update({new_column_title: read_bites})


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
            {'Bandwidth Raw': '240 Mbits/sec', 'Bandwidth': 251658240, 'Transfer Raw': '28.6 MBytes',
             'Transfer': 29989273, 'Interval': '0.0- 1.0 sec'},
            {'Bandwidth Raw': '217 Mbits/sec', 'Bandwidth': 227540992, 'Transfer Raw': '25.9 MBytes',
             'Transfer': 27158118, 'Interval': '1.0- 2.0 sec'},
            {'Bandwidth Raw': '222 Mbits/sec', 'Bandwidth': 232783872, 'Transfer Raw': '26.5 MBytes',
             'Transfer': 27787264, 'Interval': '2.0- 3.0 sec'},
            {'Bandwidth Raw': '223 Mbits/sec', 'Bandwidth': 233832448, 'Transfer Raw': '26.6 MBytes',
             'Transfer': 27892121, 'Interval': '3.0- 4.0 sec'},
            {'Bandwidth Raw': '218 Mbits/sec', 'Bandwidth': 228589568, 'Transfer Raw': '26.0 MBytes',
             'Transfer': 27262976, 'Interval': '4.0- 5.0 sec'},
            {'Bandwidth Raw': '220 Mbits/sec', 'Bandwidth': 230686720, 'Transfer Raw': '26.2 MBytes',
             'Transfer': 27472691, 'Interval': '5.0- 6.0 sec'},
            {'Bandwidth Raw': '224 Mbits/sec', 'Bandwidth': 234881024, 'Transfer Raw': '26.8 MBytes',
             'Transfer': 28101836, 'Interval': '6.0- 7.0 sec'},
            {'Bandwidth Raw': '218 Mbits/sec', 'Bandwidth': 228589568, 'Transfer Raw': '26.0 MBytes',
             'Transfer': 27262976, 'Interval': '7.0- 8.0 sec'},
            {'Bandwidth Raw': '216 Mbits/sec', 'Bandwidth': 226492416, 'Transfer Raw': '25.8 MBytes',
             'Transfer': 27053260, 'Interval': '8.0- 9.0 sec'},
            {'Bandwidth Raw': '221 Mbits/sec', 'Bandwidth': 231735296, 'Transfer Raw': '26.4 MBytes',
             'Transfer': 27682406, 'Interval': '9.0-10.0 sec'},
            {'Bandwidth Raw': '222 Mbits/sec', 'Bandwidth': 232783872, 'Transfer Raw': '265 MBytes',
             'Transfer': 277872640, 'Interval': '0.0-10.0 sec'}]},
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
    'CONNECTIONS': {
        'local 10.1.1.1 port 5001 connected with 10.6.2.5 port 32781': [{'Bandwidth Raw': '9.84 Mbits/sec',
                                                                         'Bandwidth': 10317987,
                                                                         'Datagrams': '(0%)',
                                                                         'Interval': '0.0- 1.0 sec',
                                                                         'Jitter': '1.830 ms',
                                                                         'Lost/Total': '0/ 837',
                                                                         'Transfer Raw': '1.17 MBytes',
                                                                         'Transfer': 1226833},
                                                                        {'Bandwidth Raw': '9.94 Mbits/sec',
                                                                         'Bandwidth': 10422845,
                                                                         'Datagrams': '(0.59%)',
                                                                         'Interval': '1.0- 2.0 sec',
                                                                         'Jitter': '1.846 ms',
                                                                         'Lost/Total': '5/ 850',
                                                                         'Transfer Raw': '1.18 MBytes',
                                                                         'Transfer': 1237319},
                                                                        {'Bandwidth Raw': '9.98 Mbits/sec',
                                                                         'Bandwidth': 10464788,
                                                                         'Datagrams': '(0.24%)',
                                                                         'Interval': '2.0- 3.0 sec',
                                                                         'Jitter': '1.802 ms',
                                                                         'Lost/Total': '2/ 851',
                                                                         'Transfer Raw': '1.19 MBytes',
                                                                         'Transfer': 1247805},
                                                                        {'Bandwidth Raw': '10.0 Mbits/sec',
                                                                         'Bandwidth': 10485760,
                                                                         'Datagrams': '(0%)',
                                                                         'Interval': '3.0- 4.0 sec',
                                                                         'Jitter': '1.830 ms',
                                                                         'Lost/Total': '0/ 850',
                                                                         'Transfer Raw': '1.19 MBytes',
                                                                         'Transfer': 1247805},
                                                                        {'Bandwidth Raw': '9.98 Mbits/sec',
                                                                         'Bandwidth': 10464788,
                                                                         'Datagrams': '(0.12%)',
                                                                         'Interval': '4.0- 5.0 sec',
                                                                         'Jitter': '1.846 ms',
                                                                         'Lost/Total': '1/ 850',
                                                                         'Transfer Raw': '1.19 MBytes',
                                                                         'Transfer': 1247805},
                                                                        {'Bandwidth Raw': '10.0 Mbits/sec',
                                                                         'Bandwidth': 10485760,
                                                                         'Datagrams': '(0%)',
                                                                         'Interval': '5.0- 6.0 sec',
                                                                         'Jitter': '1.806 ms',
                                                                         'Lost/Total': '0/ 851',
                                                                         'Transfer Raw': '1.19 MBytes',
                                                                         'Transfer': 1247805},
                                                                        {'Bandwidth Raw': '8.87 Mbits/sec',
                                                                         'Bandwidth': 9300869,
                                                                         'Datagrams': '(0.13%)',
                                                                         'Interval': '6.0- 7.0 sec',
                                                                         'Jitter': '1.803 ms',
                                                                         'Lost/Total': '1/ 755',
                                                                         'Transfer Raw': '1.06 MBytes',
                                                                         'Transfer': 1111490},
                                                                        {'Bandwidth Raw': '10.0 Mbits/sec',
                                                                         'Bandwidth': 10485760,
                                                                         'Datagrams': '(0%)',
                                                                         'Interval': '7.0- 8.0 sec',
                                                                         'Jitter': '1.831 ms',
                                                                         'Lost/Total': '0/ 850',
                                                                         'Transfer Raw': '1.19 MBytes',
                                                                         'Transfer': 1247805},
                                                                        {'Bandwidth Raw': '10.0 Mbits/sec',
                                                                         'Bandwidth': 10485760,
                                                                         'Datagrams': '(0%)',
                                                                         'Interval': '8.0- 9.0 sec',
                                                                         'Jitter': '1.841 ms',
                                                                         'Lost/Total': '0/ 850',
                                                                         'Transfer Raw': '1.19 MBytes',
                                                                         'Transfer': 1247805},
                                                                        {'Bandwidth Raw': '10.0 Mbits/sec',
                                                                         'Bandwidth': 10485760,
                                                                         'Datagrams': '(0%)',
                                                                         'Interval': '9.0-10.0 sec',
                                                                         'Jitter': '1.801 ms',
                                                                         'Lost/Total': '0/ 851',
                                                                         'Transfer Raw': '1.19 MBytes',
                                                                         'Transfer': 1247805},
                                                                        {'Bandwidth Raw': '9.86 Mbits/sec',
                                                                         'Bandwidth': 10338959,
                                                                         'Datagrams': '(0.11%)',
                                                                         'Interval': '0.0-10.0 sec',
                                                                         'Jitter': '2.618 ms',
                                                                         'Lost/Total': '9/ 8409',
                                                                         'Transfer Raw': '11.8 MBytes',
                                                                         'Transfer': 12373196}]},
    'INFO': ['Server listening on UDP port 5001', 'Receiving 1470 byte datagrams',
             'UDP buffer size: 8.00 KByte (default)']}

COMMAND_OUTPUT_multiple_connections = """
xyz@debian:~$ iperf -c 192.168.0.100 -P 20
------------------------------------------------------------
Client connecting to 192.168.0.100, TCP port 5001
TCP window size: 16.0 KByte (default)
------------------------------------------------------------
[ 15] local 192.168.0.102 port 57258 connected with 192.168.0.100 port 5001
[  3] local 192.168.0.102 port 57246 connected with 192.168.0.100 port 5001
[  4] local 192.168.0.102 port 57247 connected with 192.168.0.100 port 5001
[  5] local 192.168.0.102 port 57248 connected with 192.168.0.100 port 5001
[  7] local 192.168.0.102 port 57250 connected with 192.168.0.100 port 5001
[  6] local 192.168.0.102 port 57249 connected with 192.168.0.100 port 5001
[ 10] local 192.168.0.102 port 57253 connected with 192.168.0.100 port 5001
[  8] local 192.168.0.102 port 57251 connected with 192.168.0.100 port 5001
[  9] local 192.168.0.102 port 57252 connected with 192.168.0.100 port 5001
[ 16] local 192.168.0.102 port 57259 connected with 192.168.0.100 port 5001
[ 19] local 192.168.0.102 port 57261 connected with 192.168.0.100 port 5001
[ 18] local 192.168.0.102 port 57260 connected with 192.168.0.100 port 5001
[ 20] local 192.168.0.102 port 57262 connected with 192.168.0.100 port 5001
[ 17] local 192.168.0.102 port 57263 connected with 192.168.0.100 port 5001
[ 21] local 192.168.0.102 port 57264 connected with 192.168.0.100 port 5001
[ 11] local 192.168.0.102 port 57254 connected with 192.168.0.100 port 5001
[ 12] local 192.168.0.102 port 57255 connected with 192.168.0.100 port 5001
[ 13] local 192.168.0.102 port 57256 connected with 192.168.0.100 port 5001
[ 14] local 192.168.0.102 port 57257 connected with 192.168.0.100 port 5001
[ 22] local 192.168.0.102 port 57265 connected with 192.168.0.100 port 5001
[ ID] Interval       Transfer     Bandwidth
[  8]  0.0-10.6 sec  16.6 MBytes  13.1 Mbits/sec
[ 16]  0.0-10.6 sec  16.6 MBytes  13.1 Mbits/sec
[ 18]  0.0-10.6 sec  16.5 MBytes  13.1 Mbits/sec
[ 17]  0.0-10.7 sec  16.6 MBytes  13.0 Mbits/sec
[ 21]  0.0-10.7 sec  15.6 MBytes  12.3 Mbits/sec
[ 12]  0.0-10.7 sec  17.5 MBytes  13.7 Mbits/sec
[ 22]  0.0-10.7 sec  16.6 MBytes  13.0 Mbits/sec
[ 15]  0.0-10.8 sec  17.8 MBytes  13.8 Mbits/sec
[  3]  0.0-10.7 sec  18.5 MBytes  14.5 Mbits/sec
[  4]  0.0-10.8 sec  18.1 MBytes  14.1 Mbits/sec
[  5]  0.0-10.7 sec  17.6 MBytes  13.9 Mbits/sec
[  7]  0.0-10.8 sec  18.4 MBytes  14.3 Mbits/sec
[  6]  0.0-10.8 sec  17.0 MBytes  13.2 Mbits/sec
[ 10]  0.0-10.8 sec  16.8 MBytes  13.1 Mbits/sec
[  9]  0.0-10.8 sec  16.8 MBytes  13.0 Mbits/sec
[ 19]  0.0-10.6 sec  16.5 MBytes  13.0 Mbits/sec
[ 20]  0.0-10.7 sec  16.5 MBytes  12.9 Mbits/sec
[ 11]  0.0-10.7 sec  18.0 MBytes  14.0 Mbits/sec
[ 13]  0.0-10.7 sec  17.8 MBytes  13.9 Mbits/sec
[ 14]  0.0-10.8 sec  18.2 MBytes  14.1 Mbits/sec
[SUM]  0.0-10.8 sec   344 MBytes   266 Mbits/sec
xyz@debian:~$"""

COMMAND_KWARGS_multiple_connections = {
    'options': '-c 192.168.0.100 -P 20'
}

COMMAND_RESULT_multiple_connections = {
    'CONNECTIONS': {
        'local 192.168.0.102 port 57246 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '14.5 Mbits/sec',
                                                                                   'Bandwidth': 15204352,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '18.5 MBytes',
                                                                                   'Transfer': 19398656}],
        'local 192.168.0.102 port 57247 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '14.1 Mbits/sec',
                                                                                   'Bandwidth': 14784921,
                                                                                   'Interval': '0.0-10.8 sec',
                                                                                   'Transfer Raw': '18.1 MBytes',
                                                                                   'Transfer': 18979225}],
        'local 192.168.0.102 port 57248 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.9 Mbits/sec',
                                                                                   'Bandwidth': 14575206,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '17.6 MBytes',
                                                                                   'Transfer': 18454937}],
        'local 192.168.0.102 port 57249 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.2 Mbits/sec',
                                                                                   'Bandwidth': 13841203,
                                                                                   'Interval': '0.0-10.8 sec',
                                                                                   'Transfer Raw': '17.0 MBytes',
                                                                                   'Transfer': 17825792}],
        'local 192.168.0.102 port 57250 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '14.3 Mbits/sec',
                                                                                   'Bandwidth': 14994636,
                                                                                   'Interval': '0.0-10.8 sec',
                                                                                   'Transfer Raw': '18.4 MBytes',
                                                                                   'Transfer': 19293798}],
        'local 192.168.0.102 port 57251 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                                                   'Bandwidth': 13736345,
                                                                                   'Interval': '0.0-10.6 sec',
                                                                                   'Transfer Raw': '16.6 MBytes',
                                                                                   'Transfer': 17406361}],
        'local 192.168.0.102 port 57252 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                                                   'Bandwidth': 13631488,
                                                                                   'Interval': '0.0-10.8 sec',
                                                                                   'Transfer Raw': '16.8 MBytes',
                                                                                   'Transfer': 17616076}],
        'local 192.168.0.102 port 57253 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                                                   'Bandwidth': 13736345,
                                                                                   'Interval': '0.0-10.8 sec',
                                                                                   'Transfer Raw': '16.8 MBytes',
                                                                                   'Transfer': 17616076}],
        'local 192.168.0.102 port 57254 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '14.0 Mbits/sec',
                                                                                   'Bandwidth': 14680064,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '18.0 MBytes',
                                                                                   'Transfer': 18874368}],
        'local 192.168.0.102 port 57255 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.7 Mbits/sec',
                                                                                   'Bandwidth': 14365491,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '17.5 MBytes',
                                                                                   'Transfer': 18350080}],
        'local 192.168.0.102 port 57256 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.9 Mbits/sec',
                                                                                   'Bandwidth': 14575206,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '17.8 MBytes',
                                                                                   'Transfer': 18664652}],
        'local 192.168.0.102 port 57257 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '14.1 Mbits/sec',
                                                                                   'Bandwidth': 14784921,
                                                                                   'Interval': '0.0-10.8 sec',
                                                                                   'Transfer Raw': '18.2 MBytes',
                                                                                   'Transfer': 19084083}],
        'local 192.168.0.102 port 57258 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.8 Mbits/sec',
                                                                                   'Bandwidth': 14470348,
                                                                                   'Interval': '0.0-10.8 sec',
                                                                                   'Transfer Raw': '17.8 MBytes',
                                                                                   'Transfer': 18664652}],
        'local 192.168.0.102 port 57259 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                                                   'Bandwidth': 13736345,
                                                                                   'Interval': '0.0-10.6 sec',
                                                                                   'Transfer Raw': '16.6 MBytes',
                                                                                   'Transfer': 17406361}],
        'local 192.168.0.102 port 57260 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                                                   'Bandwidth': 13736345,
                                                                                   'Interval': '0.0-10.6 sec',
                                                                                   'Transfer Raw': '16.5 MBytes',
                                                                                   'Transfer': 17301504}],
        'local 192.168.0.102 port 57261 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                                                   'Bandwidth': 13631488,
                                                                                   'Interval': '0.0-10.6 sec',
                                                                                   'Transfer Raw': '16.5 MBytes',
                                                                                   'Transfer': 17301504}],
        'local 192.168.0.102 port 57262 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '12.9 Mbits/sec',
                                                                                   'Bandwidth': 13526630,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '16.5 MBytes',
                                                                                   'Transfer': 17301504}],
        'local 192.168.0.102 port 57263 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                                                   'Bandwidth': 13631488,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '16.6 MBytes',
                                                                                   'Transfer': 17406361}],
        'local 192.168.0.102 port 57264 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '12.3 Mbits/sec',
                                                                                   'Bandwidth': 12897484,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '15.6 MBytes',
                                                                                   'Transfer': 16357785}],
        'local 192.168.0.102 port 57265 connected with 192.168.0.100 port 5001': [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                                                   'Bandwidth': 13631488,
                                                                                   'Interval': '0.0-10.7 sec',
                                                                                   'Transfer Raw': '16.6 MBytes',
                                                                                   'Transfer': 17406361}]},
    'INFO': ['Client connecting to 192.168.0.100, TCP port 5001', 'TCP window size: 16.0 KByte (default)',
             '[SUM]  0.0-10.8 sec   344 MBytes   266 Mbits/sec']}
