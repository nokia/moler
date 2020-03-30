# -*- coding: utf-8 -*-
"""
Iperf2 command module.

It is refactored Iperf module changing data format returned.
New format doesn't require additional post processing of values inside returned dict
(it was the case with old one)

Moreover, new format provides final report - see bellow.

iperf2 was orphaned in the late 2000s at version 2.0.5
Then in 2014, Bob (Robert) McMahon from Broadcom restarted development of iperf2
Official iperf2 releases after 2.0.5: https://sourceforge.net/projects/iperf2/files/
Important changes:
- starting from 2.0.8 -b may be used to limit bandwidth at TCP
- as a consequence -b doesn't force -u
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.util.converterhelper import ConverterHelper
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.publisher import Publisher


class Iperf2(GenericUnixCommand, Publisher):
    """
    Run iperf command, return its statistics and report.

    Single line of iperf output may look like::

      [ ID]   Interval       Transfer      Bandwidth        Jitter   Lost/Total Datagrams
      [904]   0.0- 1.0 sec   1.17 MBytes   9.84 Mbits/sec   1.830 ms    0/ 837   (0%)

    It represents data transfer statistics reported per given interval.
    This line is parsed out and produces statistics record as python dict.
    (examples can be found at bottom of iperf2.py source code)
    Some keys inside dict are normalized to Bytes.
    In such case you will see both: raw and normalized values::

      'Transfer Raw':     '1.17 MBytes',
      'Transfer':         1226833,           # Bytes
      'Bandwidth Raw':    '9.84 Mbits/sec',
      'Bandwidth':        1230000,           # Bytes/sec

    Iperf statistics are stored under connection name with format
    (client_port@client_IP, server_port@server_IP)
    It represents iperf output line (iperf server example below) like::

      [  3] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 56262
      ("56262@192.168.0.10", "5016@192.168.0.12"): [<statistics dicts here>]

    Iperf returned value has also additional connection named "report connection".
    It has format
    (client_IP, server_port@server_IP)
    So, for above example you should expect structure like::

      ("192.168.0.10", "5016@192.168.0.12"): {'report': {<report dict here>}}

    """
    def __init__(self, connection, options, prompt=None, newline_chars=None, runner=None):
        """
        Create iperf2 command

        :param connection: moler connection used by iperf command
        :param options: iperf options (as in iperf documentation)
        :param prompt: prompt (regexp) where iperf starts from, if None - default prompt regexp used
        :param newline_chars: expected newline characters of iperf output
        :param runner: runner used for command
        """
        super(Iperf2, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.port, self.options = self._validate_options(options)
        self.current_ret['CONNECTIONS'] = dict()
        self.current_ret['INFO'] = list()

        # private values
        self._connection_dict = dict()
        self._converter_helper = ConverterHelper()
        self._got_server_report_hdr = False
        self._got_server_report = False
        self._stopping_server = False

    _re_port = re.compile(r"(?P<PORT_OPTION>\-\-port|\-p)\s+(?P<PORT>\d+)")

    def _validate_options(self, options):
        if (('-d' in options) or ('--dualtest' in options)) and (('-P' in options) or ('--parallel' in options)):
            raise AttributeError("Unsupported options combination (--dualtest & --parallel)")
        if self._regex_helper.search_compiled(Iperf2._re_port, options):
            port = int(self._regex_helper.group('PORT'))
        else:
            port = 5001
        return port, options

    def build_command_string(self):
        cmd = 'iperf ' + str(self.options)
        return cmd

    @property
    def protocol(self):
        if self.options.startswith('-u') or (' -u' in self.options) or ('--udp' in self.options):
            return 'udp'
        return 'tcp'

    _re_interval = re.compile(r"(?P<INTERVAL_OPTION>\-\-interval|\-i)\s+(?P<INTERVAL>[\d\.]+)")

    @property
    def interval(self):
        if self._regex_helper.search_compiled(Iperf2._re_interval, self.options):
            return float(self._regex_helper.group('INTERVAL'))
        return 0.0

    _re_time = re.compile(r"(?P<TIME_OPTION>\-\-time|\-t)\s+(?P<TIME>[\d\.]+)")

    @property
    def time(self):
        if self._regex_helper.search_compiled(Iperf2._re_time, self.options):
            return float(self._regex_helper.group('TIME'))
        return 10.0

    @property
    def dualtest(self):
        return ('--dualtest' in self.options) or ('-d' in self.options)

    @property
    def works_in_dualtest(self):
        if self.client:
            return self.dualtest
        if self.parallel_client:
            return False
        connections = self._connection_dict.values()
        return len(connections) > 1

    @property
    def client(self):
        return ('-c ' in self.options) or ('--client ' in self.options)

    @property
    def server(self):
        return self.options.startswith('-s') or (' -s' in self.options) or ('--server' in self.options)

    @property
    def parallel_client(self):
        if self.client:
            return ('-P ' in self.options) or ('--parallel ' in self.options)
        if len(self._connection_dict.keys()) > 1:
            # all remote connections must be same otherwise it is --dualtest requested from server
            _, first_remote = list(self._connection_dict.values())[0]
            for _, remote in self._connection_dict.values():
                if remote != first_remote:
                    return False
            return True
        return False

    @property
    def singlerun_server(self):
        if self.client:
            return False
        singlerun_param_nonlast = ('-P 1 ' in self.options) or ('--parallel 1 ' in self.options)
        singlerun_param_as_last = self.options.endswith('-P 1') or self.options.endswith('--parallel 1')
        return singlerun_param_nonlast or singlerun_param_as_last

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse_connection_name_and_id(line)
                self._parse_headers(line)
                self._parse_connection_info(line)
                self._parse_too_early_ctrl_c(line)
                self._parse_svr_report_header(line)
                self._parse_connection_headers(line)
            except ParsingDone:
                pass
        return super(Iperf2, self).on_new_line(line, is_full_line)

    def _process_line_from_command(self, current_chunk, line, is_full_line):
        decoded_line = self._decode_line(line=line)
        if self._is_replicated_cmd_echo(line):
            return
        self.on_new_line(line=decoded_line, is_full_line=is_full_line)

    def _is_replicated_cmd_echo(self, line):
        prompt_and_command = r'{}\s*{}'.format(self._re_prompt.pattern, self.command_string)
        found_echo = self._regex_helper.search(prompt_and_command, line)
        return found_echo is not None

    def subscribe(self, subscriber):
        """
        Subscribe for notifications about iperf statistic as it comes.

        Anytime we find iperf statistics line like:
        [  3]  2.0- 3.0 sec   612 KBytes  5010 Kbits/sec   0.022 ms    0/  426 (0%)
        such line is parsed and published to subscriber

        Subscriber must be function or method with following signature (name doesn't matter):

            def iperf_observer(from_client, to_server, data_record=None, report=None):
                ...

        Either data_record is published or report.
        Report is published on last line of iperf statistics summarizing stats for whole period:
        [904]   0.0-10.0 sec   11.8 MBytes   9.86 Mbits/sec   2.618 ms   9/ 8409  (0.11%)

        :param subscriber: function to be called to notify about data.
        """
        super(Iperf2, self).subscribe(subscriber)

    def is_end_of_cmd_output(self, line):
        """
        Checks if end of command is reached.

        For iperf server we can't await prompt since at server it is not displayed

        :param line: Line from device.
        :return:
        """
        if self.server:
            if self._has_all_reports():
                self._stop_server()
                return super(Iperf2, self).is_end_of_cmd_output(line)
            return False
        else:
            return super(Iperf2, self).is_end_of_cmd_output(line)

    def _stop_server(self):
        if not self._stopping_server:
            if not self.singlerun_server:
                self.break_cmd()
            self._stopping_server = True

    _re_command_failure = re.compile(r"(?P<FAILURE_MSG>.*failed.*|.*error.*|.*command not found.*|.*iperf:.*)")

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Iperf2._re_command_failure, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("FAILURE_MSG"))))
            raise ParsingDone

    # [  3] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 56262
    # [  5] local 192.168.0.12 port 47384 connected with 192.168.0.10 port 5016
    # [  4] local fd00::2:0 port 49597 connected with fd00::1:0 port 5901
    _r_conn_info = r"(\[\s*\d*\])\s+local\s+(\S+)\s+port\s+(\d+)\s+connected with\s+(\S+)\s+port\s+(\d+)"
    _re_connection_info = re.compile(_r_conn_info)

    def _parse_connection_name_and_id(self, line):
        if self._regex_helper.search_compiled(Iperf2._re_connection_info, line):
            connection_id, local_host, local_port, remote_host, remote_port = self._regex_helper.groups()
            local = "{}@{}".format(local_port, local_host)
            remote = "{}@{}".format(remote_port, remote_host)
            if self.port == int(remote_port):
                from_client, to_server = local, remote
            else:
                from_client, to_server = remote, local
            connection_dict = {connection_id: (from_client, to_server)}
            self._connection_dict.update(connection_dict)
            raise ParsingDone

    # iperf output for: udp client, tcp client, tcp server
    # [ ID] Interval       Transfer     Bandwidth

    # iperf output for: udp server
    # [ ID] Interval       Transfer     Bandwidth        Jitter   Lost/Total Datagrams
    _re_headers = re.compile(r"\[\s+ID\]\s+Interval\s+Transfer\s+Bandwidth")

    def _parse_headers(self, line):
        if self._regex_helper.search_compiled(Iperf2._re_headers, line):
            if self.parallel_client:
                # header line is after connections
                # so, we can create virtual Summary connection
                client, server = list(self._connection_dict.values())[0]
                client_host, client_port, server_host, server_port = self._split_connection_name((client, server))
                connection_id = '[SUM]'
                self._connection_dict[connection_id] = ("{}@{}".format("multiport", client_host), server)
            raise ParsingDone

    def _split_connection_name(self, connection_name):
        client, server = connection_name
        client_port, client_host = client.split("@")
        server_port, server_host = server.split("@")
        return client_host, client_port, server_host, server_port

    # tcp:
    # [ ID] Interval       Transfer     Bandwidth
    # [  4]  0.0- 1.0 sec   979 KBytes  8020 Kbits/sec
    #
    # udp:
    # [ ID] Interval       Transfer     Bandwidth        Jitter   Lost/Total Datagrams
    # [  3]  0.0- 1.0 sec   612 KBytes  5010 Kbits/sec   0.022 ms    0/  426 (0%)

    _r_id = r"(?P<ID>\[\s*\d*\]|\[SUM\])"
    _r_interval = r"(?P<Interval>[\d\.]+\-\s*[\d\.]+)\s*sec"
    _r_transfer = r"(?P<Transfer>[\d\.]+\s+\w+)"
    _r_bandwidth = r"(?P<Bandwidth>[\d\.]+\s+\w+/sec)"
    _r_jitter = r"(?P<Jitter>\d+\.\d+\s\w+)"
    _r_datagrams = r"(?P<Lost_vs_Total_Datagrams>\d+/\s*\d+)\s*\((?P<Lost_Datagrams_ratio>[\d\.]+\%)\)"
    _r_rec = r"{}\s+{}\s+{}\s+{}".format(_r_id, _r_interval, _r_transfer, _r_bandwidth)
    _r_rec_udp_svr = r"{}\s+{}\s+{}".format(_r_rec, _r_jitter, _r_datagrams)
    _re_iperf_record = re.compile(_r_rec)
    _re_iperf_record_udp_svr = re.compile(_r_rec_udp_svr)

    def _parse_connection_info(self, line):
        regex_found = self._regex_helper.search_compiled
        if regex_found(Iperf2._re_iperf_record_udp_svr, line) or regex_found(Iperf2._re_iperf_record, line):
            iperf_record = self._regex_helper.groupdict()
            connection_id = iperf_record.pop("ID")
            iperf_record = self._detailed_parse_interval(iperf_record)
            iperf_record = self._detailed_parse_datagrams(iperf_record)
            # [SUM]  0.0- 4.0 sec  1057980 KBytes  2165942 Kbits/sec   last line when server used with -P
            if (not self.parallel_client) and (connection_id == '[SUM]'):
                raise ParsingDone  # skip it
            connection_name = self._connection_dict[connection_id]
            normalized_iperf_record = self._normalize_to_bytes(iperf_record)
            self._update_current_ret(connection_name, normalized_iperf_record)
            self._parse_final_record(connection_name)
            if self.protocol == 'udp' and self._got_server_report_hdr:
                self._got_server_report = True
            raise ParsingDone

    @staticmethod
    def _detailed_parse_interval(iperf_record):
        start, end = iperf_record["Interval"].split('-')
        iperf_record["Interval"] = (float(start), float(end))
        return iperf_record

    @staticmethod
    def _detailed_parse_datagrams(iperf_record):
        if "Lost_vs_Total_Datagrams" in iperf_record:
            lost, total = iperf_record["Lost_vs_Total_Datagrams"].split('/')
            iperf_record["Lost_vs_Total_Datagrams"] = (int(lost), int(total))
        return iperf_record

    def _update_current_ret(self, connection_name, info_dict):
        if connection_name in self.current_ret['CONNECTIONS']:
            self.current_ret['CONNECTIONS'][connection_name].append(info_dict)
        else:
            connection_dict = {connection_name: [info_dict]}
            self.current_ret['CONNECTIONS'].update(connection_dict)

    def _parse_final_record(self, connection_name):
        last_record = self.current_ret['CONNECTIONS'][connection_name][-1]
        if self._is_final_record(last_record):
            if self.parallel_client and ('multiport' not in connection_name[0]):
                return  # for parallel we take report only from [SUM] final record
            client_host, client_port, server_host, server_port = self._split_connection_name(connection_name)
            from_client, to_server = client_host, "{}@{}".format(server_port, server_host)
            result_connection = (from_client, to_server)
            self.current_ret['CONNECTIONS'][result_connection] = {'report': last_record}
            self.notify_subscribers(from_client=from_client, to_server=to_server, report=last_record)
        else:
            from_client, to_server = connection_name
            self.notify_subscribers(from_client=from_client, to_server=to_server, data_record=last_record)

    def _is_final_record(self, last_record):
        start, end = last_record['Interval']
        if self.interval and (self.interval < self.time):  # interval reports
            final = (start == 0.0) and (end > self.interval)
        else:  # only final report
            final = start == 0.0
        return final

    def _has_all_reports(self):
        if len(self._connection_dict) < 1:
            return False
        result = self.current_ret['CONNECTIONS']
        connections = list(self._connection_dict.values())
        client_host, client_port, server_host, server_port = self._split_connection_name(connections[0])
        from_client, to_server = client_host, "{}@{}".format(self.port, server_host)
        has_client_report = (from_client, to_server) in result
        if self.works_in_dualtest:  # need two reports
            from_server, to_client = server_host, "{}@{}".format(self.port, client_host)
            has_server_report = ((from_server, to_client) in result)
            all_reports = has_client_report and has_server_report
            works_as_client = True  # in dualtest both server and client work as client
        else:
            all_reports = has_client_report
            works_as_client = self.client
        # udp client additionally awaits server report
        if self.protocol == 'udp' and works_as_client:
            all_reports = all_reports and self._got_server_report
        return all_reports

    # [  5] Sent 2552 datagrams
    # ------------------------------------------------------------
    _re_ornaments = re.compile(r"(?P<ORNAMENTS>----*|\[\s*ID\].*)", re.IGNORECASE)

    def _parse_connection_headers(self, line):
        if not self._regex_helper.search_compiled(Iperf2._re_ornaments, line):
            self.current_ret['INFO'].append(line.strip())
            raise ParsingDone

    def _parse_svr_report_header(self, line):
        if "Server Report:" in line:
            self._got_server_report_hdr = True
            raise ParsingDone

    def _normalize_to_bytes(self, input_dict):
        new_dict = {}
        for (key, raw_value) in input_dict.items():
            if 'Bytes' in raw_value:  # iperf MBytes means 1024 * 1024 Bytes - see iperf.fr/iperf-doc.php
                new_dict[key + " Raw"] = raw_value
                value_in_bytes, _, _ = self._converter_helper.to_bytes(raw_value)
                new_dict[key] = value_in_bytes
            elif 'bits' in raw_value:  # iperf Mbits means 1000 * 1000 bits - see iperf.fr/iperf-doc.php
                new_dict[key + " Raw"] = raw_value
                value_in_bits, _, _ = self._converter_helper.to_bytes(raw_value, binary_multipliers=False)
                value_in_bytes = value_in_bits // 8
                new_dict[key] = value_in_bytes
            else:
                new_dict[key] = raw_value
        return new_dict

    # ^CWaiting for server threads to complete. Interrupt again to force quit
    _re_interrupt_again = re.compile(r"Interrupt again to force quit")

    def _parse_too_early_ctrl_c(self, line):
        # Happens at script execution. Scripts are quicker then humans.
        if self._regex_helper.search_compiled(Iperf2._re_interrupt_again, line):
            self.break_cmd()  # send Ctrl-C once more
            raise ParsingDone


COMMAND_OUTPUT_basic_client = """
xyz@debian:~$ iperf -c 10.1.1.1 -i 1
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
    'options': '-c 10.1.1.1 -i 1'
}

COMMAND_RESULT_basic_client = {
    'CONNECTIONS':
        {("49597@192.168.0.102", "5001@192.168.0.100"): [
            {'Bandwidth Raw': '240 Mbits/sec', 'Bandwidth': 30000000, 'Transfer Raw': '28.6 MBytes',
             'Transfer': 29989273, 'Interval': (0.0, 1.0)},
            {'Bandwidth Raw': '217 Mbits/sec', 'Bandwidth': 27125000, 'Transfer Raw': '25.9 MBytes',
             'Transfer': 27158118, 'Interval': (1.0, 2.0)},
            {'Bandwidth Raw': '222 Mbits/sec', 'Bandwidth': 27750000, 'Transfer Raw': '26.5 MBytes',
             'Transfer': 27787264, 'Interval': (2.0, 3.0)},
            {'Bandwidth Raw': '223 Mbits/sec', 'Bandwidth': 27875000, 'Transfer Raw': '26.6 MBytes',
             'Transfer': 27892121, 'Interval': (3.0, 4.0)},
            {'Bandwidth Raw': '218 Mbits/sec', 'Bandwidth': 27250000, 'Transfer Raw': '26.0 MBytes',
             'Transfer': 27262976, 'Interval': (4.0, 5.0)},
            {'Bandwidth Raw': '220 Mbits/sec', 'Bandwidth': 27500000, 'Transfer Raw': '26.2 MBytes',
             'Transfer': 27472691, 'Interval': (5.0, 6.0)},
            {'Bandwidth Raw': '224 Mbits/sec', 'Bandwidth': 28000000, 'Transfer Raw': '26.8 MBytes',
             'Transfer': 28101836, 'Interval': (6.0, 7.0)},
            {'Bandwidth Raw': '218 Mbits/sec', 'Bandwidth': 27250000, 'Transfer Raw': '26.0 MBytes',
             'Transfer': 27262976, 'Interval': (7.0, 8.0)},
            {'Bandwidth Raw': '216 Mbits/sec', 'Bandwidth': 27000000, 'Transfer Raw': '25.8 MBytes',
             'Transfer': 27053260, 'Interval': (8.0, 9.0)},
            {'Bandwidth Raw': '221 Mbits/sec', 'Bandwidth': 27625000, 'Transfer Raw': '26.4 MBytes',
             'Transfer': 27682406, 'Interval': (9.0, 10.0)},
            {'Bandwidth Raw': '222 Mbits/sec', 'Bandwidth': 27750000, 'Transfer Raw': '265 MBytes',
             'Transfer': 277872640, 'Interval': (0.0, 10.0)}],
         ("192.168.0.102", "5001@192.168.0.100"):
            {'report': {'Transfer': 277872640, 'Bandwidth': 27750000, 'Transfer Raw': '265 MBytes',
                        'Bandwidth Raw': '222 Mbits/sec', 'Interval': (0.0, 10.0)}}},
    'INFO': ['Client connecting to 10.1.1.1, TCP port 5001', 'TCP window size: 16384 Byte (default)']
}


COMMAND_OUTPUT_basic_server = """
xyz@debian:~$ iperf -s -u -i 1
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
    'options': '-s -u -i 1'
}

COMMAND_RESULT_basic_server = {
    'CONNECTIONS': {
        ("32781@10.6.2.5", "5001@10.1.1.1"): [{'Bandwidth Raw': '9.84 Mbits/sec',
                                               'Bandwidth': 1230000,
                                               'Interval': (0.0, 1.0),
                                               'Jitter': '1.830 ms',
                                               'Lost_vs_Total_Datagrams': (0, 837),
                                               'Lost_Datagrams_ratio': '0%',
                                               'Transfer Raw': '1.17 MBytes',
                                               'Transfer': 1226833},
                                              {'Bandwidth Raw': '9.94 Mbits/sec',
                                               'Bandwidth': 1242500,
                                               'Interval': (1.0, 2.0),
                                               'Jitter': '1.846 ms',
                                               'Lost_vs_Total_Datagrams': (5, 850),
                                               'Lost_Datagrams_ratio': '0.59%',
                                               'Transfer Raw': '1.18 MBytes',
                                               'Transfer': 1237319},
                                              {'Bandwidth Raw': '9.98 Mbits/sec',
                                               'Bandwidth': 1247500,
                                               'Interval': (2.0, 3.0),
                                               'Jitter': '1.802 ms',
                                               'Lost_vs_Total_Datagrams': (2, 851),
                                               'Lost_Datagrams_ratio': '0.24%',
                                               'Transfer Raw': '1.19 MBytes',
                                               'Transfer': 1247805},
                                              {'Bandwidth Raw': '10.0 Mbits/sec',
                                               'Bandwidth': 1250000,
                                               'Interval': (3.0, 4.0),
                                               'Jitter': '1.830 ms',
                                               'Lost_vs_Total_Datagrams': (0, 850),
                                               'Lost_Datagrams_ratio': '0%',
                                               'Transfer Raw': '1.19 MBytes',
                                               'Transfer': 1247805},
                                              {'Bandwidth Raw': '9.98 Mbits/sec',
                                               'Bandwidth': 1247500,
                                               'Interval': (4.0, 5.0),
                                               'Jitter': '1.846 ms',
                                               'Lost_vs_Total_Datagrams': (1, 850),
                                               'Lost_Datagrams_ratio': '0.12%',
                                               'Transfer Raw': '1.19 MBytes',
                                               'Transfer': 1247805},
                                              {'Bandwidth Raw': '10.0 Mbits/sec',
                                               'Bandwidth': 1250000,
                                               'Interval': (5.0, 6.0),
                                               'Jitter': '1.806 ms',
                                               'Lost_vs_Total_Datagrams': (0, 851),
                                               'Lost_Datagrams_ratio': '0%',
                                               'Transfer Raw': '1.19 MBytes',
                                               'Transfer': 1247805},
                                              {'Bandwidth Raw': '8.87 Mbits/sec',
                                               'Bandwidth': 1108750,
                                               'Interval': (6.0, 7.0),
                                               'Jitter': '1.803 ms',
                                               'Lost_vs_Total_Datagrams': (1, 755),
                                               'Lost_Datagrams_ratio': '0.13%',
                                               'Transfer Raw': '1.06 MBytes',
                                               'Transfer': 1111490},
                                              {'Bandwidth Raw': '10.0 Mbits/sec',
                                               'Bandwidth': 1250000,
                                               'Interval': (7.0, 8.0),
                                               'Jitter': '1.831 ms',
                                               'Lost_vs_Total_Datagrams': (0, 850),
                                               'Lost_Datagrams_ratio': '0%',
                                               'Transfer Raw': '1.19 MBytes',
                                               'Transfer': 1247805},
                                              {'Bandwidth Raw': '10.0 Mbits/sec',
                                               'Bandwidth': 1250000,
                                               'Interval': (8.0, 9.0),
                                               'Jitter': '1.841 ms',
                                               'Lost_vs_Total_Datagrams': (0, 850),
                                               'Lost_Datagrams_ratio': '0%',
                                               'Transfer Raw': '1.19 MBytes',
                                               'Transfer': 1247805},
                                              {'Bandwidth Raw': '10.0 Mbits/sec',
                                               'Bandwidth': 1250000,
                                               'Interval': (9.0, 10.0),
                                               'Jitter': '1.801 ms',
                                               'Lost_vs_Total_Datagrams': (0, 851),
                                               'Lost_Datagrams_ratio': '0%',
                                               'Transfer Raw': '1.19 MBytes',
                                               'Transfer': 1247805},
                                              {'Bandwidth Raw': '9.86 Mbits/sec',
                                               'Bandwidth': 1232500,
                                               'Interval': (0.0, 10.0),
                                               'Jitter': '2.618 ms',
                                               'Lost_vs_Total_Datagrams': (9, 8409),
                                               'Lost_Datagrams_ratio': '0.11%',
                                               'Transfer Raw': '11.8 MBytes',
                                               'Transfer': 12373196}],
        ("10.6.2.5", "5001@10.1.1.1"): {'report': {'Lost_Datagrams_ratio': '0.11%',
                                                   'Jitter': '2.618 ms',
                                                   'Transfer': 12373196,
                                                   'Interval': (0.0, 10.0),
                                                   'Transfer Raw': '11.8 MBytes',
                                                   'Bandwidth': 1232500,
                                                   'Lost_vs_Total_Datagrams': (9, 8409),
                                                   'Bandwidth Raw': '9.86 Mbits/sec'}}},
    'INFO': ['Server listening on UDP port 5001', 'Receiving 1470 byte datagrams',
             'UDP buffer size: 8.00 KByte (default)']}


COMMAND_OUTPUT_tcp_ipv6_server = """
xyz@debian:~$ iperf -s -V -p 5901 -i 1.0
------------------------------------------------------------
Server listening on TCP port 5901
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  4] local fd00::1:0 port 5901 connected with fd00::2:0 port 48836
[ ID] Interval       Transfer     Bandwidth
[  4]  0.0- 1.0 sec  2.97 GBytes  25.6 Gbits/sec
[  4]  1.0- 2.0 sec  2.65 GBytes  22.7 Gbits/sec
[  4]  2.0- 3.0 sec  3.23 GBytes  27.7 Gbits/sec
[  4]  3.0- 4.0 sec  2.94 GBytes  25.3 Gbits/sec
[  4]  0.0- 4.0 sec  11.8 GBytes  25.3 Gbits/sec
xyz@debian:~$"""


COMMAND_KWARGS_tcp_ipv6_server = {
    'options': '-s -V -p 5901 -i 1.0'
}

COMMAND_RESULT_tcp_ipv6_server = {
    'CONNECTIONS': {
        ("48836@fd00::2:0", "5901@fd00::1:0"): [{'Transfer': 3189013217,
                                                 'Bandwidth': 3200000000,
                                                 'Transfer Raw': '2.97 GBytes',
                                                 'Bandwidth Raw': '25.6 Gbits/sec',
                                                 'Interval': (0.0, 1.0)},
                                                {'Transfer': 2845415833,
                                                 'Bandwidth': 2837500000,
                                                 'Transfer Raw': '2.65 GBytes',
                                                 'Bandwidth Raw': '22.7 Gbits/sec',
                                                 'Interval': (1.0, 2.0)},
                                                {'Transfer': 3468186091,
                                                 'Bandwidth': 3462500000,
                                                 'Transfer Raw': '3.23 GBytes',
                                                 'Bandwidth Raw': '27.7 Gbits/sec',
                                                 'Interval': (2.0, 3.0)},
                                                {'Transfer': 3156800962,
                                                 'Bandwidth': 3162500000,
                                                 'Transfer Raw': '2.94 GBytes',
                                                 'Bandwidth Raw': '25.3 Gbits/sec',
                                                 'Interval': (3.0, 4.0)},
                                                {'Transfer': 12670153523,
                                                 'Bandwidth': 3162500000,
                                                 'Transfer Raw': '11.8 GBytes',
                                                 'Bandwidth Raw': '25.3 Gbits/sec',
                                                 'Interval': (0.0, 4.0)}],
        ("fd00::2:0", "5901@fd00::1:0"): {'report': {'Transfer': 12670153523,
                                                     'Bandwidth': 3162500000,
                                                     'Transfer Raw': '11.8 GBytes',
                                                     'Bandwidth Raw': '25.3 Gbits/sec',
                                                     'Interval': (0.0, 4.0)}}},
    'INFO': ['Server listening on TCP port 5901',
             'TCP window size: 85.3 KByte (default)']}


COMMAND_OUTPUT_tcp_ipv6_client = """
xyz@debian:~$ iperf -c fd00::1:0 -V -p 5901 -i 1.0
------------------------------------------------------------
Client connecting to fd00::1:0, TCP port 5901
TCP window size: 2565 Byte (default)
------------------------------------------------------------
[  3] local fd00::2:0 port 49597 connected with fd00::1:0 port 5901
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


COMMAND_KWARGS_tcp_ipv6_client = {
    'options': '-c fd00::1:0 -V -p 5901 -i 1.0'
}

COMMAND_RESULT_tcp_ipv6_client = {
    'CONNECTIONS':
        {("49597@fd00::2:0", "5901@fd00::1:0"): [
            {'Bandwidth Raw': '240 Mbits/sec', 'Bandwidth': 30000000, 'Transfer Raw': '28.6 MBytes',
             'Transfer': 29989273, 'Interval': (0.0, 1.0)},
            {'Bandwidth Raw': '217 Mbits/sec', 'Bandwidth': 27125000, 'Transfer Raw': '25.9 MBytes',
             'Transfer': 27158118, 'Interval': (1.0, 2.0)},
            {'Bandwidth Raw': '222 Mbits/sec', 'Bandwidth': 27750000, 'Transfer Raw': '26.5 MBytes',
             'Transfer': 27787264, 'Interval': (2.0, 3.0)},
            {'Bandwidth Raw': '223 Mbits/sec', 'Bandwidth': 27875000, 'Transfer Raw': '26.6 MBytes',
             'Transfer': 27892121, 'Interval': (3.0, 4.0)},
            {'Bandwidth Raw': '218 Mbits/sec', 'Bandwidth': 27250000, 'Transfer Raw': '26.0 MBytes',
             'Transfer': 27262976, 'Interval': (4.0, 5.0)},
            {'Bandwidth Raw': '220 Mbits/sec', 'Bandwidth': 27500000, 'Transfer Raw': '26.2 MBytes',
             'Transfer': 27472691, 'Interval': (5.0, 6.0)},
            {'Bandwidth Raw': '224 Mbits/sec', 'Bandwidth': 28000000, 'Transfer Raw': '26.8 MBytes',
             'Transfer': 28101836, 'Interval': (6.0, 7.0)},
            {'Bandwidth Raw': '218 Mbits/sec', 'Bandwidth': 27250000, 'Transfer Raw': '26.0 MBytes',
             'Transfer': 27262976, 'Interval': (7.0, 8.0)},
            {'Bandwidth Raw': '216 Mbits/sec', 'Bandwidth': 27000000, 'Transfer Raw': '25.8 MBytes',
             'Transfer': 27053260, 'Interval': (8.0, 9.0)},
            {'Bandwidth Raw': '221 Mbits/sec', 'Bandwidth': 27625000, 'Transfer Raw': '26.4 MBytes',
             'Transfer': 27682406, 'Interval': (9.0, 10.0)},
            {'Bandwidth Raw': '222 Mbits/sec', 'Bandwidth': 27750000, 'Transfer Raw': '265 MBytes',
             'Transfer': 277872640, 'Interval': (0.0, 10.0)}],
         ("fd00::2:0", "5901@fd00::1:0"):
            {'report': {'Transfer': 277872640, 'Bandwidth': 27750000, 'Transfer Raw': '265 MBytes',
                        'Bandwidth Raw': '222 Mbits/sec', 'Interval': (0.0, 10.0)}}},
    'INFO': ['Client connecting to fd00::1:0, TCP port 5901', 'TCP window size: 2565 Byte (default)']
}


COMMAND_OUTPUT_bidirectional_udp_client = """
abc@debian:~$ iperf -c 192.168.0.12 -u -p 5016 -f k -i 1.0 -t 6.0 --dualtest -b 5000.0k
------------------------------------------------------------
Server listening on UDP port 5016
Receiving 1470 byte datagrams
UDP buffer size: 1024 KByte (default)
------------------------------------------------------------
------------------------------------------------------------
Client connecting to 192.168.0.12, UDP port 5016
Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)
UDP buffer size: 1024 KByte (default)
------------------------------------------------------------
[  4] local 192.168.0.10 port 56262 connected with 192.168.0.12 port 5016
[  3] local 192.168.0.10 port 5016 connected with 192.168.0.12 port 47384
[ ID] Interval       Transfer     Bandwidth
[  4]  0.0- 1.0 sec   613 KBytes  5022 Kbits/sec
[  3]  0.0- 1.0 sec   612 KBytes  5010 Kbits/sec   0.011 ms    0/  426 (0%)
[  4]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec
[  3]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec   0.012 ms    0/  425 (0%)
[  4]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec
[  3]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec   0.017 ms    0/  425 (0%)
[  4]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec
[  3]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec   0.019 ms    0/  425 (0%)
[  4]  4.0- 5.0 sec   610 KBytes  4998 Kbits/sec
[  3]  4.0- 5.0 sec   610 KBytes  4998 Kbits/sec   0.014 ms    0/  425 (0%)
[  4]  5.0- 6.0 sec   610 KBytes  4998 Kbits/sec
[  4]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec
[  4] Sent 2552 datagrams
[  3]  5.0- 6.0 sec   612 KBytes  5010 Kbits/sec   0.017 ms    0/  426 (0%)
[  3]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.017 ms    0/ 2552 (0%)
[  4] Server Report:
[  4]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.017 ms    0/ 2552 (0%)
abc@debian:~$"""


COMMAND_KWARGS_bidirectional_udp_client = {
    'options': '-c 192.168.0.12 -u -p 5016 -f k -i 1.0 -t 6.0 --dualtest -b 5000.0k'
}


COMMAND_RESULT_bidirectional_udp_client = {
    'CONNECTIONS': {
        ("56262@192.168.0.10", "5016@192.168.0.12"): [{'Transfer': 627712,
                                                       'Bandwidth': 627750,
                                                       'Transfer Raw': '613 KBytes',
                                                       'Bandwidth Raw': '5022 Kbits/sec',
                                                       'Interval': (0.0, 1.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (1.0, 2.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (2.0, 3.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (3.0, 4.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (4.0, 5.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (5.0, 6.0)},
                                                      {'Transfer': 3751936,
                                                       'Bandwidth': 625000,
                                                       'Transfer Raw': '3664 KBytes',
                                                       'Bandwidth Raw': '5000 Kbits/sec',
                                                       'Interval': (0.0, 6.0)},
                                                      {'Transfer Raw': '3664 KBytes',
                                                       'Jitter': '0.017 ms',
                                                       'Transfer': 3751936,
                                                       'Interval': (0.0, 6.0),
                                                       'Bandwidth': 625000,
                                                       'Lost_vs_Total_Datagrams': (0, 2552),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5000 Kbits/sec'}],
        ("47384@192.168.0.12", "5016@192.168.0.10"): [{'Transfer Raw': '612 KBytes',
                                                       'Jitter': '0.011 ms',
                                                       'Transfer': 626688,
                                                       'Interval': (0.0, 1.0),
                                                       'Bandwidth': 626250,
                                                       'Lost_vs_Total_Datagrams': (0, 426),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5010 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.012 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (1.0, 2.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.017 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (2.0, 3.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.019 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (3.0, 4.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.014 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (4.0, 5.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '612 KBytes',
                                                       'Jitter': '0.017 ms',
                                                       'Transfer': 626688,
                                                       'Interval': (5.0, 6.0),
                                                       'Bandwidth': 626250,
                                                       'Lost_vs_Total_Datagrams': (0, 426),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5010 Kbits/sec'},
                                                      {'Transfer Raw': '3664 KBytes',
                                                       'Jitter': '0.017 ms',
                                                       'Transfer': 3751936,
                                                       'Interval': (0.0, 6.0),
                                                       'Bandwidth': 625000,
                                                       'Lost_vs_Total_Datagrams': (0, 2552),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5000 Kbits/sec'}],
        ("192.168.0.10", "5016@192.168.0.12"): {'report': {'Lost_Datagrams_ratio': '0%',
                                                           'Jitter': '0.017 ms',
                                                           'Transfer': 3751936,
                                                           'Interval': (0.0, 6.0),
                                                           'Transfer Raw': '3664 KBytes',
                                                           'Bandwidth': 625000,
                                                           'Lost_vs_Total_Datagrams': (0, 2552),
                                                           'Bandwidth Raw': '5000 Kbits/sec'}},
        ("192.168.0.12", "5016@192.168.0.10"): {'report': {'Lost_Datagrams_ratio': '0%',
                                                           'Jitter': '0.017 ms',
                                                           'Transfer': 3751936,
                                                           'Interval': (0.0, 6.0),
                                                           'Transfer Raw': '3664 KBytes',
                                                           'Bandwidth': 625000,
                                                           'Lost_vs_Total_Datagrams': (0, 2552),
                                                           'Bandwidth Raw': '5000 Kbits/sec'}}},
    'INFO': ['Server listening on UDP port 5016', 'Receiving 1470 byte datagrams',
             'UDP buffer size: 1024 KByte (default)',
             'Client connecting to 192.168.0.12, UDP port 5016',
             'Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)',
             'UDP buffer size: 1024 KByte (default)',
             '[  4] Sent 2552 datagrams']}


COMMAND_OUTPUT_bidirectional_udp_server = """
xyz@debian:~$ iperf -s -u -p 5016 -f k -i 1.0
------------------------------------------------------------
Server listening on UDP port 5016
Receiving 1470 byte datagrams
UDP buffer size: 1024 KByte (default)
------------------------------------------------------------
[  3] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 56262
------------------------------------------------------------
Client connecting to 192.168.0.10, UDP port 5016
Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)
UDP buffer size: 1024 KByte (default)
------------------------------------------------------------
[  5] local 192.168.0.12 port 47384 connected with 192.168.0.10 port 5016
[ ID] Interval       Transfer     Bandwidth        Jitter   Lost/Total Datagrams
[  3]  0.0- 1.0 sec   612 KBytes  5010 Kbits/sec   0.022 ms    0/  426 (0%)
[  5]  0.0- 1.0 sec   613 KBytes  5022 Kbits/sec
[  3]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec   0.016 ms    0/  425 (0%)
[  5]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec
[  3]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec   0.021 ms    0/  425 (0%)
[  5]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec
[  3]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec   0.009 ms    0/  425 (0%)
[  5]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec
[  3]  4.0- 5.0 sec   612 KBytes  5010 Kbits/sec   0.014 ms    0/  426 (0%)
[  5]  4.0- 5.0 sec   610 KBytes  4998 Kbits/sec
[  3]  5.0- 6.0 sec   610 KBytes  4998 Kbits/sec   0.018 ms    0/  425 (0%)
[  3]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.018 ms    0/ 2552 (0%)
[  5]  5.0- 6.0 sec   610 KBytes  4998 Kbits/sec
[  5]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec
[  5] Sent 2552 datagrams
[  5] Server Report:
[  5]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.017 ms    0/ 2552 (0%)
xyz@debian:~$"""


COMMAND_KWARGS_bidirectional_udp_server = {
    'options': '-s -u -p 5016 -f k -i 1.0'
}


COMMAND_RESULT_bidirectional_udp_server = {
    'CONNECTIONS': {
        ("47384@192.168.0.12", "5016@192.168.0.10"): [{'Transfer': 627712,
                                                       'Bandwidth': 627750,
                                                       'Transfer Raw': '613 KBytes',
                                                       'Bandwidth Raw': '5022 Kbits/sec',
                                                       'Interval': (0.0, 1.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (1.0, 2.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (2.0, 3.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (3.0, 4.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (4.0, 5.0)},
                                                      {'Transfer': 624640,
                                                       'Bandwidth': 624750,
                                                       'Transfer Raw': '610 KBytes',
                                                       'Bandwidth Raw': '4998 Kbits/sec',
                                                       'Interval': (5.0, 6.0)},
                                                      {'Transfer': 3751936,
                                                       'Bandwidth': 625000,
                                                       'Transfer Raw': '3664 KBytes',
                                                       'Bandwidth Raw': '5000 Kbits/sec',
                                                       'Interval': (0.0, 6.0)},
                                                      {'Transfer Raw': '3664 KBytes',
                                                       'Jitter': '0.017 ms',
                                                       'Transfer': 3751936,
                                                       'Interval': (0.0, 6.0),
                                                       'Bandwidth': 625000,
                                                       'Lost_vs_Total_Datagrams': (0, 2552),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5000 Kbits/sec'}],
        ("56262@192.168.0.10", "5016@192.168.0.12"): [{'Transfer Raw': '612 KBytes',
                                                       'Jitter': '0.022 ms',
                                                       'Transfer': 626688,
                                                       'Interval': (0.0, 1.0),
                                                       'Bandwidth': 626250,
                                                       'Lost_vs_Total_Datagrams': (0, 426),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5010 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.016 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (1.0, 2.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.021 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (2.0, 3.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.009 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (3.0, 4.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '612 KBytes',
                                                       'Jitter': '0.014 ms',
                                                       'Transfer': 626688,
                                                       'Interval': (4.0, 5.0),
                                                       'Bandwidth': 626250,
                                                       'Lost_vs_Total_Datagrams': (0, 426),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5010 Kbits/sec'},
                                                      {'Transfer Raw': '610 KBytes',
                                                       'Jitter': '0.018 ms',
                                                       'Transfer': 624640,
                                                       'Interval': (5.0, 6.0),
                                                       'Bandwidth': 624750,
                                                       'Lost_vs_Total_Datagrams': (0, 425),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '4998 Kbits/sec'},
                                                      {'Transfer Raw': '3664 KBytes',
                                                       'Jitter': '0.018 ms',
                                                       'Transfer': 3751936,
                                                       'Interval': (0.0, 6.0),
                                                       'Bandwidth': 625000,
                                                       'Lost_vs_Total_Datagrams': (0, 2552),
                                                       'Lost_Datagrams_ratio': '0%',
                                                       'Bandwidth Raw': '5000 Kbits/sec'}],
        ("192.168.0.12", "5016@192.168.0.10"): {'report': {'Lost_Datagrams_ratio': u'0%',
                                                           'Jitter': '0.017 ms',
                                                           'Transfer': 3751936,
                                                           'Interval': (0.0, 6.0),
                                                           'Transfer Raw': '3664 KBytes',
                                                           'Bandwidth': 625000,
                                                           'Lost_vs_Total_Datagrams': (0, 2552),
                                                           'Bandwidth Raw': '5000 Kbits/sec'}},
        ("192.168.0.10", "5016@192.168.0.12"): {'report': {'Lost_Datagrams_ratio': '0%',
                                                           'Jitter': '0.018 ms',
                                                           'Transfer': 3751936,
                                                           'Interval': (0.0, 6.0),
                                                           'Transfer Raw': '3664 KBytes',
                                                           'Bandwidth': 625000,
                                                           'Lost_vs_Total_Datagrams': (0, 2552),
                                                           'Bandwidth Raw': '5000 Kbits/sec'}}},
    'INFO': ['Server listening on UDP port 5016',
             'Receiving 1470 byte datagrams',
             'UDP buffer size: 1024 KByte (default)',
             'Client connecting to 192.168.0.10, UDP port 5016',
             'Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)',
             'UDP buffer size: 1024 KByte (default)',
             '[  5] Sent 2552 datagrams']}


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
        ("57246@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '14.5 Mbits/sec',
                                                         'Bandwidth': 1812500,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '18.5 MBytes',
                                                         'Transfer': 19398656}],
        ("57247@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '14.1 Mbits/sec',
                                                         'Bandwidth': 1762500,
                                                         'Interval': (0.0, 10.8),
                                                         'Transfer Raw': '18.1 MBytes',
                                                         'Transfer': 18979225}],
        ("57248@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.9 Mbits/sec',
                                                         'Bandwidth': 1737500,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '17.6 MBytes',
                                                         'Transfer': 18454937}],
        ("57249@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.2 Mbits/sec',
                                                         'Bandwidth': 1650000,
                                                         'Interval': (0.0, 10.8),
                                                         'Transfer Raw': '17.0 MBytes',
                                                         'Transfer': 17825792}],
        ("57250@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '14.3 Mbits/sec',
                                                         'Bandwidth': 1787500,
                                                         'Interval': (0.0, 10.8),
                                                         'Transfer Raw': '18.4 MBytes',
                                                         'Transfer': 19293798}],
        ("57251@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                         'Bandwidth': 1637500,
                                                         'Interval': (0.0, 10.6),
                                                         'Transfer Raw': '16.6 MBytes',
                                                         'Transfer': 17406361}],
        ("57252@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                         'Bandwidth': 1625000,
                                                         'Interval': (0.0, 10.8),
                                                         'Transfer Raw': '16.8 MBytes',
                                                         'Transfer': 17616076}],
        ("57253@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                         'Bandwidth': 1637500,
                                                         'Interval': (0.0, 10.8),
                                                         'Transfer Raw': '16.8 MBytes',
                                                         'Transfer': 17616076}],
        ("57254@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '14.0 Mbits/sec',
                                                         'Bandwidth': 1750000,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '18.0 MBytes',
                                                         'Transfer': 18874368}],
        ("57255@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.7 Mbits/sec',
                                                         'Bandwidth': 1712500,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '17.5 MBytes',
                                                         'Transfer': 18350080}],
        ("57256@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.9 Mbits/sec',
                                                         'Bandwidth': 1737500,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '17.8 MBytes',
                                                         'Transfer': 18664652}],
        ("57257@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '14.1 Mbits/sec',
                                                         'Bandwidth': 1762500,
                                                         'Interval': (0.0, 10.8),
                                                         'Transfer Raw': '18.2 MBytes',
                                                         'Transfer': 19084083}],
        ("57258@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.8 Mbits/sec',
                                                         'Bandwidth': 1725000,
                                                         'Interval': (0.0, 10.8),
                                                         'Transfer Raw': '17.8 MBytes',
                                                         'Transfer': 18664652}],
        ("57259@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                         'Bandwidth': 1637500,
                                                         'Interval': (0.0, 10.6),
                                                         'Transfer Raw': '16.6 MBytes',
                                                         'Transfer': 17406361}],
        ("57260@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.1 Mbits/sec',
                                                         'Bandwidth': 1637500,
                                                         'Interval': (0.0, 10.6),
                                                         'Transfer Raw': '16.5 MBytes',
                                                         'Transfer': 17301504}],
        ("57261@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                         'Bandwidth': 1625000,
                                                         'Interval': (0.0, 10.6),
                                                         'Transfer Raw': '16.5 MBytes',
                                                         'Transfer': 17301504}],
        ("57262@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '12.9 Mbits/sec',
                                                         'Bandwidth': 1612500,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '16.5 MBytes',
                                                         'Transfer': 17301504}],
        ("57263@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                         'Bandwidth': 1625000,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '16.6 MBytes',
                                                         'Transfer': 17406361}],
        ("57264@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '12.3 Mbits/sec',
                                                         'Bandwidth': 1537500,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '15.6 MBytes',
                                                         'Transfer': 16357785}],
        ("57265@192.168.0.102", "5001@192.168.0.100"): [{'Bandwidth Raw': '13.0 Mbits/sec',
                                                         'Bandwidth': 1625000,
                                                         'Interval': (0.0, 10.7),
                                                         'Transfer Raw': '16.6 MBytes',
                                                         'Transfer': 17406361}],
        ("multiport@192.168.0.102", "5001@192.168.0.100"): [{'Transfer': 360710144,
                                                             'Bandwidth': 33250000,
                                                             'Transfer Raw': '344 MBytes',
                                                             'Bandwidth Raw': '266 Mbits/sec',
                                                             'Interval': (0.0, 10.8)}],
        ("192.168.0.102", "5001@192.168.0.100"): {'report': {'Transfer': 360710144,
                                                             'Bandwidth': 33250000,
                                                             'Transfer Raw': '344 MBytes',
                                                             'Bandwidth Raw': '266 Mbits/sec',
                                                             'Interval': (0.0, 10.8)}}},
    'INFO': ['Client connecting to 192.168.0.100, TCP port 5001',
             'TCP window size: 16.0 KByte (default)']}


COMMAND_OUTPUT_multiple_connections_server = """
xyz@debian:~$ iperf -s -p 5016 -f k
------------------------------------------------------------
Server listening on TCP port 5016
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  4] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 42520
[  5] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 42522
[  6] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 42524
[ ID] Interval       Transfer     Bandwidth
[  4]  0.0- 5.0 sec  2398848 KBytes  3926238 Kbits/sec
[  5]  0.0- 5.0 sec  2160256 KBytes  3535024 Kbits/sec
[  6]  0.0- 5.0 sec  2361856 KBytes  3864920 Kbits/sec
[SUM]  0.0- 5.0 sec  6920960 KBytes  11325398 Kbits/sec
xyz@debian:~$"""

COMMAND_KWARGS_multiple_connections_server = {
    'options': '-s -p 5016 -f k'
}

COMMAND_RESULT_multiple_connections_server = {
    'CONNECTIONS': {
        ('42520@192.168.0.10', '5016@192.168.0.12'): [{'Transfer': 2456420352,
                                                       'Bandwidth': 490779750,
                                                       'Transfer Raw': '2398848 KBytes',
                                                       'Bandwidth Raw': '3926238 Kbits/sec',
                                                       'Interval': (0.0, 5.0)}],
        ('42524@192.168.0.10', '5016@192.168.0.12'): [{'Transfer': 2418540544,
                                                       'Bandwidth': 483115000,
                                                       'Transfer Raw': '2361856 KBytes',
                                                       'Bandwidth Raw': '3864920 Kbits/sec',
                                                       'Interval': (0.0, 5.0)}],
        ('42522@192.168.0.10', '5016@192.168.0.12'): [{'Transfer': 2212102144,
                                                       'Bandwidth': 441878000,
                                                       'Transfer Raw': '2160256 KBytes',
                                                       'Bandwidth Raw': '3535024 Kbits/sec',
                                                       'Interval': (0.0, 5.0)}],
        ('multiport@192.168.0.10', '5016@192.168.0.12'): [{'Transfer': 7087063040,
                                                           'Bandwidth': 1415674750,
                                                           'Transfer Raw': '6920960 KBytes',
                                                           'Bandwidth Raw': '11325398 Kbits/sec',
                                                           'Interval': (0.0, 5.0)}],
        ('192.168.0.10', '5016@192.168.0.12'): {'report': {'Transfer': 7087063040,
                                                           'Bandwidth': 1415674750,
                                                           'Transfer Raw': '6920960 KBytes',
                                                           'Bandwidth Raw': '11325398 Kbits/sec',
                                                           'Interval': (0.0, 5.0)}}},
    'INFO': ['Server listening on TCP port 5016',
             'TCP window size: 85.3 KByte (default)']
}

COMMAND_OUTPUT_singlerun_server = """
xyz@debian:~$ iperf -s -p 5001 -f k -i 1.0 -P 1
------------------------------------------------------------
Server listening on TCP port 5001
TCP window size: 85.3 KByte (default)
------------------------------------------------------------
[  4] local 192.168.44.50 port 5001 connected with 192.168.44.100 port 57272
[ ID] Interval       Transfer     Bandwidth
[  4]  0.0- 1.0 sec  232124 KBytes  1901558 Kbits/sec
[  4]  1.0- 2.0 sec  158626 KBytes  1299464 Kbits/sec
[  4]  2.0- 3.0 sec  191597 KBytes  1569562 Kbits/sec
[  4]  3.0- 4.0 sec  243509 KBytes  1994828 Kbits/sec
[  4]  0.0- 4.0 sec  825856 KBytes  1690728 Kbits/sec
[SUM]  0.0- 4.0 sec  1057980 KBytes  2165942 Kbits/sec
xyz@debian:~$"""

COMMAND_KWARGS_singlerun_server = {
    'options': '-s -p 5001 -f k -i 1.0 -P 1'
}

COMMAND_RESULT_singlerun_server = {
    'CONNECTIONS': {
        ('57272@192.168.44.100', '5001@192.168.44.50'): [{'Transfer': 237694976,
                                                          'Bandwidth': 237694750,
                                                          'Transfer Raw': '232124 KBytes',
                                                          'Bandwidth Raw': '1901558 Kbits/sec',
                                                          'Interval': (0.0, 1.0)},
                                                         {'Transfer': 162433024,
                                                          'Bandwidth': 162433000,
                                                          'Transfer Raw': '158626 KBytes',
                                                          'Bandwidth Raw': '1299464 Kbits/sec',
                                                          'Interval': (1.0, 2.0)},
                                                         {'Transfer': 196195328,
                                                          'Bandwidth': 196195250,
                                                          'Transfer Raw': '191597 KBytes',
                                                          'Bandwidth Raw': '1569562 Kbits/sec',
                                                          'Interval': (2.0, 3.0)},
                                                         {'Transfer': 249353216,
                                                          'Bandwidth': 249353500,
                                                          'Transfer Raw': '243509 KBytes',
                                                          'Bandwidth Raw': '1994828 Kbits/sec',
                                                          'Interval': (3.0, 4.0)},
                                                         {'Transfer': 845676544,
                                                          'Bandwidth': 211341000,
                                                          'Transfer Raw': '825856 KBytes',
                                                          'Bandwidth Raw': '1690728 Kbits/sec',
                                                          'Interval': (0.0, 4.0)}],
        ('192.168.44.100', '5001@192.168.44.50'): {'report': {'Transfer': 845676544,
                                                              'Bandwidth': 211341000,
                                                              'Transfer Raw': '825856 KBytes',
                                                              'Bandwidth Raw': '1690728 Kbits/sec',
                                                              'Interval': (0.0, 4.0)}}},
    'INFO': ['Server listening on TCP port 5001',
             'TCP window size: 85.3 KByte (default)']
}


COMMAND_OUTPUT_singlerun_udp_server = """
xyz@debian:~$ iperf -s -u -p 5001 -f k -i 1.0 -P 1
------------------------------------------------------------
Server listening on UDP port 5001
Receiving 1470 byte datagrams
UDP buffer size:  208 KByte (default)
------------------------------------------------------------
[  3] local 192.168.44.50 port 5001 connected with 192.168.44.100 port 42599
[ ID] Interval       Transfer     Bandwidth        Jitter   Lost/Total Datagrams
[  3]  0.0- 1.0 sec   129 KBytes  1058 Kbits/sec   0.033 ms    0/   90 (0%)
[  3]  1.0- 2.0 sec   128 KBytes  1047 Kbits/sec   0.222 ms    0/   89 (0%)
[  3]  2.0- 3.0 sec   128 KBytes  1047 Kbits/sec   0.022 ms    0/   89 (0%)
[  3]  3.0- 4.0 sec   128 KBytes  1047 Kbits/sec   0.028 ms    0/   89 (0%)
[  3]  0.0- 4.0 sec   512 KBytes  1049 Kbits/sec   0.028 ms    0/  357 (0%)
[SUM]  0.0- 4.0 sec   642 KBytes  1313 Kbits/sec   0.033 ms    0/  447 (0%)
xyz@debian:~$"""

COMMAND_KWARGS_singlerun_udp_server = {
    'options': '-s -u -p 5001 -f k -i 1.0 -P 1'
}

COMMAND_RESULT_singlerun_udp_server = {
    'CONNECTIONS': {
        ('42599@192.168.44.100', '5001@192.168.44.50'): [{'Lost_Datagrams_ratio': '0%',
                                                          'Jitter': '0.033 ms',
                                                          'Transfer': 132096,
                                                          'Interval': (0.0, 1.0),
                                                          'Transfer Raw': '129 KBytes',
                                                          'Bandwidth': 132250,
                                                          'Lost_vs_Total_Datagrams': (0, 90),
                                                          'Bandwidth Raw': '1058 Kbits/sec'},
                                                         {'Lost_Datagrams_ratio': '0%',
                                                          'Jitter': '0.222 ms',
                                                          'Transfer': 131072,
                                                          'Interval': (1.0, 2.0),
                                                          'Transfer Raw': '128 KBytes',
                                                          'Bandwidth': 130875,
                                                          'Lost_vs_Total_Datagrams': (0, 89),
                                                          'Bandwidth Raw': '1047 Kbits/sec'},
                                                         {'Lost_Datagrams_ratio': '0%',
                                                          'Jitter': '0.022 ms',
                                                          'Transfer': 131072,
                                                          'Interval': (2.0, 3.0),
                                                          'Transfer Raw': '128 KBytes',
                                                          'Bandwidth': 130875,
                                                          'Lost_vs_Total_Datagrams': (0, 89),
                                                          'Bandwidth Raw': '1047 Kbits/sec'},
                                                         {'Lost_Datagrams_ratio': '0%',
                                                          'Jitter': '0.028 ms',
                                                          'Transfer': 131072,
                                                          'Interval': (3.0, 4.0),
                                                          'Transfer Raw': '128 KBytes',
                                                          'Bandwidth': 130875,
                                                          'Lost_vs_Total_Datagrams': (0, 89),
                                                          'Bandwidth Raw': '1047 Kbits/sec'},
                                                         {'Lost_Datagrams_ratio': '0%',
                                                          'Jitter': '0.028 ms',
                                                          'Transfer': 524288,
                                                          'Interval': (0.0, 4.0),
                                                          'Transfer Raw': '512 KBytes',
                                                          'Bandwidth': 131125,
                                                          'Lost_vs_Total_Datagrams': (0, 357),
                                                          'Bandwidth Raw': '1049 Kbits/sec'}],
        ('192.168.44.100', '5001@192.168.44.50'): {'report': {'Lost_Datagrams_ratio': '0%',
                                                              'Jitter': '0.028 ms',
                                                              'Transfer': 524288,
                                                              'Interval': (0.0, 4.0),
                                                              'Transfer Raw': '512 KBytes',
                                                              'Bandwidth': 131125,
                                                              'Lost_vs_Total_Datagrams': (0, 357),
                                                              'Bandwidth Raw': '1049 Kbits/sec'}}},
    'INFO': ['Server listening on UDP port 5001',
             'Receiving 1470 byte datagrams',
             'UDP buffer size:  208 KByte (default)']
}
