# -*- coding: utf-8 -*-
"""
Iperf3 command module.

It is refactored Iperf2 module adapted to iperf ver. 3.9.
The changes align with the iperf3 documentation available at https://iperf.fr/iperf-doc.php.

Important changes (in comparison to Iperf2) to note:

- Certain options such as -u, -t, and -P are no longer applicable on the server side.
  Although these options are included on the client side,
- Removed dual tests,
- Added several new stats: Retr and Cwnd for TCP; Total Datagrams for UDP.
"""

__author__ = "Kacper Kozik,Marcin Usielski"
__copyright__ = "Copyright (C) 2023-2024, Nokia"
__email__ = "kacper.kozik@nokia.com, marcin.usielski@nokia.com"


import re
from moler.cmd.unix.iperf2 import Iperf2
from moler.exceptions import ParsingDone


class Iperf3(Iperf2):
    """
    Run iperf3 command, return its statistics and report.

    Single line of iperf3 output may look like::

      [ ID]   Interval       Transfer      Bitrate        Jitter   Lost/Total Datagrams
      [904]   0.0- 1.0 sec   1.17 MBytes   9.84 Mbits/sec   1.830 ms    0/ 837   (0%)

    It represents data transfer statistics reported per given interval.
    This line is parsed out and produces statistics record as python dict.
    (examples can be found at bottom of iperf3.py source code)
    Some keys inside dict are normalized to Bytes.
    In such case you will see both: raw and normalized values::

      'Transfer Raw':     '1.17 MBytes',
      'Transfer':         1226833,           # Bytes
      'Bitrate Raw':    '9.84 Mbits/sec',
      'Bitrate':        1230000,           # Bytes/sec

    Iperf statistics are stored under connection name with format
    (client_port@client_IP, server_port@server_IP)
    It represents iperf3 output line (iperf3 server example below) like::

      [  5] local 192.168.0.12 port 5016 connected to 192.168.0.10 port 56262
      ("56262@192.168.0.10", "5016@192.168.0.12"): [<statistics dicts here>]

    Iperf returned value has also additional connection named "report connection".
    It has format
    (client_IP, server_port@server_IP)
    So, for above example you should expect structure like::

      ("192.168.0.10", "5016@192.168.0.12"): {'report': {<report dict here>}}

    """

    def __init__(self, connection, options, prompt=None, newline_chars=None, runner=None):
        """
        Create iperf3 command

        :param connection: moler connection used by iperf3 command
        :param options: iperf3 options (as in iperf3 documentation)
        :param prompt: prompt (regexp) where iperf3 starts from, if None - default prompt regexp used
        :param newline_chars: expected newline characters of iperf3 output
        :param runner: runner used for command
        """
        super(Iperf3, self).__init__(connection=connection,
                                     prompt=prompt,
                                     newline_chars=newline_chars,
                                     runner=runner,
                                     options=options)

    def _validate_options(self, options):
        client_only_options = [
            ("-u", "--udp"),
            ("-t", "--time"),
            ("-P", "--parallel")]

        for short_option, long_option in client_only_options:
            self._raise_option_error(short_option, long_option, options)

        if self._regex_helper.search_compiled(Iperf3._re_port, options):
            port = int(self._regex_helper.group("PORT"))
        else:
            port = 5201
        return port, options

    def _raise_option_error(self, short_option, long_option, options):
        if ((short_option in options) or (long_option in options)) and (
                ("-s" in options) or ("--server" in options)):
            raise AttributeError(
                f"Option ({long_option}) you are trying to set is client only")

    def build_command_string(self):
        cmd = f"iperf3 {str(self.options)}"
        return cmd

    @property
    def parallel_client(self):
        if self.client:
            return ("-P " in self.options) or ("--parallel " in self.options)
        return len(self._connection_dict.keys()) > 1

    def _parse_svr_report_header(self, line):
        # In iperf3 svr report header does not exists
        pass

    # [  5] local 127.0.0.1 port 35108 connected to 127.0.0.1 port 5201
    _r_conn_info = r"(\[\s*\d*\])\s+local\s+(\S+)\s+port\s+(\d+)\s+connected to\s+(\S+)\s+port\s+(\d+)"
    _re_connection_info = re.compile(_r_conn_info)

    def _parse_connection_name_and_id(self, line):
        if self._regex_helper.search_compiled(Iperf3._re_connection_info, line):
            (
                connection_id,
                local_host,
                local_port,
                remote_host,
                remote_port,
            ) = self._regex_helper.groups()
            local = f"{local_port}@{local_host}"
            remote = f"{remote_port}@{remote_host}"
            if self.port == int(remote_port):
                from_client, to_server = local, remote
                client_host = local_host
            else:
                from_client, to_server = remote, local
                client_host = remote_host
            connection = (from_client, to_server)
            connection_dict = {connection_id: connection}
            self._connection_dict.update(connection_dict)
            if client_host not in self._same_host_connections:
                self._same_host_connections[client_host] = [connection]
            else:
                self._same_host_connections[client_host].append(connection)
            raise ParsingDone

    # iperf3 output for: tcp server
    # [ ID] Interval      Transfer      Bitrate

    # iperf3 output for: tcp client
    # [ ID] Interval      Transfer      Bitrate      Retr        Cwnd

    # iperf3 output for: udp server
    # [ ID] Interval      Transfer      Bitrate      Jitter      Lost/Total Datagrams

    # iperf3 output for: udp client
    # [ ID] Interval      Transfer      Bitrate      Total Datagrams

    # for iperf3 versions <= 3.1.7 the Bitrate column was named Bandwidth
    _re_headers = re.compile(r"\[\s+ID\]\s+Interval\s+Transfer\s+(Bitrate|Bandwidth)")

    def _parse_headers(self, line):
        if self._regex_helper.search_compiled(Iperf3._re_headers, line):
            if self.parallel_client:
                client, server = list(self._connection_dict.values())[0]
                # pylint: disable-next=unused-variable
                (
                    client_host,
                    _,
                    _,
                    _,
                ) = self._split_connection_name((client, server))
                connection_id = "[SUM]"
                self._connection_dict[connection_id] = (
                    f"multiport@{client_host}",
                    server,)
            raise ParsingDone

    # tcp server:
    # [ ID] Interval       Transfer     Bitrate
    # [  5] 0.00-1.00 sec  2.56 GBytes  22.0 Gbits/sec

    # tcp client:
    # [ ID] Interval         Transfer     Bitrate         Retr   Cwnd
    # [  5] 0.00-1.00 sec    2.84 GBytes  24.4 Gbits/sec  0      1.37 MBytes

    # tcp client summary:
    # [ ID] Interval         Transfer     Bitrate         Retr
    # [  5] 0.00-5.00 sec    12.5 GBytes  21.4 Gbits/sec  0

    # udp server:
    # [ ID] Interval         Transfer     Bitrate         Jitter     Lost/Total Datagrams
    # [  5] 0.00-1.00 sec    1.03 MBytes  8.63 Mbits/sec  0.017 ms   0/49 (0%)

    # udp client:
    # [ ID] Interval         Transfer     Bitrate         Total Datagrams
    # [  5] 0.00-1.00 sec    624 KBytes   5107 Kbits/sec  29

    _r_id = r"(?P<ID>\[\s*\d*\]|\[SUM\])"
    _r_interval = r"(?P<Interval>[\d\.]+\-\s*[\d\.]+)\s*sec"
    _r_transfer = r"(?P<Transfer>[\d\.]+\s+\w+)"
    _r_bitrate = r"(?P<Bitrate>[\d\.]+\s+\w+/sec)"

    _r_retr = r"(?P<Retr>\d+)"
    _r_cwnd = r"(?P<Cwnd>[\d\.]+\s+\w+)"

    _r_jitter = r"(?P<Jitter>\d+\.\d+\s\w+)"
    _r_datagrams = r"(?P<Lost_vs_Total_Datagrams>\d+/\s*\d+)\s*\((?P<Lost_Datagrams_ratio>[\d\.]+\%)\)"

    _r_total_datagrams = r"(?P<Total_Datagrams>\d+)"

    _r_rec_tcp_svr = fr"{_r_id}\s+{_r_interval}\s+{_r_transfer}\s+{_r_bitrate}"
    _r_rec_tcp_cli = fr"{_r_rec_tcp_svr}\s+{_r_retr}\s+{_r_cwnd}"
    _r_rec_udp_svr = fr"{_r_rec_tcp_svr}\s+{_r_jitter}\s+{_r_datagrams}"
    _r_rec_udp_cli = fr"{_r_rec_tcp_svr}\s+{_r_total_datagrams}"
    _r_rec_tcp_cli_summary = fr"{_r_rec_tcp_svr}\s+{_r_retr}"

    _re_iperf_record_tcp_svr = re.compile(_r_rec_tcp_svr)
    _re_iperf_record_tcp_cli = re.compile(_r_rec_tcp_cli)
    _re_iperf_record_udp_svr = re.compile(_r_rec_udp_svr)
    _re_iperf_record_udp_cli = re.compile(_r_rec_udp_cli)
    _re_iperf_record_tcp_cli_summary = re.compile(_r_rec_tcp_cli_summary)

    def _parse_connection_info(self, line):
        regex_found = self._regex_helper.search_compiled
        if regex_found(Iperf3._re_iperf_record_udp_svr, line) or \
                self.protocol == "udp" and regex_found(
                    Iperf3._re_iperf_record_udp_cli, line) or \
                self.protocol == "tcp" and regex_found(
                    Iperf3._re_iperf_record_tcp_cli, line) or \
                self.protocol == "tcp" and self.client and regex_found(
                    Iperf3._re_iperf_record_tcp_cli_summary, line) or \
                regex_found(Iperf3._re_iperf_record_tcp_svr, line):

            iperf_record = self._regex_helper.groupdict()
            connection_id = iperf_record.pop("ID")
            iperf_record = self._detailed_parse_interval(iperf_record)
            iperf_record = self._detailed_parse_datagrams(iperf_record)
            iperf_record = self._convert_retr_parameter(iperf_record)
            iperf_record = self._convert_datagrams_parameter(iperf_record)

            connection_name = self._connection_dict[connection_id]
            normalized_iperf_record = self._normalize_to_bytes(iperf_record)
            normalized_iperf_record = self._convert_jitter(
                normalized_iperf_record)
            self._update_current_ret(connection_name, normalized_iperf_record)
            self._parse_final_record(connection_name, line)

            raise ParsingDone

    @staticmethod
    def _convert_datagrams_parameter(iperf_record):
        if "Total_Datagrams" in iperf_record:
            iperf_record["Total_Datagrams"] = int(
                iperf_record["Total_Datagrams"])
        return iperf_record

    @staticmethod
    def _convert_retr_parameter(iperf_record):
        if "Retr" in iperf_record:
            iperf_record["Retr"] = int(iperf_record["Retr"])
        return iperf_record

    def _get_last_record_of_interval(self, connection_name, interval):
        last_rec = self.current_ret["CONNECTIONS"][connection_name][-1]
        if last_rec["Interval"] == interval:
            return last_rec
        return None

    # pylint: disable-next=arguments-differ
    def _parse_final_record(self, connection_name, line):
        if self.parallel_client and ("multiport" not in connection_name[0]):
            return  # for parallel we take report / publish stats only from summary records
        last_record = self.current_ret["CONNECTIONS"][connection_name][-1]

        if self._is_final_record(line):
            # pylint: disable-next=unused-variable
            (
                client_host,
                _,
                server_host,
                server_port,
            ) = self._split_connection_name(connection_name)
            from_client, to_server = client_host, f"{server_port}@{server_host}"
            result_connection = (from_client, to_server)
            self.current_ret["CONNECTIONS"][result_connection] = {
                "report": last_record}
            self.notify_subscribers(
                from_client=from_client, to_server=to_server, report=last_record)
        else:
            from_client, to_server = connection_name
            self.notify_subscribers(
                from_client=from_client, to_server=to_server, data_record=last_record)

    _r_option_report = r"(?P<Option>receiver|sender)"
    _r_rec_tcp_svr_report = fr"{_r_rec_tcp_svr}\s+{_r_option_report}"
    _r_rec_tcp_cli_report = fr"{_r_rec_tcp_cli}\s+{_r_option_report}"
    _r_rec_udp_svr_report = fr"{_r_rec_udp_svr}\s+{_r_option_report}"
    _r_rec_udp_cli_report = fr"{_r_rec_udp_cli}\s+{_r_option_report}"
    _r_rec_tcp_cli_summary_report = fr"{_r_rec_tcp_cli_summary}\s+{_r_option_report}"

    _re_iperf_record_tcp_svr_report = re.compile(_r_rec_tcp_svr_report)
    _re_iperf_record_tcp_cli_report = re.compile(_r_rec_tcp_cli_report)
    _re_iperf_record_udp_svr_report = re.compile(_r_rec_udp_svr_report)
    _re_iperf_record_udp_cli_report = re.compile(_r_rec_udp_cli_report)
    _re_iperf_record_tcp_cli_summary_report = re.compile(
        _r_rec_tcp_cli_summary_report)

    # pylint: disable-next=arguments-renamed
    def _is_final_record(self, line):
        regex_found = self._regex_helper.search_compiled

        if regex_found(Iperf3._re_iperf_record_udp_svr_report, line) or \
                self.protocol == "udp" and regex_found(
                    Iperf3._re_iperf_record_udp_cli_report, line) or \
                self.protocol == "tcp" and regex_found(
                    Iperf3._re_iperf_record_tcp_cli_report, line) or \
                self.protocol == "tcp" and self.client and regex_found(
                    Iperf3._re_iperf_record_tcp_cli_summary_report, line) or \
                regex_found(Iperf3._re_iperf_record_tcp_svr_report, line):

            result_option = self._regex_helper.groupdict().pop("Option")

            if self.server and result_option == "receiver":
                return True
            elif self.client and result_option == "sender":
                return True
        else:
            return False

    def _has_all_reports(self):
        if len(self._connection_dict) < 1:
            return False
        result = self.current_ret["CONNECTIONS"]
        connections = list(self._connection_dict.values())
        client_host, _, server_host, _ = self._split_connection_name(
            connections[0])
        return (client_host, f"{self.port}@{server_host}") in result

    # - - - - - - - - - - - - - - - - - - - - - - - - -
    _re_summary_ornament = re.compile(r"(?P<SUM_ORNAMENT>(-\s)+)")
    _re_blank_line = re.compile(r"(?P<BLANK>^\s*$)")

    def _parse_connection_headers(self, line):
        if not self._regex_helper.search_compiled(Iperf3._re_ornaments, line) and \
           not self._regex_helper.search_compiled(Iperf3._re_summary_ornament, line) and \
           not self._regex_helper.search_compiled(Iperf3._re_blank_line, line):
            self.current_ret["INFO"].append(line.strip())
            raise ParsingDone

    def _normalize_to_bytes(self, input_dict):
        new_dict = {}
        for key, raw_value in input_dict.items():
            # iperf MBytes means 1024 * 1024 Bytes - see iperf.fr/iperf-doc.php
            if not isinstance(raw_value, int) and ("Bytes" in raw_value):
                new_dict[f"{key} Raw"] = raw_value
                value_in_bytes, _, _ = self._converter_helper.to_bytes(
                    raw_value)
                new_dict[key] = value_in_bytes
            # iperf Mbits means 1000 * 1000 bits - see iperf.fr/iperf-doc.php
            elif not isinstance(raw_value, int) and ("bits" in raw_value):
                new_dict[f"{key} Raw"] = raw_value
                value_in_bits, _, _ = self._converter_helper.to_bytes(
                    raw_value, binary_multipliers=False)
                value_in_bytes = value_in_bits // 8
                new_dict[key] = value_in_bytes
            else:
                new_dict[key] = raw_value
        return new_dict

    def _convert_jitter(self, input_dict):
        # jitter value in milliseconds
        for key in list(input_dict):
            raw_value = input_dict[key]
            if not isinstance(raw_value, (int, float)) and "ms" in raw_value:
                input_dict[f"{key} Raw"] = raw_value
                value_in_ms, _ = raw_value.split(" ")
                value_in_ms = float(value_in_ms)
                input_dict[key] = value_in_ms
        return input_dict


COMMAND_OUTPUT_basic_client = """
xyz@debian:~$ iperf3 -c 127.0.0.1 -i 1
Connecting to host 127.0.0.1, port 5201
[  5] local 127.0.0.1 port 48058 connected to 127.0.0.1 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  3.16 GBytes  27.2 Gbits/sec    0   1.25 MBytes
[  5]   1.00-2.00   sec  4.17 GBytes  35.8 Gbits/sec    0   1.25 MBytes
[  5]   2.00-3.00   sec  2.40 GBytes  20.6 Gbits/sec    0   1.25 MBytes
[  5]   3.00-4.00   sec  2.40 GBytes  20.6 Gbits/sec    0   3.18 MBytes
[  5]   4.00-5.00   sec  2.36 GBytes  20.2 Gbits/sec    0   3.18 MBytes
[  5]   5.00-6.00   sec  2.40 GBytes  20.6 Gbits/sec    0   3.18 MBytes
[  5]   6.00-7.00   sec  2.41 GBytes  20.7 Gbits/sec    0   3.18 MBytes
[  5]   7.00-8.00   sec  2.37 GBytes  20.4 Gbits/sec    0   4.81 MBytes
[  5]   8.00-9.00   sec  3.89 GBytes  33.4 Gbits/sec    0   4.81 MBytes
[  5]   9.00-10.00  sec  3.56 GBytes  30.6 Gbits/sec    0   4.81 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  29.1 GBytes  25.0 Gbits/sec    0             sender
[  5]   0.00-10.05  sec  29.1 GBytes  24.9 Gbits/sec                  receiver

iperf Done.
xyz@debian:~$"""

COMMAND_KWARGS_basic_client = {"options": "-c 127.0.0.1 -i 1"}

COMMAND_RESULT_basic_client = {
    'CONNECTIONS':
        {('127.0.0.1', '5201@127.0.0.1'): {'report': {'Bitrate': 3125000000,
                                                      'Bitrate Raw': '25.0 Gbits/sec',
                                                      'Interval': (0.0,
                                                                     10.0),
                                                      'Retr': 0,
                                                      'Transfer': 31245887078,
                                                      'Transfer Raw': '29.1 GBytes'}},
         ('48058@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 3400000000,
                                                  'Bitrate Raw': '27.2 Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 MBytes',
                                                  'Interval': (0.0,
                                                               1.0),
                                                  'Retr': 0,
                                                  'Transfer': 3393024163,
                                                  'Transfer Raw': '3.16 GBytes'},
                                                 {'Bitrate': 4475000000,
                                                  'Bitrate Raw': '35.8 Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 MBytes',
                                                  'Interval': (1.0,
                                                               2.0),
                                                  'Retr': 0,
                                                  'Transfer': 4477503406,
                                                  'Transfer Raw': '4.17 GBytes'},
                                                 {'Bitrate': 2575000000,
                                                  'Bitrate Raw': '20.6 Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 MBytes',
                                                  'Interval': (2.0,
                                                               3.0),
                                                  'Retr': 0,
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 GBytes'},
                                                 {'Bitrate': 2575000000,
                                                  'Bitrate Raw': '20.6 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (3.0,
                                                               4.0),
                                                  'Retr': 0,
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 GBytes'},
                                                 {'Bitrate': 2525000000,
                                                  'Bitrate Raw': '20.2 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (4.0,
                                                               5.0),
                                                  'Retr': 0,
                                                  'Transfer': 2534030704,
                                                  'Transfer Raw': '2.36 GBytes'},
                                                 {'Bitrate': 2575000000,
                                                  'Bitrate Raw': '20.6 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (5.0,
                                                               6.0),
                                                  'Retr': 0,
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 GBytes'},
                                                 {'Bitrate': 2587500000,
                                                  'Bitrate Raw': '20.7 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (6.0,
                                                               7.0),
                                                  'Retr': 0,
                                                  'Transfer': 2587717795,
                                                  'Transfer Raw': '2.41 GBytes'},
                                                 {'Bitrate': 2550000000,
                                                  'Bitrate Raw': '20.4 Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 MBytes',
                                                  'Interval': (7.0,
                                                               8.0),
                                                  'Retr': 0,
                                                  'Transfer': 2544768122,
                                                  'Transfer Raw': '2.37 GBytes'},
                                                 {'Bitrate': 4175000000,
                                                  'Bitrate Raw': '33.4 Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 MBytes',
                                                  'Interval': (8.0,
                                                               9.0),
                                                  'Retr': 0,
                                                  'Transfer': 4176855695,
                                                  'Transfer Raw': '3.89 GBytes'},
                                                 {'Bitrate': 3825000000,
                                                  'Bitrate Raw': '30.6 Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 MBytes',
                                                  'Interval': (9.0,
                                                               10.0),
                                                  'Retr': 0,
                                                  'Transfer': 3822520893,
                                                  'Transfer Raw': '3.56 GBytes'},
                                                 {'Bitrate': 3125000000,
                                                  'Bitrate Raw': '25.0 Gbits/sec',
                                                  'Interval': (0.0,
                                                               10.0),
                                                  'Retr': 0,
                                                  'Transfer': 31245887078,
                                                  'Transfer Raw': '29.1 GBytes'},
                                                 {'Bitrate': 3112500000,
                                                  'Bitrate Raw': '24.9 Gbits/sec',
                                                  'Interval': (0.0,
                                                               10.05),
                                                  'Transfer': 31245887078,
                                                  'Transfer Raw': '29.1 GBytes'}]},
    'INFO': ['Connecting to host 127.0.0.1, port 5201',
             'iperf Done.']}


COMMAND_OUTPUT_basic_client_bytes_bits_convert = """
xyz@debian:~$ iperf3 -c 127.0.0.1 -i 1
Connecting to host 127.0.0.1, port 5201
[  5] local 127.0.0.1 port 48058 connected to 127.0.0.1 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  3.16 GBytes  27.2 Gbits/sec    0   1.25 MBytes
[  5]   1.00-2.00   sec  4.17 GBytes  35.8 Gbits/sec    0   1.25 MBytes
[  5]   2.00-3.00   sec  2.40 GBytes  20.6 Gbits/sec    0   1.25 MBytes
[  5]   3.00-4.00   sec  2.40 GBytes  20.6 Gbits/sec    0   3.18 MBytes
[  5]   4.00-5.00   sec  2.36 GBytes  20.2 Gbits/sec    0   3.18 MBytes
[  5]   5.00-6.00   sec  2.40 GBytes  20.6 Gbits/sec    0   3.18 MBytes
[  5]   6.00-7.00   sec  2.41 GBytes  20.7 Gbits/sec    0   3.18 MBytes
[  5]   7.00-8.00   sec  2.37 GBytes  20.4 Gbits/sec    0   4.81 MBytes
[  5]   8.00-9.00   sec  3.89 GBytes  33.4 Gbits/sec    0   4.81 MBytes
[  5]   9.00-10.00  sec  3.56 GBytes  30.6 Gbits/sec    0   4.81 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  29.1 GBytes  25.0 Gbits/sec    0             sender
[  5]   0.00-10.05  sec  0.00 Bytes   0.00 bits/sec                   receiver

iperf Done.
xyz@debian:~$"""

COMMAND_KWARGS_basic_client_bytes_bits_convert = {
    "options": "-c 127.0.0.1 -i 1"}

COMMAND_RESULT_basic_client_bytes_bits_convert = {
    'CONNECTIONS':
        {('127.0.0.1', '5201@127.0.0.1'): {'report': {'Bitrate': 3125000000,
                                                      'Bitrate Raw': '25.0 Gbits/sec',
                                                      'Interval': (0.0,
                                                                     10.0),
                                                      'Retr': 0,
                                                      'Transfer': 31245887078,
                                                      'Transfer Raw': '29.1 GBytes'}},
         ('48058@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 3400000000,
                                                  'Bitrate Raw': '27.2 Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 MBytes',
                                                  'Interval': (0.0,
                                                               1.0),
                                                  'Retr': 0,
                                                  'Transfer': 3393024163,
                                                  'Transfer Raw': '3.16 GBytes'},
                                                 {'Bitrate': 4475000000,
                                                  'Bitrate Raw': '35.8 Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 MBytes',
                                                  'Interval': (1.0,
                                                               2.0),
                                                  'Retr': 0,
                                                  'Transfer': 4477503406,
                                                  'Transfer Raw': '4.17 GBytes'},
                                                 {'Bitrate': 2575000000,
                                                  'Bitrate Raw': '20.6 Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 MBytes',
                                                  'Interval': (2.0,
                                                               3.0),
                                                  'Retr': 0,
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 GBytes'},
                                                 {'Bitrate': 2575000000,
                                                  'Bitrate Raw': '20.6 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (3.0,
                                                               4.0),
                                                  'Retr': 0,
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 GBytes'},
                                                 {'Bitrate': 2525000000,
                                                  'Bitrate Raw': '20.2 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (4.0,
                                                               5.0),
                                                  'Retr': 0,
                                                  'Transfer': 2534030704,
                                                  'Transfer Raw': '2.36 GBytes'},
                                                 {'Bitrate': 2575000000,
                                                  'Bitrate Raw': '20.6 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (5.0,
                                                               6.0),
                                                  'Retr': 0,
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 GBytes'},
                                                 {'Bitrate': 2587500000,
                                                  'Bitrate Raw': '20.7 Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 MBytes',
                                                  'Interval': (6.0,
                                                               7.0),
                                                  'Retr': 0,
                                                  'Transfer': 2587717795,
                                                  'Transfer Raw': '2.41 GBytes'},
                                                 {'Bitrate': 2550000000,
                                                  'Bitrate Raw': '20.4 Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 MBytes',
                                                  'Interval': (7.0,
                                                               8.0),
                                                  'Retr': 0,
                                                  'Transfer': 2544768122,
                                                  'Transfer Raw': '2.37 GBytes'},
                                                 {'Bitrate': 4175000000,
                                                  'Bitrate Raw': '33.4 Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 MBytes',
                                                  'Interval': (8.0,
                                                               9.0),
                                                  'Retr': 0,
                                                  'Transfer': 4176855695,
                                                  'Transfer Raw': '3.89 GBytes'},
                                                 {'Bitrate': 3825000000,
                                                  'Bitrate Raw': '30.6 Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 MBytes',
                                                  'Interval': (9.0,
                                                               10.0),
                                                  'Retr': 0,
                                                  'Transfer': 3822520893,
                                                  'Transfer Raw': '3.56 GBytes'},
                                                 {'Bitrate': 3125000000,
                                                  'Bitrate Raw': '25.0 Gbits/sec',
                                                  'Interval': (0.0,
                                                               10.0),
                                                  'Retr': 0,
                                                  'Transfer': 31245887078,
                                                  'Transfer Raw': '29.1 GBytes'},
                                                 {'Bitrate': 0,
                                                  'Bitrate Raw': '0.00 bits/sec',
                                                  'Interval': (0.0,
                                                               10.05),
                                                  'Transfer': 0,
                                                  'Transfer Raw': '0.00 Bytes'}]},
    'INFO': ['Connecting to host 127.0.0.1, port 5201',
             'iperf Done.']}


COMMAND_OUTPUT_basic_server = """
xyz@debian:~$ iperf3 -s -i 1
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------
Accepted connection from 127.0.0.1, port 40530
[  5] local 127.0.0.1 port 5201 connected to 127.0.0.1 port 34761
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-1.00   sec   129 KBytes  1.06 Mbits/sec  0.015 ms  0/6 (0%)
[  5]   1.00-2.00   sec   129 KBytes  1.06 Mbits/sec  0.016 ms  0/6 (0%)
[  5]   2.00-3.00   sec   129 KBytes  1.06 Mbits/sec  0.019 ms  0/6 (0%)
[  5]   3.00-4.00   sec   129 KBytes  1.06 Mbits/sec  0.028 ms  0/6 (0%)
[  5]   4.00-5.00   sec   129 KBytes  1.06 Mbits/sec  0.024 ms  0/6 (0%)
[  5]   5.00-6.00   sec   129 KBytes  1.06 Mbits/sec  0.032 ms  0/6 (0%)
[  5]   6.00-7.00   sec   129 KBytes  1.06 Mbits/sec  0.027 ms  0/6 (0%)
[  5]   7.00-8.00   sec   129 KBytes  1.06 Mbits/sec  0.022 ms  0/6 (0%)
[  5]   8.00-9.00   sec   129 KBytes  1.06 Mbits/sec  0.022 ms  0/6 (0%)
[  5]   9.00-10.00  sec   129 KBytes  1.06 Mbits/sec  0.022 ms  0/6 (0%)
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-10.04  sec  1.26 MBytes  1.05 Mbits/sec  0.022 ms  0/60 (0%)  receiver
-----------------------------------------------------------
Server listening on 5201
-----------------------------------------------------------
xyz@debian:~$"""

COMMAND_KWARGS_basic_server = {"options": "-s -i 1"}

COMMAND_RESULT_basic_server = {
    'CONNECTIONS': {
        ('127.0.0.1', '5201@127.0.0.1'): {'report': {'Bitrate': 131250,
                                                     'Bitrate Raw': '1.05 Mbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Jitter': 0.022,
                                                     'Jitter Raw': '0.022 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 60),
                                                     'Transfer': 1321205,
                                                     'Transfer Raw': '1.26 MBytes'}},
        ('34761@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Jitter': 0.015,
                                                 'Jitter Raw': '0.015 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Jitter': 0.016,
                                                 'Jitter Raw': '0.016 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Jitter': 0.019,
                                                 'Jitter Raw': '0.019 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Jitter': 0.028,
                                                 'Jitter Raw': '0.028 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Jitter': 0.024,
                                                 'Jitter Raw': '0.024 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Jitter': 0.032,
                                                 'Jitter Raw': '0.032 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Jitter': 0.027,
                                                 'Jitter Raw': '0.027 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Jitter': 0.022,
                                                 'Jitter Raw': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Jitter': 0.022,
                                                 'Jitter Raw': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 Mbits/sec',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Jitter': 0.022,
                                                 'Jitter Raw': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 131250,
                                                 'Bitrate Raw': '1.05 Mbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Jitter': 0.022,
                                                 'Jitter Raw': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             60),
                                                 'Transfer': 1321205,
                                                 'Transfer Raw': '1.26 MBytes'}]},
    'INFO': ['Server listening on 5201',
             'Accepted connection from 127.0.0.1, port 40530',
             'Server listening on 5201']}


COMMAND_OUTPUT_tcp_ipv6_server = """
xyz@debian:~$ iperf3 -s -V -p 5901 -i 1.0
iperf 3.6
Linux debian
-----------------------------------------------------------
Server listening on 5901
-----------------------------------------------------------
Time: Wed, 26 Jul 2023 14:07:18 GMT
Accepted connection from 127.0.0.1, port 37974
      Cookie: abcd
      TCP MSS: 0 (default)
[  5] local 127.0.0.1 port 5901 connected to 127.0.0.1 port 37988
Starting Test: protocol: TCP, 1 streams, 131072 byte blocks, omitting 0 seconds, 10 second test, tos 0
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-1.00   sec  2.26 GBytes  19.4 Gbits/sec
[  5]   1.00-2.00   sec  2.49 GBytes  21.4 Gbits/sec
[  5]   2.00-3.00   sec  2.41 GBytes  20.7 Gbits/sec
[  5]   3.00-4.00   sec  2.51 GBytes  21.5 Gbits/sec
[  5]   4.00-5.00   sec  2.99 GBytes  25.7 Gbits/sec
[  5]   5.00-6.00   sec  2.52 GBytes  21.6 Gbits/sec
[  5]   6.00-7.00   sec  2.52 GBytes  21.7 Gbits/sec
[  5]   7.00-8.00   sec  2.50 GBytes  21.5 Gbits/sec
[  5]   8.00-9.00   sec  2.54 GBytes  21.9 Gbits/sec
[  5]   9.00-10.00  sec  2.89 GBytes  24.8 Gbits/sec
[  5]  10.00-10.04  sec  71.2 MBytes  14.4 Gbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
Test Complete. Summary Results:
[ ID] Interval           Transfer     Bitrate
[  5] (sender statistics not available)
[  5]   0.00-10.04  sec  25.7 GBytes  22.0 Gbits/sec                  receiver
CPU Utilization: local/receiver 59.8% (3.9%u/55.9%s), remote/sender 0.0% (0.0%u/0.0%s)
rcv_tcp_congestion cubic
iperf 3.6
Linux debian
-----------------------------------------------------------
Server listening on 5901
-----------------------------------------------------------
xyz@debian:~$"""


COMMAND_KWARGS_tcp_ipv6_server = {"options": "-s -V -p 5901 -i 1.0"}

COMMAND_RESULT_tcp_ipv6_server = {
    'CONNECTIONS': {
        ('127.0.0.1', '5901@127.0.0.1'): {'report': {'Bitrate': 2750000000,
                                                     'Bitrate Raw': '22.0 Gbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Transfer': 27595164876,
                                                     'Transfer Raw': '25.7 GBytes'}},
        ('37988@127.0.0.1', '5901@127.0.0.1'): [{'Bitrate': 2425000000,
                                                 'Bitrate Raw': '19.4 Gbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Transfer': 2426656522,
                                                 'Transfer Raw': '2.26 GBytes'},
                                                {'Bitrate': 2675000000,
                                                 'Bitrate Raw': '21.4 Gbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Transfer': 2673617141,
                                                 'Transfer Raw': '2.49 GBytes'},
                                                {'Bitrate': 2587500000,
                                                 'Bitrate Raw': '20.7 Gbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Transfer': 2587717795,
                                                 'Transfer Raw': '2.41 GBytes'},
                                                {'Bitrate': 2687500000,
                                                 'Bitrate Raw': '21.5 Gbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Transfer': 2695091978,
                                                 'Transfer Raw': '2.51 GBytes'},
                                                {'Bitrate': 3212500000,
                                                 'Bitrate Raw': '25.7 Gbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Transfer': 3210488053,
                                                 'Transfer Raw': '2.99 GBytes'},
                                                {'Bitrate': 2700000000,
                                                 'Bitrate Raw': '21.6 Gbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Transfer': 2705829396,
                                                 'Transfer Raw': '2.52 GBytes'},
                                                {'Bitrate': 2712500000,
                                                 'Bitrate Raw': '21.7 Gbits/sec',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Transfer': 2705829396,
                                                 'Transfer Raw': '2.52 GBytes'},
                                                {'Bitrate': 2687500000,
                                                 'Bitrate Raw': '21.5 Gbits/sec',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Transfer': 2684354560,
                                                 'Transfer Raw': '2.50 GBytes'},
                                                {'Bitrate': 2737500000,
                                                 'Bitrate Raw': '21.9 Gbits/sec',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Transfer': 2727304232,
                                                 'Transfer Raw': '2.54 GBytes'},
                                                {'Bitrate': 3100000000,
                                                 'Bitrate Raw': '24.8 Gbits/sec',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Transfer': 3103113871,
                                                 'Transfer Raw': '2.89 GBytes'},
                                                {'Bitrate': 1800000000,
                                                 'Bitrate Raw': '14.4 Gbits/sec',
                                                 'Interval': (10.0,
                                                              10.04),
                                                 'Transfer': 74658611,
                                                 'Transfer Raw': '71.2 MBytes'},
                                                {'Bitrate': 2750000000,
                                                 'Bitrate Raw': '22.0 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 27595164876,
                                                 'Transfer Raw': '25.7 GBytes'}]},
    'INFO': ['iperf 3.6',
             'Linux debian',
             'Server listening on 5901',
             'Time: Wed, 26 Jul 2023 14:07:18 GMT',
             'Accepted connection from 127.0.0.1, port 37974',
             'Cookie: abcd',
             'TCP MSS: 0 (default)',
             'Starting Test: protocol: TCP, 1 streams, 131072 byte blocks, omitting 0 seconds, 10 second test, tos 0',
             'Test Complete. Summary Results:',
             '[  5] (sender statistics not available)',
             'CPU Utilization: local/receiver 59.8% (3.9%u/55.9%s), remote/sender 0.0% (0.0%u/0.0%s)',
             'rcv_tcp_congestion cubic',
             'iperf 3.6',
             'Linux debian',
             'Server listening on 5901']}


COMMAND_OUTPUT_tcp_ipv6_client = """
xyz@debian:~$ iperf3 -c fd00::1:0 -V -p 5901 -i 1
iperf 3.6
Linux debian
Control connection MSS 22016
Time: Thu, 27 Jul 2023 07:33:51 GMT
Connecting to host fd00::1:0, port 5901
      Cookie: abcd
      TCP MSS: 22016 (default)
[  5] local fd00::2:0 port 49597 connected to fd00::1:0 port 5901
Starting Test: protocol: TCP, 1 streams, 131072 byte blocks, omitting 0 seconds, 10 second test, tos 0
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  3.75 GBytes  32.2 Gbits/sec    0   1.19 MBytes
[  5]   1.00-2.00   sec  2.63 GBytes  22.6 Gbits/sec    0   1.19 MBytes
[  5]   2.00-3.00   sec  2.76 GBytes  23.7 Gbits/sec    0   1.37 MBytes
[  5]   3.00-4.00   sec  2.51 GBytes  21.5 Gbits/sec    0   1.37 MBytes
[  5]   4.00-5.00   sec  2.53 GBytes  21.8 Gbits/sec    0   1.37 MBytes
[  5]   5.00-6.00   sec  2.46 GBytes  21.1 Gbits/sec    0   1.37 MBytes
[  5]   6.00-7.00   sec  2.48 GBytes  21.3 Gbits/sec    0   1.37 MBytes
[  5]   7.00-8.00   sec  3.48 GBytes  29.9 Gbits/sec    0   1.37 MBytes
[  5]   8.00-9.00   sec  2.76 GBytes  23.7 Gbits/sec    0   2.06 MBytes
[  5]   9.00-10.00  sec  4.71 GBytes  40.5 Gbits/sec    0   2.06 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
Test Complete. Summary Results:
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  30.1 GBytes  25.8 Gbits/sec    0             sender
[  5]   0.00-10.04  sec  30.1 GBytes  25.7 Gbits/sec                  receiver
CPU Utilization: local/sender 97.2% (1.9%u/95.3%s), remote/receiver 64.2% (3.4%u/60.8%s)
snd_tcp_congestion cubic
rcv_tcp_congestion cubic

iperf Done.
xyz@debian:~$"""


COMMAND_KWARGS_tcp_ipv6_client = {
    "options": "-c fd00::1:0 -V -p 5901 -i 1"}

COMMAND_RESULT_tcp_ipv6_client = {
    'CONNECTIONS': {
        ('fd00::2:0', '5901@fd00::1:0'): {'report': {'Bitrate': 3225000000,
                                                     'Bitrate Raw': '25.8 Gbits/sec',
                                                     'Interval': (0.0,
                                                                  10.0),
                                                     'Retr': 0,
                                                     'Transfer': 32319628902,
                                                     'Transfer Raw': '30.1 GBytes'}},
        ('49597@fd00::2:0', '5901@fd00::1:0'): [{'Bitrate': 4025000000,
                                                 'Bitrate Raw': '32.2 Gbits/sec',
                                                 'Cwnd': 1247805,
                                                 'Cwnd Raw': '1.19 MBytes',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Retr': 0,
                                                 'Transfer': 4026531840,
                                                 'Transfer Raw': '3.75 GBytes'},
                                                {'Bitrate': 2825000000,
                                                 'Bitrate Raw': '22.6 Gbits/sec',
                                                 'Cwnd': 1247805,
                                                 'Cwnd Raw': '1.19 MBytes',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Retr': 0,
                                                 'Transfer': 2823940997,
                                                 'Transfer Raw': '2.63 GBytes'},
                                                {'Bitrate': 2962500000,
                                                 'Bitrate Raw': '23.7 Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 MBytes',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Retr': 0,
                                                 'Transfer': 2963527434,
                                                 'Transfer Raw': '2.76 GBytes'},
                                                {'Bitrate': 2687500000,
                                                 'Bitrate Raw': '21.5 Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 MBytes',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Retr': 0,
                                                 'Transfer': 2695091978,
                                                 'Transfer Raw': '2.51 GBytes'},
                                                {'Bitrate': 2725000000,
                                                 'Bitrate Raw': '21.8 Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 MBytes',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Retr': 0,
                                                 'Transfer': 2716566814,
                                                 'Transfer Raw': '2.53 GBytes'},
                                                {'Bitrate': 2637500000,
                                                 'Bitrate Raw': '21.1 Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 MBytes',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Retr': 0,
                                                 'Transfer': 2641404887,
                                                 'Transfer Raw': '2.46 GBytes'},
                                                {'Bitrate': 2662500000,
                                                 'Bitrate Raw': '21.3 Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 MBytes',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Retr': 0,
                                                 'Transfer': 2662879723,
                                                 'Transfer Raw': '2.48 GBytes'},
                                                {'Bitrate': 3737500000,
                                                 'Bitrate Raw': '29.9 Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 MBytes',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Retr': 0,
                                                 'Transfer': 3736621547,
                                                 'Transfer Raw': '3.48 GBytes'},
                                                {'Bitrate': 2962500000,
                                                 'Bitrate Raw': '23.7 Gbits/sec',
                                                 'Cwnd': 2160066,
                                                 'Cwnd Raw': '2.06 MBytes',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Retr': 0,
                                                 'Transfer': 2963527434,
                                                 'Transfer Raw': '2.76 GBytes'},
                                                {'Bitrate': 5062500000,
                                                 'Bitrate Raw': '40.5 Gbits/sec',
                                                 'Cwnd': 2160066,
                                                 'Cwnd Raw': '2.06 MBytes',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 5057323991,
                                                 'Transfer Raw': '4.71 GBytes'},
                                                {'Bitrate': 3225000000,
                                                 'Bitrate Raw': '25.8 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 32319628902,
                                                 'Transfer Raw': '30.1 GBytes'},
                                                {'Bitrate': 3212500000,
                                                 'Bitrate Raw': '25.7 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 32319628902,
                                                 'Transfer Raw': '30.1 GBytes'}]},
    'INFO': ['iperf 3.6',
             'Linux debian',
             'Control connection MSS 22016',
             'Time: Thu, 27 Jul 2023 07:33:51 GMT',
             'Connecting to host fd00::1:0, port 5901',
             'Cookie: abcd',
             'TCP MSS: 22016 (default)',
             'Starting Test: protocol: TCP, 1 streams, 131072 byte blocks, omitting 0 seconds, 10 second test, tos 0',
             'Test Complete. Summary Results:',
             'CPU Utilization: local/sender 97.2% (1.9%u/95.3%s), remote/receiver 64.2% (3.4%u/60.8%s)',
             'snd_tcp_congestion cubic',
             'rcv_tcp_congestion cubic',
             'iperf Done.']}


COMMAND_OUTPUT_udp_client_params = """
abc@debian:~$ iperf3 -c 127.0.0.1 -u -p 5017 -f k -i 1.0 -t 6.0 -b 5000.0k
Connecting to host 127.0.0.1, port 5017
[  5] local 127.0.0.1 port 55371 connected to 127.0.0.1 port 5017
[ ID] Interval           Transfer     Bitrate         Total Datagrams
[  5]   0.00-1.00   sec   624 KBytes  5107 Kbits/sec  29
[  5]   1.00-2.00   sec   602 KBytes  4932 Kbits/sec  28
[  5]   2.00-3.00   sec   624 KBytes  5108 Kbits/sec  29
[  5]   3.00-4.00   sec   602 KBytes  4932 Kbits/sec  28
[  5]   4.00-5.00   sec   602 KBytes  4932 Kbits/sec  28
[  5]   5.00-6.00   sec   624 KBytes  5108 Kbits/sec  29
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-6.00   sec  3.59 MBytes  5020 Kbits/sec  0.000 ms  0/171 (0%)  sender
[  5]   0.00-6.04   sec  3.59 MBytes  4984 Kbits/sec  0.046 ms  0/171 (0%)  receiver

iperf Done.
abc@debian:~$"""


COMMAND_KWARGS_udp_client_params = {
    "options": "-c 127.0.0.1 -u -p 5017 -f k -i 1.0 -t 6.0 -b 5000.0k"
}


COMMAND_RESULT_udp_client_params = {
    'CONNECTIONS': {
        ('127.0.0.1', '5017@127.0.0.1'): {'report': {'Bitrate': 627500,
                                                     'Bitrate Raw': '5020 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  6.0),
                                                     'Jitter': 0.0,
                                                     'Jitter Raw': '0.000 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 171),
                                                     'Transfer': 3764387,
                                                     'Transfer Raw': '3.59 MBytes'}},
        ('55371@127.0.0.1', '5017@127.0.0.1'): [{'Bitrate': 638375,
                                                 'Bitrate Raw': '5107 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Total_Datagrams': 29,
                                                 'Transfer': 638976,
                                                 'Transfer Raw': '624 KBytes'},
                                                {'Bitrate': 616500,
                                                 'Bitrate Raw': '4932 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Total_Datagrams': 28,
                                                 'Transfer': 616448,
                                                 'Transfer Raw': '602 KBytes'},
                                                {'Bitrate': 638500,
                                                 'Bitrate Raw': '5108 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Total_Datagrams': 29,
                                                 'Transfer': 638976,
                                                 'Transfer Raw': '624 KBytes'},
                                                {'Bitrate': 616500,
                                                 'Bitrate Raw': '4932 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Total_Datagrams': 28,
                                                 'Transfer': 616448,
                                                 'Transfer Raw': '602 KBytes'},
                                                {'Bitrate': 616500,
                                                 'Bitrate Raw': '4932 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Total_Datagrams': 28,
                                                 'Transfer': 616448,
                                                 'Transfer Raw': '602 KBytes'},
                                                {'Bitrate': 638500,
                                                 'Bitrate Raw': '5108 Kbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Total_Datagrams': 29,
                                                 'Transfer': 638976,
                                                 'Transfer Raw': '624 KBytes'},
                                                {'Bitrate': 627500,
                                                 'Bitrate Raw': '5020 Kbits/sec',
                                                 'Interval': (0.0,
                                                              6.0),
                                                 'Jitter': 0.0,
                                                 'Jitter Raw': '0.000 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             171),
                                                 'Transfer': 3764387,
                                                 'Transfer Raw': '3.59 MBytes'},
                                                {'Bitrate': 623000,
                                                 'Bitrate Raw': '4984 Kbits/sec',
                                                 'Interval': (0.0,
                                                              6.04),
                                                 'Jitter': 0.046,
                                                 'Jitter Raw': '0.046 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             171),
                                                 'Transfer': 3764387,
                                                 'Transfer Raw': '3.59 MBytes'}]},
    'INFO': ['Connecting to host 127.0.0.1, port 5017', 'iperf Done.']}


COMMAND_OUTPUT_udp_server_params = """
xyz@debian:~$ iperf3 -s -p 5016 -f k -i 1.0
-----------------------------------------------------------
Server listening on 5016
-----------------------------------------------------------
Accepted connection from 127.0.0.1, port 60294
[  5] local 127.0.0.1 port 5016 connected to 127.0.0.1 port 60306
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-1.00   sec  3.01 GBytes  25846640 Kbits/sec
[  5]   1.00-2.00   sec  2.56 GBytes  21954184 Kbits/sec
[  5]   2.00-3.00   sec  2.56 GBytes  21951897 Kbits/sec
[  5]   3.00-4.00   sec  2.55 GBytes  21925486 Kbits/sec
[  5]   4.00-5.00   sec  2.56 GBytes  22018130 Kbits/sec
[  5]   5.00-6.00   sec  2.58 GBytes  22139685 Kbits/sec
[  5]   6.00-7.00   sec  2.57 GBytes  22113509 Kbits/sec
[  5]   7.00-8.00   sec  2.57 GBytes  22069511 Kbits/sec
[  5]   8.00-9.00   sec  2.57 GBytes  22097527 Kbits/sec
[  5]   9.00-10.00  sec  2.57 GBytes  22035949 Kbits/sec
[  5]  10.00-10.04  sec   109 MBytes  21662383 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-10.04  sec  26.2 GBytes  22412094 Kbits/sec                  receiver
-----------------------------------------------------------
Server listening on 5016
-----------------------------------------------------------
xyz@debian:~$"""


COMMAND_KWARGS_udp_server_params = {"options": "-s -p 5016 -f k -i 1.0"}


COMMAND_RESULT_udp_server_params = {
    'CONNECTIONS': {
        ('127.0.0.1', '5016@127.0.0.1'): {'report': {'Bitrate': 2801511750,
                                                     'Bitrate Raw': '22412094 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Transfer': 28132035788,
                                                     'Transfer Raw': '26.2 GBytes'}},
        ('60306@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 3230830000,
                                                 'Bitrate Raw': '25846640 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Transfer': 3231962890,
                                                 'Transfer Raw': '3.01 GBytes'},
                                                {'Bitrate': 2744273000,
                                                 'Bitrate Raw': '21954184 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Transfer': 2748779069,
                                                 'Transfer Raw': '2.56 GBytes'},
                                                {'Bitrate': 2743987125,
                                                 'Bitrate Raw': '21951897 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Transfer': 2748779069,
                                                 'Transfer Raw': '2.56 GBytes'},
                                                {'Bitrate': 2740685750,
                                                 'Bitrate Raw': '21925486 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Transfer': 2738041651,
                                                 'Transfer Raw': '2.55 GBytes'},
                                                {'Bitrate': 2752266250,
                                                 'Bitrate Raw': '22018130 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Transfer': 2748779069,
                                                 'Transfer Raw': '2.56 GBytes'},
                                                {'Bitrate': 2767460625,
                                                 'Bitrate Raw': '22139685 Kbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Transfer': 2770253905,
                                                 'Transfer Raw': '2.58 GBytes'},
                                                {'Bitrate': 2764188625,
                                                 'Bitrate Raw': '22113509 Kbits/sec',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Transfer': 2759516487,
                                                 'Transfer Raw': '2.57 GBytes'},
                                                {'Bitrate': 2758688875,
                                                 'Bitrate Raw': '22069511 Kbits/sec',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Transfer': 2759516487,
                                                 'Transfer Raw': '2.57 GBytes'},
                                                {'Bitrate': 2762190875,
                                                 'Bitrate Raw': '22097527 Kbits/sec',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Transfer': 2759516487,
                                                 'Transfer Raw': '2.57 GBytes'},
                                                {'Bitrate': 2754493625,
                                                 'Bitrate Raw': '22035949 Kbits/sec',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Transfer': 2759516487,
                                                 'Transfer Raw': '2.57 GBytes'},
                                                {'Bitrate': 2707797875,
                                                 'Bitrate Raw': '21662383 Kbits/sec',
                                                 'Interval': (10.0,
                                                              10.04),
                                                 'Transfer': 114294784,
                                                 'Transfer Raw': '109 MBytes'},
                                                {'Bitrate': 2801511750,
                                                 'Bitrate Raw': '22412094 Kbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 28132035788,
                                                 'Transfer Raw': '26.2 GBytes'}]},
    'INFO': ['Server listening on 5016',
             'Accepted connection from 127.0.0.1, port 60294',
             'Server listening on 5016']}


COMMAND_OUTPUT_multiple_connections = """
xyz@debian:~$ iperf3 -c 127.0.0.1 -P 3
Connecting to host 127.0.0.1, port 5201
[  5] local 127.0.0.1 port 46026 connected to 127.0.0.1 port 5201
[  7] local 127.0.0.1 port 46036 connected to 127.0.0.1 port 5201
[  9] local 127.0.0.1 port 46052 connected to 127.0.0.1 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  1000 MBytes  8.39 Gbits/sec    0    959 KBytes
[  7]   0.00-1.00   sec  1000 MBytes  8.39 Gbits/sec    0    959 KBytes
[  9]   0.00-1.00   sec  1000 MBytes  8.39 Gbits/sec    0    959 KBytes
[SUM]   0.00-1.00   sec  2.93 GBytes  25.2 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   1.00-2.00   sec   889 MBytes  7.45 Gbits/sec    0    959 KBytes
[  7]   1.00-2.00   sec   889 MBytes  7.45 Gbits/sec    0    959 KBytes
[  9]   1.00-2.00   sec   889 MBytes  7.45 Gbits/sec    0    959 KBytes
[SUM]   1.00-2.00   sec  2.60 GBytes  22.3 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   2.00-3.00   sec   862 MBytes  7.24 Gbits/sec    0    959 KBytes
[  7]   2.00-3.00   sec   862 MBytes  7.24 Gbits/sec    0    959 KBytes
[  9]   2.00-3.00   sec   862 MBytes  7.24 Gbits/sec    0    959 KBytes
[SUM]   2.00-3.00   sec  2.53 GBytes  21.7 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   3.00-4.00   sec   860 MBytes  7.21 Gbits/sec    0    959 KBytes
[  7]   3.00-4.00   sec   860 MBytes  7.21 Gbits/sec    0    959 KBytes
[  9]   3.00-4.00   sec   860 MBytes  7.21 Gbits/sec    0    959 KBytes
[SUM]   3.00-4.00   sec  2.52 GBytes  21.6 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   4.00-5.00   sec   859 MBytes  7.20 Gbits/sec    0    959 KBytes
[  7]   4.00-5.00   sec   859 MBytes  7.20 Gbits/sec    0    959 KBytes
[  9]   4.00-5.00   sec   859 MBytes  7.20 Gbits/sec    0    959 KBytes
[SUM]   4.00-5.00   sec  2.52 GBytes  21.6 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   5.00-6.00   sec   858 MBytes  7.20 Gbits/sec    0    959 KBytes
[  7]   5.00-6.00   sec   858 MBytes  7.20 Gbits/sec    0    959 KBytes
[  9]   5.00-6.00   sec   858 MBytes  7.20 Gbits/sec    0    959 KBytes
[SUM]   5.00-6.00   sec  2.51 GBytes  21.6 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   6.00-7.00   sec   992 MBytes  8.33 Gbits/sec    0    959 KBytes
[  7]   6.00-7.00   sec   992 MBytes  8.33 Gbits/sec    0    959 KBytes
[  9]   6.00-7.00   sec   992 MBytes  8.33 Gbits/sec    0    959 KBytes
[SUM]   6.00-7.00   sec  2.91 GBytes  25.0 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   7.00-8.00   sec   861 MBytes  7.22 Gbits/sec    0    959 KBytes
[  7]   7.00-8.00   sec   861 MBytes  7.22 Gbits/sec    0    959 KBytes
[  9]   7.00-8.00   sec   861 MBytes  7.22 Gbits/sec    0    959 KBytes
[SUM]   7.00-8.00   sec  2.52 GBytes  21.7 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   8.00-9.00   sec   829 MBytes  6.94 Gbits/sec    0    959 KBytes
[  7]   8.00-9.00   sec   829 MBytes  6.94 Gbits/sec    0    959 KBytes
[  9]   8.00-9.00   sec   829 MBytes  6.94 Gbits/sec    0    959 KBytes
[SUM]   8.00-9.00   sec  2.43 GBytes  20.8 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   9.00-10.00  sec   852 MBytes  7.16 Gbits/sec    0    959 KBytes
[  7]   9.00-10.00  sec   852 MBytes  7.16 Gbits/sec    0    959 KBytes
[  9]   9.00-10.00  sec   852 MBytes  7.16 Gbits/sec    0    959 KBytes
[SUM]   9.00-10.00  sec  2.50 GBytes  21.5 Gbits/sec    0
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-10.00  sec  8.65 GBytes  7.43 Gbits/sec    0             sender
[  5]   0.00-10.04  sec  8.65 GBytes  7.41 Gbits/sec                  receiver
[  7]   0.00-10.00  sec  8.65 GBytes  7.43 Gbits/sec    0             sender
[  7]   0.00-10.04  sec  8.65 GBytes  7.41 Gbits/sec                  receiver
[  9]   0.00-10.00  sec  8.65 GBytes  7.43 Gbits/sec    0             sender
[  9]   0.00-10.04  sec  8.65 GBytes  7.41 Gbits/sec                  receiver
[SUM]   0.00-10.00  sec  26.0 GBytes  22.3 Gbits/sec    0             sender
[SUM]   0.00-10.04  sec  26.0 GBytes  22.2 Gbits/sec                  receiver

iperf Done.
xyz@debian:~$"""

COMMAND_KWARGS_multiple_connections = {"options": "-c 127.0.0.1 -P 3"}

COMMAND_RESULT_multiple_connections = {
    'CONNECTIONS': {
        ('127.0.0.1', '5201@127.0.0.1'): {'report': {'Bitrate': 2787500000,
                                                     'Bitrate Raw': '22.3 Gbits/sec',
                                                     'Interval': (0.0,
                                                                  10.0),
                                                     'Retr': 0,
                                                     'Transfer': 27917287424,
                                                     'Transfer Raw': '26.0 GBytes'}},
        ('46026@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 1048750000,
                                                 'Bitrate Raw': '8.39 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Retr': 0,
                                                 'Transfer': 1048576000,
                                                 'Transfer Raw': '1000 MBytes'},
                                                {'Bitrate': 931250000,
                                                 'Bitrate Raw': '7.45 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Retr': 0,
                                                 'Transfer': 932184064,
                                                 'Transfer Raw': '889 MBytes'},
                                                {'Bitrate': 905000000,
                                                 'Bitrate Raw': '7.24 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Retr': 0,
                                                 'Transfer': 903872512,
                                                 'Transfer Raw': '862 MBytes'},
                                                {'Bitrate': 901250000,
                                                 'Bitrate Raw': '7.21 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Retr': 0,
                                                 'Transfer': 901775360,
                                                 'Transfer Raw': '860 MBytes'},
                                                {'Bitrate': 900000000,
                                                 'Bitrate Raw': '7.20 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Retr': 0,
                                                 'Transfer': 900726784,
                                                 'Transfer Raw': '859 MBytes'},
                                                {'Bitrate': 900000000,
                                                 'Bitrate Raw': '7.20 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Retr': 0,
                                                 'Transfer': 899678208,
                                                 'Transfer Raw': '858 MBytes'},
                                                {'Bitrate': 1041250000,
                                                 'Bitrate Raw': '8.33 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Retr': 0,
                                                 'Transfer': 1040187392,
                                                 'Transfer Raw': '992 MBytes'},
                                                {'Bitrate': 902500000,
                                                 'Bitrate Raw': '7.22 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Retr': 0,
                                                 'Transfer': 902823936,
                                                 'Transfer Raw': '861 MBytes'},
                                                {'Bitrate': 867500000,
                                                 'Bitrate Raw': '6.94 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Retr': 0,
                                                 'Transfer': 869269504,
                                                 'Transfer Raw': '829 MBytes'},
                                                {'Bitrate': 895000000,
                                                 'Bitrate Raw': '7.16 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 893386752,
                                                 'Transfer Raw': '852 MBytes'},
                                                {'Bitrate': 928750000,
                                                 'Bitrate Raw': '7.43 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 9287866777,
                                                 'Transfer Raw': '8.65 GBytes'},
                                                {'Bitrate': 926250000,
                                                 'Bitrate Raw': '7.41 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 9287866777,
                                                 'Transfer Raw': '8.65 GBytes'}],
        ('46036@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 1048750000,
                                                 'Bitrate Raw': '8.39 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Retr': 0,
                                                 'Transfer': 1048576000,
                                                 'Transfer Raw': '1000 MBytes'},
                                                {'Bitrate': 931250000,
                                                 'Bitrate Raw': '7.45 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Retr': 0,
                                                 'Transfer': 932184064,
                                                 'Transfer Raw': '889 MBytes'},
                                                {'Bitrate': 905000000,
                                                 'Bitrate Raw': '7.24 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Retr': 0,
                                                 'Transfer': 903872512,
                                                 'Transfer Raw': '862 MBytes'},
                                                {'Bitrate': 901250000,
                                                 'Bitrate Raw': '7.21 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Retr': 0,
                                                 'Transfer': 901775360,
                                                 'Transfer Raw': '860 MBytes'},
                                                {'Bitrate': 900000000,
                                                 'Bitrate Raw': '7.20 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Retr': 0,
                                                 'Transfer': 900726784,
                                                 'Transfer Raw': '859 MBytes'},
                                                {'Bitrate': 900000000,
                                                 'Bitrate Raw': '7.20 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Retr': 0,
                                                 'Transfer': 899678208,
                                                 'Transfer Raw': '858 MBytes'},
                                                {'Bitrate': 1041250000,
                                                 'Bitrate Raw': '8.33 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Retr': 0,
                                                 'Transfer': 1040187392,
                                                 'Transfer Raw': '992 MBytes'},
                                                {'Bitrate': 902500000,
                                                 'Bitrate Raw': '7.22 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Retr': 0,
                                                 'Transfer': 902823936,
                                                 'Transfer Raw': '861 MBytes'},
                                                {'Bitrate': 867500000,
                                                 'Bitrate Raw': '6.94 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Retr': 0,
                                                 'Transfer': 869269504,
                                                 'Transfer Raw': '829 MBytes'},
                                                {'Bitrate': 895000000,
                                                 'Bitrate Raw': '7.16 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 893386752,
                                                 'Transfer Raw': '852 MBytes'},
                                                {'Bitrate': 928750000,
                                                 'Bitrate Raw': '7.43 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 9287866777,
                                                 'Transfer Raw': '8.65 GBytes'},
                                                {'Bitrate': 926250000,
                                                 'Bitrate Raw': '7.41 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 9287866777,
                                                 'Transfer Raw': '8.65 GBytes'}],
        ('46052@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 1048750000,
                                                 'Bitrate Raw': '8.39 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Retr': 0,
                                                 'Transfer': 1048576000,
                                                 'Transfer Raw': '1000 MBytes'},
                                                {'Bitrate': 931250000,
                                                 'Bitrate Raw': '7.45 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Retr': 0,
                                                 'Transfer': 932184064,
                                                 'Transfer Raw': '889 MBytes'},
                                                {'Bitrate': 905000000,
                                                 'Bitrate Raw': '7.24 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Retr': 0,
                                                 'Transfer': 903872512,
                                                 'Transfer Raw': '862 MBytes'},
                                                {'Bitrate': 901250000,
                                                 'Bitrate Raw': '7.21 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Retr': 0,
                                                 'Transfer': 901775360,
                                                 'Transfer Raw': '860 MBytes'},
                                                {'Bitrate': 900000000,
                                                 'Bitrate Raw': '7.20 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Retr': 0,
                                                 'Transfer': 900726784,
                                                 'Transfer Raw': '859 MBytes'},
                                                {'Bitrate': 900000000,
                                                 'Bitrate Raw': '7.20 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Retr': 0,
                                                 'Transfer': 899678208,
                                                 'Transfer Raw': '858 MBytes'},
                                                {'Bitrate': 1041250000,
                                                 'Bitrate Raw': '8.33 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Retr': 0,
                                                 'Transfer': 1040187392,
                                                 'Transfer Raw': '992 MBytes'},
                                                {'Bitrate': 902500000,
                                                 'Bitrate Raw': '7.22 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Retr': 0,
                                                 'Transfer': 902823936,
                                                 'Transfer Raw': '861 MBytes'},
                                                {'Bitrate': 867500000,
                                                 'Bitrate Raw': '6.94 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Retr': 0,
                                                 'Transfer': 869269504,
                                                 'Transfer Raw': '829 MBytes'},
                                                {'Bitrate': 895000000,
                                                 'Bitrate Raw': '7.16 Gbits/sec',
                                                 'Cwnd': 982016,
                                                 'Cwnd Raw': '959 KBytes',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 893386752,
                                                 'Transfer Raw': '852 MBytes'},
                                                {'Bitrate': 928750000,
                                                 'Bitrate Raw': '7.43 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.0),
                                                 'Retr': 0,
                                                 'Transfer': 9287866777,
                                                 'Transfer Raw': '8.65 GBytes'},
                                                {'Bitrate': 926250000,
                                                 'Bitrate Raw': '7.41 Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 9287866777,
                                                 'Transfer Raw': '8.65 GBytes'}],
        ('multiport@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 3150000000,
                                                     'Bitrate Raw': '25.2 Gbits/sec',
                                                     'Interval': (0.0,
                                                                  1.0),
                                                     'Retr': 0,
                                                     'Transfer': 3146063544,
                                                     'Transfer Raw': '2.93 GBytes'},
                                                    {'Bitrate': 2787500000,
                                                     'Bitrate Raw': '22.3 Gbits/sec',
                                                     'Interval': (1.0,
                                                                  2.0),
                                                     'Retr': 0,
                                                     'Transfer': 2791728742,
                                                     'Transfer Raw': '2.60 GBytes'},
                                                    {'Bitrate': 2712500000,
                                                     'Bitrate Raw': '21.7 Gbits/sec',
                                                     'Interval': (2.0,
                                                                  3.0),
                                                     'Retr': 0,
                                                     'Transfer': 2716566814,
                                                     'Transfer Raw': '2.53 GBytes'},
                                                    {'Bitrate': 2700000000,
                                                     'Bitrate Raw': '21.6 Gbits/sec',
                                                     'Interval': (3.0,
                                                                  4.0),
                                                     'Retr': 0,
                                                     'Transfer': 2705829396,
                                                     'Transfer Raw': '2.52 GBytes'},
                                                    {'Bitrate': 2700000000,
                                                     'Bitrate Raw': '21.6 Gbits/sec',
                                                     'Interval': (4.0,
                                                                  5.0),
                                                     'Retr': 0,
                                                     'Transfer': 2705829396,
                                                     'Transfer Raw': '2.52 GBytes'},
                                                    {'Bitrate': 2700000000,
                                                     'Bitrate Raw': '21.6 Gbits/sec',
                                                     'Interval': (5.0,
                                                                  6.0),
                                                     'Retr': 0,
                                                     'Transfer': 2695091978,
                                                     'Transfer Raw': '2.51 GBytes'},
                                                    {'Bitrate': 3125000000,
                                                     'Bitrate Raw': '25.0 Gbits/sec',
                                                     'Interval': (6.0,
                                                                  7.0),
                                                     'Retr': 0,
                                                     'Transfer': 3124588707,
                                                     'Transfer Raw': '2.91 GBytes'},
                                                    {'Bitrate': 2712500000,
                                                     'Bitrate Raw': '21.7 Gbits/sec',
                                                     'Interval': (7.0,
                                                                  8.0),
                                                     'Retr': 0,
                                                     'Transfer': 2705829396,
                                                     'Transfer Raw': '2.52 GBytes'},
                                                    {'Bitrate': 2600000000,
                                                     'Bitrate Raw': '20.8 Gbits/sec',
                                                     'Interval': (8.0,
                                                                  9.0),
                                                     'Retr': 0,
                                                     'Transfer': 2609192632,
                                                     'Transfer Raw': '2.43 GBytes'},
                                                    {'Bitrate': 2687500000,
                                                     'Bitrate Raw': '21.5 Gbits/sec',
                                                     'Interval': (9.0,
                                                                  10.0),
                                                     'Retr': 0,
                                                     'Transfer': 2684354560,
                                                     'Transfer Raw': '2.50 GBytes'},
                                                    {'Bitrate': 2787500000,
                                                     'Bitrate Raw': '22.3 Gbits/sec',
                                                     'Interval': (0.0,
                                                                  10.0),
                                                     'Retr': 0,
                                                     'Transfer': 27917287424,
                                                     'Transfer Raw': '26.0 GBytes'},
                                                    {'Bitrate': 2775000000,
                                                     'Bitrate Raw': '22.2 Gbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Transfer': 27917287424,
                                                     'Transfer Raw': '26.0 GBytes'}]},
    'INFO': ['Connecting to host 127.0.0.1, port 5201', 'iperf Done.']}


COMMAND_OUTPUT_multiple_connections_server = """
xyz@debian:~$ iperf3 -s -p 5016 -f k -i 1
-----------------------------------------------------------
Server listening on 5016
-----------------------------------------------------------
Accepted connection from 127.0.0.1, port 38898
[  5] local 127.0.0.1 port 5016 connected to 127.0.0.1 port 38900
[  8] local 127.0.0.1 port 5016 connected to 127.0.0.1 port 38908
[ 10] local 127.0.0.1 port 5016 connected to 127.0.0.1 port 38916
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-1.00   sec  1.42 GBytes  12214422 Kbits/sec
[  8]   0.00-1.00   sec  1.42 GBytes  12214364 Kbits/sec
[ 10]   0.00-1.00   sec  1.42 GBytes  12213301 Kbits/sec
[SUM]   0.00-1.00   sec  4.27 GBytes  36642218 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   1.00-2.00   sec  1.65 GBytes  14143193 Kbits/sec
[  8]   1.00-2.00   sec  1.65 GBytes  14142158 Kbits/sec
[ 10]   1.00-2.00   sec  1.65 GBytes  14143210 Kbits/sec
[SUM]   1.00-2.00   sec  4.94 GBytes  42428531 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   2.00-3.00   sec  1.63 GBytes  14003833 Kbits/sec
[  8]   2.00-3.00   sec  1.63 GBytes  14003843 Kbits/sec
[ 10]   2.00-3.00   sec  1.63 GBytes  14003843 Kbits/sec
[SUM]   2.00-3.00   sec  4.89 GBytes  42011498 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   3.00-4.00   sec  1.70 GBytes  14593164 Kbits/sec
[  8]   3.00-4.00   sec  1.70 GBytes  14594199 Kbits/sec
[ 10]   3.00-4.00   sec  1.70 GBytes  14593150 Kbits/sec
[SUM]   3.00-4.00   sec  5.10 GBytes  43780542 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   4.00-5.00   sec  1.69 GBytes  14554131 Kbits/sec
[  8]   4.00-5.00   sec  1.69 GBytes  14554148 Kbits/sec
[ 10]   4.00-5.00   sec  1.69 GBytes  14554162 Kbits/sec
[SUM]   4.00-5.00   sec  5.08 GBytes  43662392 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   5.00-5.04   sec  67.6 MBytes  14552024 Kbits/sec
[  8]   5.00-5.04   sec  67.6 MBytes  14552291 Kbits/sec
[ 10]   5.00-5.04   sec  67.8 MBytes  14578833 Kbits/sec
[SUM]   5.00-5.04   sec   203 MBytes  43682969 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-5.04   sec  8.16 GBytes  13906767 Kbits/sec                  receiver
[  8]   0.00-5.04   sec  8.16 GBytes  13906767 Kbits/sec                  receiver
[ 10]   0.00-5.04   sec  8.16 GBytes  13906767 Kbits/sec                  receiver
[SUM]   0.00-5.04   sec  24.5 GBytes  41720300 Kbits/sec                  receiver
-----------------------------------------------------------
Server listening on 5016
-----------------------------------------------------------
xyz@debian:~$"""

COMMAND_KWARGS_multiple_connections_server = {
    "options": "-s -p 5016 -f k -i 1"}

COMMAND_RESULT_multiple_connections_server = {
    'CONNECTIONS': {
        ('127.0.0.1', '5016@127.0.0.1'): {'report': {'Bitrate': 5215037500,
                                                     'Bitrate Raw': '41720300 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  5.04),
                                                     'Transfer': 26306674688,
                                                     'Transfer Raw': '24.5 GBytes'}},
        ('38900@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 1526802750,
                                                 'Bitrate Raw': '12214422 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Transfer': 1524713390,
                                                 'Transfer Raw': '1.42 GBytes'},
                                                {'Bitrate': 1767899125,
                                                 'Bitrate Raw': '14143193 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Transfer': 1771674009,
                                                 'Transfer Raw': '1.65 GBytes'},
                                                {'Bitrate': 1750479125,
                                                 'Bitrate Raw': '14003833 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Transfer': 1750199173,
                                                 'Transfer Raw': '1.63 GBytes'},
                                                {'Bitrate': 1824145500,
                                                 'Bitrate Raw': '14593164 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Transfer': 1825361100,
                                                 'Transfer Raw': '1.70 GBytes'},
                                                {'Bitrate': 1819266375,
                                                 'Bitrate Raw': '14554131 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Transfer': 1814623682,
                                                 'Transfer Raw': '1.69 GBytes'},
                                                {'Bitrate': 1819003000,
                                                 'Bitrate Raw': '14552024 Kbits/sec',
                                                 'Interval': (5.0,
                                                              5.04),
                                                 'Transfer': 70883737,
                                                 'Transfer Raw': '67.6 MBytes'},
                                                {'Bitrate': 1738345875,
                                                 'Bitrate Raw': '13906767 Kbits/sec',
                                                 'Interval': (0.0,
                                                              5.04),
                                                 'Transfer': 8761733283,
                                                 'Transfer Raw': '8.16 GBytes'}],
        ('38908@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 1526795500,
                                                 'Bitrate Raw': '12214364 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Transfer': 1524713390,
                                                 'Transfer Raw': '1.42 GBytes'},
                                                {'Bitrate': 1767769750,
                                                 'Bitrate Raw': '14142158 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Transfer': 1771674009,
                                                 'Transfer Raw': '1.65 GBytes'},
                                                {'Bitrate': 1750480375,
                                                 'Bitrate Raw': '14003843 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Transfer': 1750199173,
                                                 'Transfer Raw': '1.63 GBytes'},
                                                {'Bitrate': 1824274875,
                                                 'Bitrate Raw': '14594199 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Transfer': 1825361100,
                                                 'Transfer Raw': '1.70 GBytes'},
                                                {'Bitrate': 1819268500,
                                                 'Bitrate Raw': '14554148 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Transfer': 1814623682,
                                                 'Transfer Raw': '1.69 GBytes'},
                                                {'Bitrate': 1819036375,
                                                 'Bitrate Raw': '14552291 Kbits/sec',
                                                 'Interval': (5.0,
                                                              5.04),
                                                 'Transfer': 70883737,
                                                 'Transfer Raw': '67.6 MBytes'},
                                                {'Bitrate': 1738345875,
                                                 'Bitrate Raw': '13906767 Kbits/sec',
                                                 'Interval': (0.0,
                                                              5.04),
                                                 'Transfer': 8761733283,
                                                 'Transfer Raw': '8.16 GBytes'}],
        ('38916@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 1526662625,
                                                 'Bitrate Raw': '12213301 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Transfer': 1524713390,
                                                 'Transfer Raw': '1.42 GBytes'},
                                                {'Bitrate': 1767901250,
                                                 'Bitrate Raw': '14143210 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Transfer': 1771674009,
                                                 'Transfer Raw': '1.65 GBytes'},
                                                {'Bitrate': 1750480375,
                                                 'Bitrate Raw': '14003843 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Transfer': 1750199173,
                                                 'Transfer Raw': '1.63 GBytes'},
                                                {'Bitrate': 1824143750,
                                                 'Bitrate Raw': '14593150 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Transfer': 1825361100,
                                                 'Transfer Raw': '1.70 GBytes'},
                                                {'Bitrate': 1819270250,
                                                 'Bitrate Raw': '14554162 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Transfer': 1814623682,
                                                 'Transfer Raw': '1.69 GBytes'},
                                                {'Bitrate': 1822354125,
                                                 'Bitrate Raw': '14578833 Kbits/sec',
                                                 'Interval': (5.0,
                                                              5.04),
                                                 'Transfer': 71093452,
                                                 'Transfer Raw': '67.8 MBytes'},
                                                {'Bitrate': 1738345875,
                                                 'Bitrate Raw': '13906767 Kbits/sec',
                                                 'Interval': (0.0,
                                                              5.04),
                                                 'Transfer': 8761733283,
                                                 'Transfer Raw': '8.16 GBytes'}],
        ('multiport@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 4580277250,
                                                     'Bitrate Raw': '36642218 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  1.0),
                                                     'Transfer': 4584877588,
                                                     'Transfer Raw': '4.27 GBytes'},
                                                    {'Bitrate': 5303566375,
                                                     'Bitrate Raw': '42428531 Kbits/sec',
                                                     'Interval': (1.0,
                                                                  2.0),
                                                     'Transfer': 5304284610,
                                                     'Transfer Raw': '4.94 GBytes'},
                                                    {'Bitrate': 5251437250,
                                                     'Bitrate Raw': '42011498 Kbits/sec',
                                                     'Interval': (2.0,
                                                                  3.0),
                                                     'Transfer': 5250597519,
                                                     'Transfer Raw': '4.89 GBytes'},
                                                    {'Bitrate': 5472567750,
                                                     'Bitrate Raw': '43780542 Kbits/sec',
                                                     'Interval': (3.0,
                                                                  4.0),
                                                     'Transfer': 5476083302,
                                                     'Transfer Raw': '5.10 GBytes'},
                                                    {'Bitrate': 5457799000,
                                                     'Bitrate Raw': '43662392 Kbits/sec',
                                                     'Interval': (4.0,
                                                                  5.0),
                                                     'Transfer': 5454608465,
                                                     'Transfer Raw': '5.08 GBytes'},
                                                    {'Bitrate': 5460371125,
                                                     'Bitrate Raw': '43682969 Kbits/sec',
                                                     'Interval': (5.0,
                                                                  5.04),
                                                     'Transfer': 212860928,
                                                     'Transfer Raw': '203 MBytes'},
                                                    {'Bitrate': 5215037500,
                                                     'Bitrate Raw': '41720300 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  5.04),
                                                     'Transfer': 26306674688,
                                                     'Transfer Raw': '24.5 GBytes'}]},
    'INFO': ['Server listening on 5016',
             'Accepted connection from 127.0.0.1, port 38898',
             'Server listening on 5016']}


COMMAND_OUTPUT_multiple_connections_udp_server = """
vagrant@app-svr:~$ iperf3 -s -p 5016 -f k -i 1
-----------------------------------------------------------
Server listening on 5016
-----------------------------------------------------------
Accepted connection from 127.0.0.1, port 57560
[  5] local 127.0.0.1 port 5016 connected to 127.0.0.1 port 33549
[  6] local 127.0.0.1 port 5016 connected to 127.0.0.1 port 36062
[  9] local 127.0.0.1 port 5016 connected to 127.0.0.1 port 52695
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-1.00   sec   129 KBytes  1057 Kbits/sec  0.007 ms  0/6 (0%)
[  6]   0.00-1.00   sec   129 KBytes  1057 Kbits/sec  0.009 ms  0/6 (0%)
[  9]   0.00-1.00   sec   129 KBytes  1057 Kbits/sec  0.007 ms  0/6 (0%)
[SUM]   0.00-1.00   sec   387 KBytes  3170 Kbits/sec  0.007 ms  0/18 (0%)
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   1.00-2.00   sec   129 KBytes  1057 Kbits/sec  0.008 ms  0/6 (0%)
[  6]   1.00-2.00   sec   129 KBytes  1057 Kbits/sec  0.010 ms  0/6 (0%)
[  9]   1.00-2.00   sec   129 KBytes  1057 Kbits/sec  0.008 ms  0/6 (0%)
[SUM]   1.00-2.00   sec   387 KBytes  3170 Kbits/sec  0.009 ms  0/18 (0%)
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   2.00-3.00   sec   129 KBytes  1057 Kbits/sec  0.007 ms  0/6 (0%)
[  6]   2.00-3.00   sec   129 KBytes  1057 Kbits/sec  0.009 ms  0/6 (0%)
[  9]   2.00-3.00   sec   129 KBytes  1057 Kbits/sec  0.007 ms  0/6 (0%)
[SUM]   2.00-3.00   sec   387 KBytes  3170 Kbits/sec  0.008 ms  0/18 (0%)
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   3.00-4.00   sec   129 KBytes  1057 Kbits/sec  0.008 ms  0/6 (0%)
[  6]   3.00-4.00   sec   129 KBytes  1057 Kbits/sec  0.009 ms  0/6 (0%)
[  9]   3.00-4.00   sec   129 KBytes  1057 Kbits/sec  0.008 ms  0/6 (0%)
[SUM]   3.00-4.00   sec   387 KBytes  3170 Kbits/sec  0.008 ms  0/18 (0%)
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   4.00-5.00   sec   129 KBytes  1057 Kbits/sec  0.009 ms  0/6 (0%)
[  6]   4.00-5.00   sec   129 KBytes  1057 Kbits/sec  0.014 ms  0/6 (0%)
[  9]   4.00-5.00   sec   129 KBytes  1057 Kbits/sec  0.010 ms  0/6 (0%)
[SUM]   4.00-5.00   sec   387 KBytes  3170 Kbits/sec  0.011 ms  0/18 (0%)
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-5.04   sec   645 KBytes  1048 Kbits/sec  0.009 ms  0/30 (0%)  receiver
[  6]   0.00-5.04   sec   645 KBytes  1048 Kbits/sec  0.014 ms  0/30 (0%)  receiver
[  9]   0.00-5.04   sec   645 KBytes  1048 Kbits/sec  0.010 ms  0/30 (0%)  receiver
[SUM]   0.00-5.04   sec  1.89 MBytes  3145 Kbits/sec  0.011 ms  0/90 (0%)  receiver
-----------------------------------------------------------
Server listening on 5016
-----------------------------------------------------------
vagrant@app-svr:~$"""

COMMAND_KWARGS_multiple_connections_udp_server = {
    "options": "-s -p 5016 -f k -i 1"
}

COMMAND_RESULT_multiple_connections_udp_server = {
    'CONNECTIONS': {
        ('127.0.0.1', '5016@127.0.0.1'): {'report': {'Bitrate': 393125,
                                                     'Bitrate Raw': '3145 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  5.04),
                                                     'Jitter': 0.011,
                                                     'Jitter Raw': '0.011 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 90),
                                                     'Transfer': 1981808,
                                                     'Transfer Raw': '1.89 MBytes'}},
        ('33549@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Jitter': 0.007,
                                                 'Jitter Raw': '0.007 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Jitter': 0.008,
                                                 'Jitter Raw': '0.008 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Jitter': 0.007,
                                                 'Jitter Raw': '0.007 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Jitter': 0.008,
                                                 'Jitter Raw': '0.008 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Jitter': 0.009,
                                                 'Jitter Raw': '0.009 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 131000,
                                                 'Bitrate Raw': '1048 Kbits/sec',
                                                 'Interval': (0.0,
                                                              5.04),
                                                 'Jitter': 0.009,
                                                 'Jitter Raw': '0.009 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             30),
                                                 'Transfer': 660480,
                                                 'Transfer Raw': '645 KBytes'}],
        ('36062@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Jitter': 0.009,
                                                 'Jitter Raw': '0.009 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Jitter': 0.010,
                                                 'Jitter Raw': '0.010 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Jitter': 0.009,
                                                 'Jitter Raw': '0.009 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Jitter': 0.009,
                                                 'Jitter Raw': '0.009 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Jitter': 0.014,
                                                 'Jitter Raw': '0.014 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 131000,
                                                 'Bitrate Raw': '1048 Kbits/sec',
                                                 'Interval': (0.0,
                                                              5.04),
                                                 'Jitter': 0.014,
                                                 'Jitter Raw': '0.014 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             30),
                                                 'Transfer': 660480,
                                                 'Transfer Raw': '645 KBytes'}],
        ('52695@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Jitter': 0.007,
                                                 'Jitter Raw': '0.007 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Jitter': 0.008,
                                                 'Jitter Raw': '0.008 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Jitter': 0.007,
                                                 'Jitter Raw': '0.007 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Jitter': 0.008,
                                                 'Jitter Raw': '0.008 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Jitter': 0.010,
                                                 'Jitter Raw': '0.010 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 131000,
                                                 'Bitrate Raw': '1048 Kbits/sec',
                                                 'Interval': (0.0,
                                                              5.04),
                                                 'Jitter': 0.010,
                                                 'Jitter Raw': '0.010 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             30),
                                                 'Transfer': 660480,
                                                 'Transfer Raw': '645 KBytes'}],
        ('multiport@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 396250,
                                                     'Bitrate Raw': '3170 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  1.0),
                                                     'Jitter': 0.007,
                                                     'Jitter Raw': '0.007 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 18),
                                                     'Transfer': 396288,
                                                     'Transfer Raw': '387 KBytes'},
                                                    {'Bitrate': 396250,
                                                     'Bitrate Raw': '3170 Kbits/sec',
                                                     'Interval': (1.0,
                                                                  2.0),
                                                     'Jitter': 0.009,
                                                     'Jitter Raw': '0.009 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 18),
                                                     'Transfer': 396288,
                                                     'Transfer Raw': '387 KBytes'},
                                                    {'Bitrate': 396250,
                                                     'Bitrate Raw': '3170 Kbits/sec',
                                                     'Interval': (2.0,
                                                                  3.0),
                                                     'Jitter': 0.008,
                                                     'Jitter Raw': '0.008 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 18),
                                                     'Transfer': 396288,
                                                     'Transfer Raw': '387 KBytes'},
                                                    {'Bitrate': 396250,
                                                     'Bitrate Raw': '3170 Kbits/sec',
                                                     'Interval': (3.0,
                                                                  4.0),
                                                     'Jitter': 0.008,
                                                     'Jitter Raw': '0.008 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 18),
                                                     'Transfer': 396288,
                                                     'Transfer Raw': '387 KBytes'},
                                                    {'Bitrate': 396250,
                                                     'Bitrate Raw': '3170 Kbits/sec',
                                                     'Interval': (4.0,
                                                                  5.0),
                                                     'Jitter': 0.011,
                                                     'Jitter Raw': '0.011 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 18),
                                                     'Transfer': 396288,
                                                     'Transfer Raw': '387 KBytes'},
                                                    {'Bitrate': 393125,
                                                     'Bitrate Raw': '3145 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  5.04),
                                                     'Jitter': 0.011,
                                                     'Jitter Raw': '0.011 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 90),
                                                     'Transfer': 1981808,
                                                     'Transfer Raw': '1.89 MBytes'}]},
    'INFO': ['Server listening on 5016',
             'Accepted connection from 127.0.0.1, port 57560',
             'Server listening on 5016']}


COMMAND_OUTPUT_multiple_connections_udp_client = """
vagrant@app-svr:~$ iperf3 -c 127.0.0.1 -u -p 5016 -f k -P 2 -i 1 -t 3.0 -b 1000.0k
Connecting to host 127.0.0.1, port 5016
[  5] local 127.0.0.1 port 35428 connected to 127.0.0.1 port 5016
[  7] local 127.0.0.1 port 50221 connected to 127.0.0.1 port 5016
[ ID] Interval           Transfer     Bitrate         Total Datagrams
[  5]   0.00-1.00   sec   129 KBytes  1057 Kbits/sec  6
[  7]   0.00-1.00   sec   129 KBytes  1057 Kbits/sec  6
[SUM]   0.00-1.00   sec   258 KBytes  2113 Kbits/sec  12
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   1.00-2.00   sec   129 KBytes  1057 Kbits/sec  6
[  7]   1.00-2.00   sec   129 KBytes  1057 Kbits/sec  6
[SUM]   1.00-2.00   sec   258 KBytes  2114 Kbits/sec  12
- - - - - - - - - - - - - - - - - - - - - - - - -
[  5]   2.00-3.00   sec   129 KBytes  1057 Kbits/sec  6
[  7]   2.00-3.00   sec   129 KBytes  1057 Kbits/sec  6
[SUM]   2.00-3.00   sec   258 KBytes  2113 Kbits/sec  12
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-3.00   sec   387 KBytes  1057 Kbits/sec  0.000 ms  0/18 (0%)  sender
[  5]   0.00-3.04   sec   387 KBytes  1042 Kbits/sec  0.021 ms  0/18 (0%)  receiver
[  7]   0.00-3.00   sec   387 KBytes  1057 Kbits/sec  0.000 ms  0/18 (0%)  sender
[  7]   0.00-3.04   sec   387 KBytes  1042 Kbits/sec  0.016 ms  0/18 (0%)  receiver
[SUM]   0.00-3.00   sec   774 KBytes  2113 Kbits/sec  0.000 ms  0/36 (0%)  sender
[SUM]   0.00-3.04   sec   774 KBytes  2084 Kbits/sec  0.018 ms  0/36 (0%)  receiver

iperf Done.
vagrant@app-svr:~$"""

COMMAND_KWARGS_multiple_connections_udp_client = {
    "options": "-c 127.0.0.1 -u -p 5016 -f k -P 2 -i 1 -t 3.0 -b 1000.0k"
}

COMMAND_RESULT_multiple_connections_udp_client = {
    'CONNECTIONS': {
        ('127.0.0.1', '5016@127.0.0.1'): {'report': {'Bitrate': 264125,
                                                     'Bitrate Raw': '2113 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  3.0),
                                                     'Jitter': 0.0,
                                                     'Jitter Raw': '0.000 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 36),
                                                     'Transfer': 792576,
                                                     'Transfer Raw': '774 KBytes'}},
        ('35428@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Total_Datagrams': 6,
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Total_Datagrams': 6,
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Total_Datagrams': 6,
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              3.0),
                                                 'Jitter': 0.0,
                                                 'Jitter Raw': '0.000 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             18),
                                                 'Transfer': 396288,
                                                 'Transfer Raw': '387 KBytes'},
                                                {'Bitrate': 130250,
                                                 'Bitrate Raw': '1042 Kbits/sec',
                                                 'Interval': (0.0,
                                                              3.04),
                                                 'Jitter': 0.021,
                                                 'Jitter Raw': '0.021 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             18),
                                                 'Transfer': 396288,
                                                 'Transfer Raw': '387 KBytes'}],
        ('50221@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Total_Datagrams': 6,
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Total_Datagrams': 6,
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Total_Datagrams': 6,
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              3.0),
                                                 'Jitter': 0.0,
                                                 'Jitter Raw': '0.000 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             18),
                                                 'Transfer': 396288,
                                                 'Transfer Raw': '387 KBytes'},
                                                {'Bitrate': 130250,
                                                 'Bitrate Raw': '1042 Kbits/sec',
                                                 'Interval': (0.0,
                                                              3.04),
                                                 'Jitter': 0.016,
                                                 'Jitter Raw': '0.016 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             18),
                                                 'Transfer': 396288,
                                                 'Transfer Raw': '387 KBytes'}],
        ('multiport@127.0.0.1', '5016@127.0.0.1'): [{'Bitrate': 264125,
                                                     'Bitrate Raw': '2113 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  1.0),
                                                     'Total_Datagrams': 12,
                                                     'Transfer': 264192,
                                                     'Transfer Raw': '258 KBytes'},
                                                    {'Bitrate': 264250,
                                                     'Bitrate Raw': '2114 Kbits/sec',
                                                     'Interval': (1.0,
                                                                  2.0),
                                                     'Total_Datagrams': 12,
                                                     'Transfer': 264192,
                                                     'Transfer Raw': '258 KBytes'},
                                                    {'Bitrate': 264125,
                                                     'Bitrate Raw': '2113 Kbits/sec',
                                                     'Interval': (2.0,
                                                                  3.0),
                                                     'Total_Datagrams': 12,
                                                     'Transfer': 264192,
                                                     'Transfer Raw': '258 KBytes'},
                                                    {'Bitrate': 264125,
                                                     'Bitrate Raw': '2113 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  3.0),
                                                     'Jitter': 0.0,
                                                     'Jitter Raw': '0.000 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 36),
                                                     'Transfer': 792576,
                                                     'Transfer Raw': '774 KBytes'},
                                                    {'Bitrate': 260500,
                                                     'Bitrate Raw': '2084 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  3.04),
                                                     'Jitter': 0.018,
                                                     'Jitter Raw': '0.018 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 36),
                                                     'Transfer': 792576,
                                                     'Transfer Raw': '774 KBytes'}]},
    'INFO': ['Connecting to host 127.0.0.1, port 5016', 'iperf Done.']}


COMMAND_OUTPUT_singlerun_server = """
xyz@debian:~$ iperf3 -s -p 5001 -f k -i 1.0
-----------------------------------------------------------
Server listening on 5001
-----------------------------------------------------------
Accepted connection from 127.0.0.1, port 38056
[  5] local 127.0.0.1 port 5001 connected to 127.0.0.1 port 38068
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-1.00   sec  2.85 GBytes  24466678 Kbits/sec
[  5]   1.00-2.00   sec  2.49 GBytes  21378343 Kbits/sec
[  5]   2.00-3.00   sec  3.04 GBytes  26132144 Kbits/sec
[  5]   3.00-4.00   sec  4.30 GBytes  36917136 Kbits/sec
[  5]   4.00-5.00   sec  3.31 GBytes  28437781 Kbits/sec
[  5]   5.00-6.00   sec  2.60 GBytes  22305911 Kbits/sec
[  5]   6.00-7.00   sec  3.14 GBytes  26933156 Kbits/sec
[  5]   7.00-8.00   sec  2.34 GBytes  20110361 Kbits/sec
[  5]   8.00-9.00   sec  2.48 GBytes  21298523 Kbits/sec
[  5]   9.00-10.00  sec  2.52 GBytes  21628470 Kbits/sec
[  5]  10.00-10.04  sec   108 MBytes  21534518 Kbits/sec
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-10.04  sec  29.2 GBytes  24946492 Kbits/sec                  receiver
-----------------------------------------------------------
Server listening on 5001
-----------------------------------------------------------
xyz@debian:~$"""

COMMAND_KWARGS_singlerun_server = {"options": "-s -p 5001 -f k -i 1.0"}

COMMAND_RESULT_singlerun_server = {
    'CONNECTIONS': {
        ('127.0.0.1', '5001@127.0.0.1'): {'report': {'Bitrate': 3118311500,
                                                     'Bitrate Raw': '24946492 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Transfer': 31353261260,
                                                     'Transfer Raw': '29.2 GBytes'}},
        ('38068@127.0.0.1', '5001@127.0.0.1'): [{'Bitrate': 3058334750,
                                                 'Bitrate Raw': '24466678 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Transfer': 3060164198,
                                                 'Transfer Raw': '2.85 GBytes'},
                                                {'Bitrate': 2672292875,
                                                 'Bitrate Raw': '21378343 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Transfer': 2673617141,
                                                 'Transfer Raw': '2.49 GBytes'},
                                                {'Bitrate': 3266518000,
                                                 'Bitrate Raw': '26132144 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Transfer': 3264175144,
                                                 'Transfer Raw': '3.04 GBytes'},
                                                {'Bitrate': 4614642000,
                                                 'Bitrate Raw': '36917136 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Transfer': 4617089843,
                                                 'Transfer Raw': '4.30 GBytes'},
                                                {'Bitrate': 3554722625,
                                                 'Bitrate Raw': '28437781 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Transfer': 3554085437,
                                                 'Transfer Raw': '3.31 GBytes'},
                                                {'Bitrate': 2788238875,
                                                 'Bitrate Raw': '22305911 Kbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Transfer': 2791728742,
                                                 'Transfer Raw': '2.60 GBytes'},
                                                {'Bitrate': 3366644500,
                                                 'Bitrate Raw': '26933156 Kbits/sec',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Transfer': 3371549327,
                                                 'Transfer Raw': '3.14 GBytes'},
                                                {'Bitrate': 2513795125,
                                                 'Bitrate Raw': '20110361 Kbits/sec',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Transfer': 2512555868,
                                                 'Transfer Raw': '2.34 GBytes'},
                                                {'Bitrate': 2662315375,
                                                 'Bitrate Raw': '21298523 Kbits/sec',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Transfer': 2662879723,
                                                 'Transfer Raw': '2.48 GBytes'},
                                                {'Bitrate': 2703558750,
                                                 'Bitrate Raw': '21628470 Kbits/sec',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Transfer': 2705829396,
                                                 'Transfer Raw': '2.52 GBytes'},
                                                {'Bitrate': 2691814750,
                                                 'Bitrate Raw': '21534518 Kbits/sec',
                                                 'Interval': (10.0,
                                                              10.04),
                                                 'Transfer': 113246208,
                                                 'Transfer Raw': '108 MBytes'},
                                                {'Bitrate': 3118311500,
                                                 'Bitrate Raw': '24946492 Kbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 31353261260,
                                                 'Transfer Raw': '29.2 GBytes'}]},
    'INFO': ['Server listening on 5001',
             'Accepted connection from 127.0.0.1, port 38056',
             'Server listening on 5001']}

COMMAND_OUTPUT_singlerun_udp_server = """
xyz@debian:~$ iperf3 -s -p 5001 -f k -i 1.0
-----------------------------------------------------------
Server listening on 5001
-----------------------------------------------------------
Accepted connection from 127.0.0.1, port 39914
[  5] local 127.0.0.1 port 5001 connected to 127.0.0.1 port 44895
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-1.00   sec   129 KBytes  1057 Kbits/sec  0.007 ms  0/6 (0%)
[  5]   1.00-2.00   sec   129 KBytes  1057 Kbits/sec  0.008 ms  0/6 (0%)
[  5]   2.00-3.00   sec   129 KBytes  1057 Kbits/sec  0.007 ms  0/6 (0%)
[  5]   3.00-4.00   sec   129 KBytes  1057 Kbits/sec  0.008 ms  0/6 (0%)
[  5]   4.00-5.00   sec   129 KBytes  1057 Kbits/sec  0.006 ms  0/6 (0%)
[  5]   5.00-6.00   sec   129 KBytes  1057 Kbits/sec  0.005 ms  0/6 (0%)
[  5]   6.00-7.00   sec   129 KBytes  1057 Kbits/sec  0.010 ms  0/6 (0%)
[  5]   7.00-8.00   sec   129 KBytes  1057 Kbits/sec  0.017 ms  0/6 (0%)
[  5]   8.00-9.00   sec   129 KBytes  1057 Kbits/sec  0.017 ms  0/6 (0%)
[  5]   9.00-10.00  sec   129 KBytes  1057 Kbits/sec  0.023 ms  0/6 (0%)
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
[  5]   0.00-10.04  sec  1.26 MBytes  1052 Kbits/sec  0.023 ms  0/60 (0%)  receiver
-----------------------------------------------------------
Server listening on 5001
-----------------------------------------------------------
xyz@debian:~$"""

COMMAND_KWARGS_singlerun_udp_server = {
    "options": "-s -p 5001 -f k -i 1.0"}

COMMAND_RESULT_singlerun_udp_server = {
    'CONNECTIONS': {
        ('127.0.0.1', '5001@127.0.0.1'): {'report': {'Bitrate': 131500,
                                                     'Bitrate Raw': '1052 Kbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Jitter': 0.023,
                                                     'Jitter Raw': '0.023 ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 60),
                                                     'Transfer': 1321205,
                                                     'Transfer Raw': '1.26 MBytes'}},
        ('44895@127.0.0.1', '5001@127.0.0.1'): [{'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Jitter': 0.007,
                                                 'Jitter Raw': '0.007 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Jitter': 0.008,
                                                 'Jitter Raw': '0.008 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Jitter': 0.007,
                                                 'Jitter Raw': '0.007 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Jitter': 0.008,
                                                 'Jitter Raw': '0.008 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Jitter': 0.006,
                                                 'Jitter Raw': '0.006 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Jitter': 0.005,
                                                 'Jitter Raw': '0.005 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Jitter': 0.010,
                                                 'Jitter Raw': '0.010 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Jitter': 0.017,
                                                 'Jitter Raw': '0.017 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Jitter': 0.017,
                                                 'Jitter Raw': '0.017 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 132125,
                                                 'Bitrate Raw': '1057 Kbits/sec',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Jitter': 0.023,
                                                 'Jitter Raw': '0.023 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 KBytes'},
                                                {'Bitrate': 131500,
                                                 'Bitrate Raw': '1052 Kbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Jitter': 0.023,
                                                 'Jitter Raw': '0.023 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             60),
                                                 'Transfer': 1321205,
                                                 'Transfer Raw': '1.26 MBytes'}]},
    'INFO': ['Server listening on 5001',
             'Accepted connection from 127.0.0.1, port 39914',
             'Server listening on 5001']}

COMMAND_OUTPUT_version = """xyz@debian:~$ iperf3 --version
iperf 3.12 (cJSON 1.7.15)
Linux ute-image12 6.1.0-26-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.112-1 (2024-09-30) x86_64
Optional features available: CPU affinity setting, IPv6 flow label, SCTP, TCP congestion algorithm setting, sendfile / zerocopy, socket pacing, authentication, bind to device, support IPv4 don't fragment
xyz@debian:~$"""

COMMAND_KWARGS_version = {"options": "--version"}

COMMAND_RESULT_version = {
    "CONNECTIONS": {},
    "INFO": [
        "iperf 3.12 (cJSON 1.7.15)",
        "Linux ute-image12 6.1.0-26-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.112-1 (2024-09-30) x86_64",
        "Optional features available: CPU affinity setting, IPv6 flow label, SCTP, TCP congestion algorithm setting, sendfile / zerocopy, socket pacing, authentication, bind to device, support IPv4 don't fragment",
    ],
}
