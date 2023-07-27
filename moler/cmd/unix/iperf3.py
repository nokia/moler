# -*- coding: utf-8 -*-
"""
Iperf3 command module.

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

__author__ = "Kacper Kozik"
__copyright__ = "Copyright (C) 2023, Nokia"
__email__ = "kacper.kozik@nokia.com"


import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.util.converterhelper import ConverterHelper
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.publisher import Publisher


class Iperf3(GenericUnixCommand, Publisher):
    """
    Run iperf command, return its statistics and report.

    Single line of iperf output may look like::

      [ ID]   Interval       Transfer      Bitrate        Jitter   Lost/Total Datagrams
      [904]   0.0- 1.0 sec   1.17 MBytes   9.84 Mbits/sec   1.830 ms    0/ 837   (0%)

    It represents data transfer statistics reported per given interval.
    This line is parsed out and produces statistics record as python dict.
    (examples can be found at bottom of iperf2.py source code)
    Some keys inside dict are normalized to Bytes.
    In such case you will see both: raw and normalized values::

      'Transfer Raw':     '1.17 MBytes',
      'Transfer':         1226833,           # Bytes
      'Bitrate Raw':    '9.84 Mbits/sec',
      'Bitrate':        1230000,           # Bytes/sec

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

    def __init__(
        self, connection, options, prompt=None, newline_chars=None, runner=None
    ):
        """
        Create iperf3 command

        :param connection: moler connection used by iperf command
        :param options: iperf options (as in iperf documentation)
        :param prompt: prompt (regexp) where iperf starts from, if None - default prompt regexp used
        :param newline_chars: expected newline characters of iperf output
        :param runner: runner used for command
        """
        super(Iperf3, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.port, self.options = self._validate_options(options)
        self.current_ret["CONNECTIONS"] = dict()
        self.current_ret["INFO"] = list()

        # private values
        self._connection_dict = dict()
        self._same_host_connections = dict()
        self._converter_helper = ConverterHelper()
        self._got_server_report_hdr = False
        self._got_server_report = False
        self._stopping_server = False

    def __str__(self):
        str_base_value = super(Iperf3, self).__str__()
        str_value = "{}, awaited_prompt='{}')".format(
            str_base_value[:-1], self._re_prompt.pattern
        )
        return str_value

    _re_port = re.compile(r"(?P<PORT_OPTION>\-\-port|\-p)\s+(?P<PORT>\d+)")

    def _validate_options(self, options):
        if (("-d" in options) or ("--dualtest" in options)) and (
            ("-P" in options) or ("--parallel" in options)
        ):
            raise AttributeError(
                "Unsupported options combination (--dualtest & --parallel)"
            )
        if (("-u" in options) or ("--udp" in options)) and (
            ("-s" in options) or ("--server" in options)
        ):
            raise AttributeError(
                "Option (--udp) you are trying to set is client only")
        if (("-t" in options) or ("--time" in options)) and (
            ("-s" in options) or ("--server" in options)
        ):
            raise AttributeError(
                "Option (--time) you are trying to set is client only")
        if self._regex_helper.search_compiled(Iperf3._re_port, options):
            port = int(self._regex_helper.group("PORT"))
        else:
            port = 5201
        return port, options

    def build_command_string(self):
        cmd = "iperf3 " + str(self.options)
        return cmd

    @property
    def protocol(self):
        if any([self.options.startswith("-u"), " -u" in self.options, "--udp" in self.options]):
            return "udp"
        return "tcp"

    _re_interval = re.compile(
        r"(?P<INTERVAL_OPTION>\-\-interval|\-i)\s+(?P<INTERVAL>[\d\.]+)"
    )

    @property
    def interval(self):
        if self._regex_helper.search_compiled(Iperf3._re_interval, self.options):
            return float(self._regex_helper.group("INTERVAL"))
        return 0.0

    _re_time = re.compile(r"(?P<TIME_OPTION>\-\-time|\-t)\s+(?P<TIME>[\d\.]+)")

    @property
    def time(self):
        if self._regex_helper.search_compiled(Iperf3._re_time, self.options):
            return float(self._regex_helper.group("TIME"))
        return 10.0

    @property
    def dualtest(self):
        return ("--dualtest" in self.options) or ("-d" in self.options)

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
        return ("-c " in self.options) or ("--client " in self.options)

    @property
    def server(self):
        return any([self.options.startswith("-s"),
                    " -s" in self.options,
                    "--server" in self.options])

    @property
    def parallel_client(self):
        if self.client:
            return ("-P " in self.options) or ("--parallel " in self.options)
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
        singlerun_param_nonlast = ("-P 1 " in self.options) or (
            "--parallel 1 " in self.options
        )
        singlerun_param_as_last = self.options.endswith(
            "-P 1"
        ) or self.options.endswith("--parallel 1")
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
        return super(Iperf3, self).on_new_line(line, is_full_line)

    def _process_line_from_command(self, current_chunk, line, is_full_line):
        decoded_line = self._decode_line(line=line)
        if self._is_replicated_cmd_echo(line):
            return
        self.on_new_line(line=decoded_line, is_full_line=is_full_line)

    def _is_replicated_cmd_echo(self, line):
        prompt_and_command = r"{}\s*{}".format(
            self._re_prompt.pattern, self.command_string
        )
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
        super(Iperf3, self).subscribe(subscriber)

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
                return super(Iperf3, self).is_end_of_cmd_output(line)
            return False
        else:
            return super(Iperf3, self).is_end_of_cmd_output(line)

    def on_inactivity(self):
        """
        Call when no data is received on connection within self.life_status.inactivity_timeout seconds.

        :return: None
        """
        if self._stopping_server and (not self.done()):
            self.break_cmd()

    def _schedule_delayed_break(self, delay):
        self.life_status.inactivity_timeout = 1.0  # will activate on_inactivity()

    def _stop_server(self):
        if not self._stopping_server:
            if not self.singlerun_server:
                self._schedule_delayed_break(delay=1.0)
            self._stopping_server = True

    _re_command_failure = re.compile(
        r"(?P<FAILURE_MSG>.*failed.*|.*error.*|.*command not found.*|.*iperf:.*)"
    )

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Iperf3._re_command_failure, line):
            self.set_exception(
                CommandFailure(
                    self, "ERROR: {}".format(
                        self._regex_helper.group("FAILURE_MSG"))
                )
            )
            raise ParsingDone

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
            local = "{}@{}".format(local_port, local_host)
            remote = "{}@{}".format(remote_port, remote_host)
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

    # iperf output for: tcp server
    # [ ID] Interval      Transfer      Bitrate

    # iperf output for: tcp client
    # [ ID] Interval      Transfer      Bitrate      Retr        Cwnd

    # iperf output for: udp server
    # [ ID] Interval      Transfer      Bitrate      Jitter      Lost/Total Datagrams

    # iperf output for: udp client
    # [ ID] Interval      Transfer      Bitrate      Total Datagrams

    # _re_headers = re.compile(r"\[\s+ID\]\s+Interval\s+Transfer\s+Bitrate\s+Retr\s+Cwnd")

    _re_headers = re.compile(r"\[\s+ID\]\s+Interval\s+Transfer\s+Bitrate")

    def _parse_headers(self, line):
        if self._regex_helper.search_compiled(Iperf3._re_headers, line):
            if self.parallel_client:
                # header line is after connections
                # so, we can create virtual Summary connection
                client, server = list(self._connection_dict.values())[0]
                (
                    client_host,
                    client_port,
                    server_host,
                    server_port,
                ) = self._split_connection_name((client, server))
                connection_id = "[SUM]"
                self._connection_dict[connection_id] = (
                    "{}@{}".format("multiport", client_host),
                    server,
                )
            raise ParsingDone

    def _split_connection_name(self, connection_name):
        client, server = connection_name
        client_port, client_host = client.split("@")
        server_port, server_host = server.split("@")
        return client_host, client_port, server_host, server_port

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

    _r_rec_tcp_svr = r"{}\s+{}\s+{}\s+{}".format(
        _r_id, _r_interval, _r_transfer, _r_bitrate
    )
    _r_rec_tcp_cli = r"{}\s+{}\s+{}".format(_r_rec_tcp_svr, _r_retr, _r_cwnd)
    _r_rec_udp_svr = r"{}\s+{}\s+{}".format(
        _r_rec_tcp_svr, _r_jitter, _r_datagrams)
    _r_rec_udp_cli = r"{}\s+{}".format(_r_rec_tcp_svr, _r_total_datagrams)
    _r_rec_tcp_cli_summary = r"{}\s+{}".format(_r_rec_tcp_svr, _r_retr)

    _re_iperf_record_tcp_svr = re.compile(_r_rec_tcp_svr)
    _re_iperf_record_tcp_cli = re.compile(_r_rec_tcp_cli)
    _re_iperf_record_udp_svr = re.compile(_r_rec_udp_svr)
    _re_iperf_record_udp_cli = re.compile(_r_rec_udp_cli)
    _re_iperf_record_tcp_cli_summary = re.compile(_r_rec_tcp_cli_summary)

    def _parse_connection_info(self, line):
        regex_found = self._regex_helper.search_compiled
        # print("!"*50)

        if regex_found(Iperf3._re_iperf_record_udp_svr, line) or \
                self.protocol == "udp" and regex_found(
                    Iperf3._re_iperf_record_udp_cli, line) or \
                self.protocol == "tcp" and regex_found(
                    Iperf3._re_iperf_record_tcp_cli, line) or \
                self.protocol == "tcp" and self.client and regex_found(
                    Iperf3._re_iperf_record_tcp_cli_summary, line) or \
                regex_found(Iperf3._re_iperf_record_tcp_svr, line):

            iperf_record = self._regex_helper.groupdict()
            # import logging
            # logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # logging.warning(iperf_record)
            # logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            connection_id = iperf_record.pop("ID")
            iperf_record = self._detailed_parse_interval(iperf_record)
            iperf_record = self._detailed_parse_datagrams(iperf_record)
            # [SUM]  0.0- 4.0 sec  1057980 KBytes  2165942 Kbits/sec   last line when server used with -P
            if (not self.parallel_client) and (connection_id == "[SUM]"):
                raise ParsingDone  # skip it

            # import logging
            # logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # logging.warning(iperf_record)
            # logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            connection_name = self._connection_dict[connection_id]

            normalized_iperf_record = self._normalize_to_bytes(iperf_record)
            self._update_current_ret(connection_name, normalized_iperf_record)
            if self._need_add_multiport_summary_record_of_interval(
                connection_name, normalized_iperf_record, line
            ):
                self._calculate_multiport_summary_record_of_interval(
                    connection_name)

            self._parse_final_record(connection_name, line)

            if self.protocol == "udp" and self._got_server_report_hdr:
                self._got_server_report = True
            raise ParsingDone

    @staticmethod
    def _detailed_parse_interval(iperf_record):
        start, end = iperf_record["Interval"].split("-")
        iperf_record["Interval"] = (float(start), float(end))
        return iperf_record

    @staticmethod
    def _detailed_parse_datagrams(iperf_record):
        if "Lost_vs_Total_Datagrams" in iperf_record:
            lost, total = iperf_record["Lost_vs_Total_Datagrams"].split("/")
            iperf_record["Lost_vs_Total_Datagrams"] = (int(lost), int(total))
        return iperf_record

    def _update_current_ret(self, connection_name, info_dict):
        # import logging
        # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # print(info_dict)
        # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        if connection_name in self.current_ret["CONNECTIONS"]:
            self.current_ret["CONNECTIONS"][connection_name].append(info_dict)
        else:
            connection_dict = {connection_name: [info_dict]}
            self.current_ret["CONNECTIONS"].update(connection_dict)

        # import logging
        # logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # logging.warning(info_dict)
        # logging.warning("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    def _all_multiport_records_of_interval(self, connection_name):
        client, server = connection_name
        client_port, client_host = client.split("@")
        last_interval = self.current_ret["CONNECTIONS"][connection_name][-1]["Interval"]
        for conn_name in self._same_host_connections[client_host]:
            if conn_name not in self.current_ret["CONNECTIONS"]:
                return False
            if not self._get_last_record_of_interval(conn_name, last_interval):
                return False
        return True

    def _get_last_record_of_interval(self, connection_name, interval):
        last_rec = self.current_ret["CONNECTIONS"][connection_name][-1]
        if last_rec["Interval"] == interval:
            return last_rec
        if len(self.current_ret["CONNECTIONS"][connection_name]) > 1:
            pre_last_rec = self.current_ret["CONNECTIONS"][connection_name][-2]
            if pre_last_rec["Interval"] == interval:
                return pre_last_rec
        return None

    def _need_add_multiport_summary_record_of_interval(
        self, connection_name, last_iperf_record, line
    ):
        # print("!"*50)
        # print(last_iperf_record)
        # print("!"*50)
        if not self.server:
            return False
        if not self.parallel_client:
            return False
        if self._is_final_record(last_iperf_record, line):
            return False
        if not self._all_multiport_records_of_interval(connection_name):
            return False
        return True

    def _calculate_multiport_summary_record_of_interval(self, connection_name):
        client, server = connection_name
        client_port, client_host = client.split("@")
        connections = self._same_host_connections[client_host]

        interval = self.current_ret["CONNECTIONS"][connection_name][-1]["Interval"]
        if interval == (4.0, 5.0):
            pass
        transfers = [
            self._get_last_record_of_interval(conn, interval)["Transfer"]
            for conn in connections
        ]
        raw_transfers = [
            self._get_last_record_of_interval(conn, interval)["Transfer Raw"]
            for conn in connections
        ]
        bitrates = [
            self._get_last_record_of_interval(conn, interval)["Bitrate"]
            for conn in connections
        ]
        raw_bitrates = [
            self._get_last_record_of_interval(conn, interval)["Bitrate Raw"]
            for conn in connections
        ]

        if self.protocol == "tcp" and self.client:
            retrs = [
                self._get_last_record_of_interval(conn, interval)["Retr"]
                for conn in connections
            ]
            retrs_values = [int(ret) for ret in retrs]
            total_retrs = sum(retrs_values)
            # cwnds = [self._get_last_record_of_interval(conn, interval)['Cwnd'] for conn in connections]
            # raw_cwnds = [self._get_last_record_of_interval(conn, interval)['Cwnd Raw'] for conn in connections]
            # cwnd_unit = cwnds[0].split()[1]  # 'Cwnd': '1.37 MBytes'

        elif self.protocol == "udp" and self.server:
            jitters = [
                self._get_last_record_of_interval(conn, interval)["Jitter"]
                for conn in connections
            ]
            ltds = [
                self._get_last_record_of_interval(conn, interval)[
                    "Lost_vs_Total_Datagrams"
                ]
                for conn in connections
            ]

            jitter_unit = jitters[0].split()[1]  # 'Jitter': '0.821 ms'
            jitter_values = [float(jit.split()[0]) for jit in jitters]

            lost_datagrams = sum([lost for lost, _ in ltds])
            total_datagrams = sum([total for _, total in ltds])

        elif self.protocol == "udp" and self.client:
            pass

        # 'Transfer Raw': '122 KBytes',
        raw_transfer_unit = raw_transfers[0].split()[1]
        raw_transfer_values = [float(raw_trf.split()[0])
                               for raw_trf in raw_transfers]

        # 'Bitrate Raw': '1000 Kbits/sec'
        raw_bitrate_unit = raw_bitrates[0].split()[1]
        raw_bitrate_values = [float(raw_bw.split()[0])
                              for raw_bw in raw_bitrates]

        sum_record = {
            "Interval": interval,
            "Transfer": sum(transfers),
            "Transfer Raw": "{} {}".format(sum(raw_transfer_values), raw_transfer_unit),
            "Bitrate": sum(bitrates),
            "Bitrate Raw": "{} {}".format(sum(raw_bitrate_values), raw_bitrate_unit),
        }

        # if self.protocol == 'tcp' and self.client:
        #     sum_record['Retr'] = "1000000000000"

        if self.protocol == "udp":
            # noinspection PyUnboundLocalVariable
            sum_record["Jitter"] = "{} {}".format(
                max(jitter_values), jitter_unit)
            # noinspection PyUnboundLocalVariable
            sum_record["Lost_vs_Total_Datagrams"] = (
                lost_datagrams, total_datagrams)
            sum_record["Lost_Datagrams_ratio"] = "{:.2f}%".format(
                lost_datagrams * 100 / total_datagrams
            )

        # print("!"*60)
        # print(sum_record)
        # print("!"*60)

        from_client = "multiport@{}".format(client_host)
        sum_connection_name = (from_client, server)
        self._update_current_ret(sum_connection_name, sum_record)
        self.notify_subscribers(
            from_client=from_client, to_server=server, data_record=sum_record
        )

    def _parse_final_record(self, connection_name, line):
        if self.parallel_client and ("multiport" not in connection_name[0]):
            return  # for parallel we take report / publish stats only from summary records
        last_record = self.current_ret["CONNECTIONS"][connection_name][-1]
        # print(self.server, self.client)

        if self._is_final_record(last_record, line):
            (
                client_host,
                client_port,
                server_host,
                server_port,
            ) = self._split_connection_name(connection_name)
            from_client, to_server = client_host, "{}@{}".format(
                server_port, server_host
            )
            result_connection = (from_client, to_server)
            # print("?" * 50)
            # print(last_record)
            # print("?" * 50)
            self.current_ret["CONNECTIONS"][result_connection] = {
                "report": last_record}
            self.notify_subscribers(
                from_client=from_client, to_server=to_server, report=last_record
            )
        else:
            # print("!" * 50)
            # print(last_record)
            # print("!" * 50)
            from_client, to_server = connection_name
            self.notify_subscribers(
                from_client=from_client, to_server=to_server, data_record=last_record
            )

    _r_option_report = r"(?P<Option>receiver|sender)"
    _r_rec_tcp_svr_report = r"{}\s+{}".format(_r_rec_tcp_svr, _r_option_report)
    _r_rec_tcp_cli_report = r"{}\s+{}".format(_r_rec_tcp_cli, _r_option_report)
    _r_rec_udp_svr_report = r"{}\s+{}".format(_r_rec_udp_svr, _r_option_report)
    _r_rec_udp_cli_report = r"{}\s+{}".format(_r_rec_udp_cli, _r_option_report)
    _r_rec_tcp_cli_summary_report = r"{}\s+{}".format(
        _r_rec_tcp_cli_summary, _r_option_report
    )

    _re_iperf_record_tcp_svr_report = re.compile(_r_rec_tcp_svr_report)
    _re_iperf_record_tcp_cli_report = re.compile(_r_rec_tcp_cli_report)
    _re_iperf_record_udp_svr_report = re.compile(_r_rec_udp_svr_report)
    _re_iperf_record_udp_cli_report = re.compile(_r_rec_udp_cli_report)
    _re_iperf_record_tcp_cli_summary_report = re.compile(
        _r_rec_tcp_cli_summary_report)

    def _is_final_record(self, last_record, line):
        # start, end = last_record['Interval']
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
        (
            client_host,
            client_port,
            server_host,
            server_port,
        ) = self._split_connection_name(connections[0])
        from_client, to_server = client_host, "{}@{}".format(
            self.port, server_host)
        has_client_report = (from_client, to_server) in result
        if self.works_in_dualtest:  # need two reports
            from_server, to_client = server_host, "{}@{}".format(
                self.port, client_host)
            has_server_report = (from_server, to_client) in result
            all_reports = has_client_report and has_server_report
            works_as_client = True  # in dualtest both server and client work as client
        else:
            all_reports = has_client_report
            works_as_client = self.client
        # udp client additionally awaits server report
        if self.protocol == "udp" and works_as_client:
            all_reports = all_reports and self._got_server_report
        return all_reports

    # [  5] Sent 2552 datagrams
    # ------------------------------------------------------------
    _re_ornaments = re.compile(
        r"(?P<ORNAMENTS>----*|\[\s*ID\].*)", re.IGNORECASE)
    _re_summary_ornament = re.compile(r"(?P<SUM_ORNAMENT>(-\s)+)")
    _re_blank_line = re.compile(r"(?P<BLANK>^\s*$)")

    def _parse_connection_headers(self, line):
        if not self._regex_helper.search_compiled(Iperf3._re_ornaments, line) and \
           not self._regex_helper.search_compiled(Iperf3._re_summary_ornament, line) and \
           not self._regex_helper.search_compiled(Iperf3._re_blank_line, line):
            self.current_ret["INFO"].append(line.strip())
            raise ParsingDone

    def _parse_svr_report_header(self, line):
        if "Server Report:" in line:
            self._got_server_report_hdr = True
            raise ParsingDone

    def _normalize_to_bytes(self, input_dict):
        new_dict = {}
        for key, raw_value in input_dict.items():
            if (
                "Bytes" in raw_value
            ):  # iperf MBytes means 1024 * 1024 Bytes - see iperf.fr/iperf-doc.php
                new_dict[key + " Raw"] = raw_value
                value_in_bytes, _, _ = self._converter_helper.to_bytes(
                    raw_value)
                new_dict[key] = value_in_bytes
            elif (
                "bits" in raw_value
            ):  # iperf Mbits means 1000 * 1000 bits - see iperf.fr/iperf-doc.php
                new_dict[key + " Raw"] = raw_value
                value_in_bits, _, _ = self._converter_helper.to_bytes(
                    raw_value, binary_multipliers=False
                )
                value_in_bytes = value_in_bits // 8
                new_dict[key] = value_in_bytes
            else:
                new_dict[key] = raw_value
        return new_dict

    # ^CWaiting for server threads to complete. Interrupt again to force quit
    _re_interrupt_again = re.compile(r"Interrupt again to force quit")

    def _parse_too_early_ctrl_c(self, line):
        # Happens at script execution. Scripts are quicker then humans.
        if self._regex_helper.search_compiled(Iperf3._re_interrupt_again, line):
            self.break_cmd()  # send Ctrl-C once more
            raise ParsingDone


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
                                                      'Bitrate Raw': '25.0 '
                                                      'Gbits/sec',
                                                      'Interval': (0.0,
                                                                     10.0),
                                                      'Retr': '0',
                                                      'Transfer': 31245887078,
                                                      'Transfer Raw': '29.1 '
                                                      'GBytes'}},
         ('48058@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 3400000000,
                                                  'Bitrate Raw': '27.2 '
                                                 'Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 '
                                                  'MBytes',
                                                  'Interval': (0.0,
                                                               1.0),
                                                  'Retr': '0',
                                                  'Transfer': 3393024163,
                                                  'Transfer Raw': '3.16 '
                                                  'GBytes'},
                                                 {'Bitrate': 4475000000,
                                                 'Bitrate Raw': '35.8 '
                                                  'Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 '
                                                  'MBytes',
                                                  'Interval': (1.0,
                                                               2.0),
                                                  'Retr': '0',
                                                  'Transfer': 4477503406,
                                                  'Transfer Raw': '4.17 '
                                                  'GBytes'},
                                                 {'Bitrate': 2575000000,
                                                 'Bitrate Raw': '20.6 '
                                                  'Gbits/sec',
                                                  'Cwnd': 1310720,
                                                  'Cwnd Raw': '1.25 '
                                                  'MBytes',
                                                  'Interval': (2.0,
                                                               3.0),
                                                  'Retr': '0',
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 '
                                                  'GBytes'},
                                                 {'Bitrate': 2575000000,
                                                 'Bitrate Raw': '20.6 '
                                                  'Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 '
                                                  'MBytes',
                                                  'Interval': (3.0,
                                                               4.0),
                                                  'Retr': '0',
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 '
                                                  'GBytes'},
                                                 {'Bitrate': 2525000000,
                                                 'Bitrate Raw': '20.2 '
                                                  'Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 '
                                                  'MBytes',
                                                  'Interval': (4.0,
                                                               5.0),
                                                  'Retr': '0',
                                                  'Transfer': 2534030704,
                                                  'Transfer Raw': '2.36 '
                                                  'GBytes'},
                                                 {'Bitrate': 2575000000,
                                                 'Bitrate Raw': '20.6 '
                                                  'Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 '
                                                  'MBytes',
                                                  'Interval': (5.0,
                                                               6.0),
                                                  'Retr': '0',
                                                  'Transfer': 2576980377,
                                                  'Transfer Raw': '2.40 '
                                                  'GBytes'},
                                                 {'Bitrate': 2587500000,
                                                 'Bitrate Raw': '20.7 '
                                                  'Gbits/sec',
                                                  'Cwnd': 3334471,
                                                  'Cwnd Raw': '3.18 '
                                                  'MBytes',
                                                  'Interval': (6.0,
                                                               7.0),
                                                  'Retr': '0',
                                                  'Transfer': 2587717795,
                                                  'Transfer Raw': '2.41 '
                                                  'GBytes'},
                                                 {'Bitrate': 2550000000,
                                                 'Bitrate Raw': '20.4 '
                                                  'Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 '
                                                  'MBytes',
                                                  'Interval': (7.0,
                                                               8.0),
                                                  'Retr': '0',
                                                  'Transfer': 2544768122,
                                                  'Transfer Raw': '2.37 '
                                                  'GBytes'},
                                                 {'Bitrate': 4175000000,
                                                 'Bitrate Raw': '33.4 '
                                                  'Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 '
                                                  'MBytes',
                                                  'Interval': (8.0,
                                                               9.0),
                                                  'Retr': '0',
                                                  'Transfer': 4176855695,
                                                  'Transfer Raw': '3.89 '
                                                  'GBytes'},
                                                 {'Bitrate': 3825000000,
                                                 'Bitrate Raw': '30.6 '
                                                  'Gbits/sec',
                                                  'Cwnd': 5043650,
                                                  'Cwnd Raw': '4.81 '
                                                  'MBytes',
                                                  'Interval': (9.0,
                                                               10.0),
                                                  'Retr': '0',
                                                  'Transfer': 3822520893,
                                                  'Transfer Raw': '3.56 '
                                                  'GBytes'},
                                                 {'Bitrate': 3125000000,
                                                 'Bitrate Raw': '25.0 '
                                                  'Gbits/sec',
                                                  'Interval': (0.0,
                                                               10.0),
                                                  'Retr': '0',
                                                  'Transfer': 31245887078,
                                                  'Transfer Raw': '29.1 '
                                                  'GBytes'},
                                                 {'Bitrate': 3112500000,
                                                 'Bitrate Raw': '24.9 '
                                                  'Gbits/sec',
                                                  'Interval': (0.0,
                                                               10.05),
                                                  'Transfer': 31245887078,
                                                  'Transfer Raw': '29.1 '
                                                  'GBytes'}]},
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
                                                     'Bitrate Raw': '1.05 '
                                                     'Mbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Jitter': '0.022 '
                                                     'ms',
                                                     'Lost_Datagrams_ratio': '0%',
                                                     'Lost_vs_Total_Datagrams': (0,
                                                                                 60),
                                                     'Transfer': 1321205,
                                                     'Transfer Raw': '1.26 '
                                                     'MBytes'}},
        ('34761@127.0.0.1', '5201@127.0.0.1'): [{'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Jitter': '0.015 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Jitter': '0.016 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Jitter': '0.019 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Jitter': '0.028 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Jitter': '0.024 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Jitter': '0.032 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Jitter': '0.027 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Jitter': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Jitter': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 132500,
                                                 'Bitrate Raw': '1.06 '
                                                 'Mbits/sec',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Jitter': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             6),
                                                 'Transfer': 132096,
                                                 'Transfer Raw': '129 '
                                                 'KBytes'},
                                                {'Bitrate': 131250,
                                                 'Bitrate Raw': '1.05 '
                                                 'Mbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Jitter': '0.022 ms',
                                                 'Lost_Datagrams_ratio': '0%',
                                                 'Lost_vs_Total_Datagrams': (0,
                                                                             60),
                                                 'Transfer': 1321205,
                                                 'Transfer Raw': '1.26 '
                                                 'MBytes'}]},
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
                                                     'Bitrate Raw': '22.0 '
                                                     'Gbits/sec',
                                                     'Interval': (0.0,
                                                                  10.04),
                                                     'Transfer': 27595164876,
                                                     'Transfer Raw': '25.7 '
                                                     'GBytes'}},
        ('37988@127.0.0.1', '5901@127.0.0.1'): [{'Bitrate': 2425000000,
                                                 'Bitrate Raw': '19.4 '
                                                 'Gbits/sec',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Transfer': 2426656522,
                                                 'Transfer Raw': '2.26 '
                                                 'GBytes'},
                                                {'Bitrate': 2675000000,
                                                 'Bitrate Raw': '21.4 '
                                                 'Gbits/sec',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Transfer': 2673617141,
                                                 'Transfer Raw': '2.49 '
                                                 'GBytes'},
                                                {'Bitrate': 2587500000,
                                                 'Bitrate Raw': '20.7 '
                                                 'Gbits/sec',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Transfer': 2587717795,
                                                 'Transfer Raw': '2.41 '
                                                 'GBytes'},
                                                {'Bitrate': 2687500000,
                                                 'Bitrate Raw': '21.5 '
                                                 'Gbits/sec',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Transfer': 2695091978,
                                                 'Transfer Raw': '2.51 '
                                                 'GBytes'},
                                                {'Bitrate': 3212500000,
                                                 'Bitrate Raw': '25.7 '
                                                 'Gbits/sec',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Transfer': 3210488053,
                                                 'Transfer Raw': '2.99 '
                                                 'GBytes'},
                                                {'Bitrate': 2700000000,
                                                 'Bitrate Raw': '21.6 '
                                                 'Gbits/sec',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Transfer': 2705829396,
                                                 'Transfer Raw': '2.52 '
                                                 'GBytes'},
                                                {'Bitrate': 2712500000,
                                                 'Bitrate Raw': '21.7 '
                                                 'Gbits/sec',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Transfer': 2705829396,
                                                 'Transfer Raw': '2.52 '
                                                 'GBytes'},
                                                {'Bitrate': 2687500000,
                                                 'Bitrate Raw': '21.5 '
                                                 'Gbits/sec',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Transfer': 2684354560,
                                                 'Transfer Raw': '2.50 '
                                                 'GBytes'},
                                                {'Bitrate': 2737500000,
                                                 'Bitrate Raw': '21.9 '
                                                 'Gbits/sec',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Transfer': 2727304232,
                                                 'Transfer Raw': '2.54 '
                                                 'GBytes'},
                                                {'Bitrate': 3100000000,
                                                 'Bitrate Raw': '24.8 '
                                                 'Gbits/sec',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Transfer': 3103113871,
                                                 'Transfer Raw': '2.89 '
                                                 'GBytes'},
                                                {'Bitrate': 1800000000,
                                                 'Bitrate Raw': '14.4 '
                                                 'Gbits/sec',
                                                 'Interval': (10.0,
                                                              10.04),
                                                 'Transfer': 74658611,
                                                 'Transfer Raw': '71.2 '
                                                 'MBytes'},
                                                {'Bitrate': 2750000000,
                                                 'Bitrate Raw': '22.0 '
                                                 'Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 27595164876,
                                                 'Transfer Raw': '25.7 '
                                                 'GBytes'}]},
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
xyz@debian:~$ iperf3 -c ::ffff:127.0.0.1 -V -p 5019 -i 1
iperf 3.6
Linux debian
Control connection MSS 22016
Time: Thu, 27 Jul 2023 07:33:51 GMT
Connecting to host ::ffff:127.0.0.1, port 5019
      Cookie: abcd
      TCP MSS: 22016 (default)
[  5] local 127.0.0.1 port 45616 connected to 127.0.0.1 port 5019
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
    "options": "-c ::ffff:127.0.0.1 -V -p 5019 -i 1"}

COMMAND_RESULT_tcp_ipv6_client = {
    'CONNECTIONS': {
        ('127.0.0.1', '5019@127.0.0.1'): {'report': {'Bitrate': 3225000000,
                                                     'Bitrate Raw': '25.8 '
                                                     'Gbits/sec',
                                                     'Interval': (0.0,
                                                                  10.0),
                                                     'Retr': '0',
                                                     'Transfer': 32319628902,
                                                     'Transfer Raw': '30.1 '
                                                     'GBytes'}},
        ('45616@127.0.0.1', '5019@127.0.0.1'): [{'Bitrate': 4025000000,
                                                'Bitrate Raw': '32.2 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1247805,
                                                 'Cwnd Raw': '1.19 '
                                                 'MBytes',
                                                 'Interval': (0.0,
                                                              1.0),
                                                 'Retr': '0',
                                                 'Transfer': 4026531840,
                                                 'Transfer Raw': '3.75 '
                                                 'GBytes'},
                                                {'Bitrate': 2825000000,
                                                'Bitrate Raw': '22.6 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1247805,
                                                 'Cwnd Raw': '1.19 '
                                                 'MBytes',
                                                 'Interval': (1.0,
                                                              2.0),
                                                 'Retr': '0',
                                                 'Transfer': 2823940997,
                                                 'Transfer Raw': '2.63 '
                                                 'GBytes'},
                                                {'Bitrate': 2962500000,
                                                'Bitrate Raw': '23.7 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 '
                                                 'MBytes',
                                                 'Interval': (2.0,
                                                              3.0),
                                                 'Retr': '0',
                                                 'Transfer': 2963527434,
                                                 'Transfer Raw': '2.76 '
                                                 'GBytes'},
                                                {'Bitrate': 2687500000,
                                                'Bitrate Raw': '21.5 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 '
                                                 'MBytes',
                                                 'Interval': (3.0,
                                                              4.0),
                                                 'Retr': '0',
                                                 'Transfer': 2695091978,
                                                 'Transfer Raw': '2.51 '
                                                 'GBytes'},
                                                {'Bitrate': 2725000000,
                                                'Bitrate Raw': '21.8 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 '
                                                 'MBytes',
                                                 'Interval': (4.0,
                                                              5.0),
                                                 'Retr': '0',
                                                 'Transfer': 2716566814,
                                                 'Transfer Raw': '2.53 '
                                                 'GBytes'},
                                                {'Bitrate': 2637500000,
                                                'Bitrate Raw': '21.1 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 '
                                                 'MBytes',
                                                 'Interval': (5.0,
                                                              6.0),
                                                 'Retr': '0',
                                                 'Transfer': 2641404887,
                                                 'Transfer Raw': '2.46 '
                                                 'GBytes'},
                                                {'Bitrate': 2662500000,
                                                'Bitrate Raw': '21.3 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 '
                                                 'MBytes',
                                                 'Interval': (6.0,
                                                              7.0),
                                                 'Retr': '0',
                                                 'Transfer': 2662879723,
                                                 'Transfer Raw': '2.48 '
                                                 'GBytes'},
                                                {'Bitrate': 3737500000,
                                                'Bitrate Raw': '29.9 '
                                                 'Gbits/sec',
                                                 'Cwnd': 1436549,
                                                 'Cwnd Raw': '1.37 '
                                                 'MBytes',
                                                 'Interval': (7.0,
                                                              8.0),
                                                 'Retr': '0',
                                                 'Transfer': 3736621547,
                                                 'Transfer Raw': '3.48 '
                                                 'GBytes'},
                                                {'Bitrate': 2962500000,
                                                'Bitrate Raw': '23.7 '
                                                 'Gbits/sec',
                                                 'Cwnd': 2160066,
                                                 'Cwnd Raw': '2.06 '
                                                 'MBytes',
                                                 'Interval': (8.0,
                                                              9.0),
                                                 'Retr': '0',
                                                 'Transfer': 2963527434,
                                                 'Transfer Raw': '2.76 '
                                                 'GBytes'},
                                                {'Bitrate': 5062500000,
                                                'Bitrate Raw': '40.5 '
                                                 'Gbits/sec',
                                                 'Cwnd': 2160066,
                                                 'Cwnd Raw': '2.06 '
                                                 'MBytes',
                                                 'Interval': (9.0,
                                                              10.0),
                                                 'Retr': '0',
                                                 'Transfer': 5057323991,
                                                 'Transfer Raw': '4.71 '
                                                 'GBytes'},
                                                {'Bitrate': 3225000000,
                                                'Bitrate Raw': '25.8 '
                                                 'Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.0),
                                                 'Retr': '0',
                                                 'Transfer': 32319628902,
                                                 'Transfer Raw': '30.1 '
                                                 'GBytes'},
                                                {'Bitrate': 3212500000,
                                                'Bitrate Raw': '25.7 '
                                                 'Gbits/sec',
                                                 'Interval': (0.0,
                                                              10.04),
                                                 'Transfer': 32319628902,
                                                 'Transfer Raw': '30.1 '
                                                 'GBytes'}]},
    'INFO': ['iperf 3.6',
             'Linux debian',
             'Control connection MSS 22016',
             'Time: Thu, 27 Jul 2023 07:33:51 GMT',
             'Connecting to host ::ffff:127.0.0.1, port 5019',
             'Cookie: abcd',
             'TCP MSS: 22016 (default)',
             'Starting Test: protocol: TCP, 1 streams, 131072 byte blocks, omitting 0 seconds, 10 second test, tos 0',
             'Test Complete. Summary Results:',
             'CPU Utilization: local/sender 97.2% (1.9%u/95.3%s), remote/receiver 64.2% (3.4%u/60.8%s)',
             'snd_tcp_congestion cubic',
             'rcv_tcp_congestion cubic',
             'iperf Done.']}


# COMMAND_OUTPUT_bidirectional_udp_client = """
# abc@debian:~$ iperf -c 192.168.0.12 -u -p 5016 -f k -i 1.0 -t 6.0 --dualtest -b 5000.0k
# ------------------------------------------------------------
# Server listening on UDP port 5016
# Receiving 1470 byte datagrams
# UDP buffer size: 1024 KByte (default)
# ------------------------------------------------------------
# ------------------------------------------------------------
# Client connecting to 192.168.0.12, UDP port 5016
# Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)
# UDP buffer size: 1024 KByte (default)
# ------------------------------------------------------------
# [  4] local 192.168.0.10 port 56262 connected with 192.168.0.12 port 5016
# [  3] local 192.168.0.10 port 5016 connected with 192.168.0.12 port 47384
# [ ID] Interval       Transfer     Bandwidth
# [  4]  0.0- 1.0 sec   613 KBytes  5022 Kbits/sec
# [  3]  0.0- 1.0 sec   612 KBytes  5010 Kbits/sec   0.011 ms    0/  426 (0%)
# [  4]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec   0.012 ms    0/  425 (0%)
# [  4]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec   0.017 ms    0/  425 (0%)
# [  4]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec   0.019 ms    0/  425 (0%)
# [  4]  4.0- 5.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  4.0- 5.0 sec   610 KBytes  4998 Kbits/sec   0.014 ms    0/  425 (0%)
# [  4]  5.0- 6.0 sec   610 KBytes  4998 Kbits/sec
# [  4]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec
# [  4] Sent 2552 datagrams
# [  3]  5.0- 6.0 sec   612 KBytes  5010 Kbits/sec   0.017 ms    0/  426 (0%)
# [  3]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.017 ms    0/ 2552 (0%)
# [  4] Server Report:
# [  4]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.017 ms    0/ 2552 (0%)
# abc@debian:~$"""


# COMMAND_KWARGS_bidirectional_udp_client = {
#     "options": "-c 192.168.0.12 -u -p 5016 -f k -i 1.0 -t 6.0 --dualtest -b 5000.0k"
# }


# COMMAND_RESULT_bidirectional_udp_client = {
#     "CONNECTIONS": {
#         ("56262@192.168.0.10", "5016@192.168.0.12"): [
#             {
#                 "Transfer": 627712,
#                 "Bandwidth": 627750,
#                 "Transfer Raw": "613 KBytes",
#                 "Bandwidth Raw": "5022 Kbits/sec",
#                 "Interval": (0.0, 1.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (1.0, 2.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (2.0, 3.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (3.0, 4.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (4.0, 5.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (5.0, 6.0),
#             },
#             {
#                 "Transfer": 3751936,
#                 "Bandwidth": 625000,
#                 "Transfer Raw": "3664 KBytes",
#                 "Bandwidth Raw": "5000 Kbits/sec",
#                 "Interval": (0.0, 6.0),
#             },
#             {
#                 "Transfer Raw": "3664 KBytes",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             },
#         ],
#         ("47384@192.168.0.12", "5016@192.168.0.10"): [
#             {
#                 "Transfer Raw": "612 KBytes",
#                 "Jitter": "0.011 ms",
#                 "Transfer": 626688,
#                 "Interval": (0.0, 1.0),
#                 "Bandwidth": 626250,
#                 "Lost_vs_Total_Datagrams": (0, 426),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5010 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.012 ms",
#                 "Transfer": 624640,
#                 "Interval": (1.0, 2.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 624640,
#                 "Interval": (2.0, 3.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.019 ms",
#                 "Transfer": 624640,
#                 "Interval": (3.0, 4.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.014 ms",
#                 "Transfer": 624640,
#                 "Interval": (4.0, 5.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "612 KBytes",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 626688,
#                 "Interval": (5.0, 6.0),
#                 "Bandwidth": 626250,
#                 "Lost_vs_Total_Datagrams": (0, 426),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5010 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "3664 KBytes",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             },
#         ],
#         ("192.168.0.10", "5016@192.168.0.12"): {
#             "report": {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Transfer Raw": "3664 KBytes",
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             }
#         },
#         ("192.168.0.12", "5016@192.168.0.10"): {
#             "report": {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Transfer Raw": "3664 KBytes",
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             }
#         },
#     },
#     "INFO": [
#         "Server listening on UDP port 5016",
#         "Receiving 1470 byte datagrams",
#         "UDP buffer size: 1024 KByte (default)",
#         "Client connecting to 192.168.0.12, UDP port 5016",
#         "Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)",
#         "UDP buffer size: 1024 KByte (default)",
#         "[  4] Sent 2552 datagrams",
#     ],
# }


# COMMAND_OUTPUT_bidirectional_udp_server = """
# xyz@debian:~$ iperf -s -u -p 5016 -f k -i 1.0
# ------------------------------------------------------------
# Server listening on UDP port 5016
# Receiving 1470 byte datagrams
# UDP buffer size: 1024 KByte (default)
# ------------------------------------------------------------
# [  3] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 56262
# ------------------------------------------------------------
# Client connecting to 192.168.0.10, UDP port 5016
# Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)
# UDP buffer size: 1024 KByte (default)
# ------------------------------------------------------------
# [  5] local 192.168.0.12 port 47384 connected with 192.168.0.10 port 5016
# [ ID] Interval       Transfer     Bandwidth        Jitter   Lost/Total Datagrams
# [  3]  0.0- 1.0 sec   612 KBytes  5010 Kbits/sec   0.022 ms    0/  426 (0%)
# [  5]  0.0- 1.0 sec   613 KBytes  5022 Kbits/sec
# [  3]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec   0.016 ms    0/  425 (0%)
# [  5]  1.0- 2.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec   0.021 ms    0/  425 (0%)
# [  5]  2.0- 3.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec   0.009 ms    0/  425 (0%)
# [  5]  3.0- 4.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  4.0- 5.0 sec   612 KBytes  5010 Kbits/sec   0.014 ms    0/  426 (0%)
# [  5]  4.0- 5.0 sec   610 KBytes  4998 Kbits/sec
# [  3]  5.0- 6.0 sec   610 KBytes  4998 Kbits/sec   0.018 ms    0/  425 (0%)
# [  3]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.018 ms    0/ 2552 (0%)
# [  5]  5.0- 6.0 sec   610 KBytes  4998 Kbits/sec
# [  5]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec
# [  5] Sent 2552 datagrams
# [  5] Server Report:
# [  5]  0.0- 6.0 sec  3664 KBytes  5000 Kbits/sec   0.017 ms    0/ 2552 (0%)
# xyz@debian:~$"""


# COMMAND_KWARGS_bidirectional_udp_server = {
#     "options": "-s -u -p 5016 -f k -i 1.0"}


# COMMAND_RESULT_bidirectional_udp_server = {
#     "CONNECTIONS": {
#         ("47384@192.168.0.12", "5016@192.168.0.10"): [
#             {
#                 "Transfer": 627712,
#                 "Bandwidth": 627750,
#                 "Transfer Raw": "613 KBytes",
#                 "Bandwidth Raw": "5022 Kbits/sec",
#                 "Interval": (0.0, 1.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (1.0, 2.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (2.0, 3.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (3.0, 4.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (4.0, 5.0),
#             },
#             {
#                 "Transfer": 624640,
#                 "Bandwidth": 624750,
#                 "Transfer Raw": "610 KBytes",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#                 "Interval": (5.0, 6.0),
#             },
#             {
#                 "Transfer": 3751936,
#                 "Bandwidth": 625000,
#                 "Transfer Raw": "3664 KBytes",
#                 "Bandwidth Raw": "5000 Kbits/sec",
#                 "Interval": (0.0, 6.0),
#             },
#             {
#                 "Transfer Raw": "3664 KBytes",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             },
#         ],
#         ("56262@192.168.0.10", "5016@192.168.0.12"): [
#             {
#                 "Transfer Raw": "612 KBytes",
#                 "Jitter": "0.022 ms",
#                 "Transfer": 626688,
#                 "Interval": (0.0, 1.0),
#                 "Bandwidth": 626250,
#                 "Lost_vs_Total_Datagrams": (0, 426),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5010 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.016 ms",
#                 "Transfer": 624640,
#                 "Interval": (1.0, 2.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.021 ms",
#                 "Transfer": 624640,
#                 "Interval": (2.0, 3.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.009 ms",
#                 "Transfer": 624640,
#                 "Interval": (3.0, 4.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "612 KBytes",
#                 "Jitter": "0.014 ms",
#                 "Transfer": 626688,
#                 "Interval": (4.0, 5.0),
#                 "Bandwidth": 626250,
#                 "Lost_vs_Total_Datagrams": (0, 426),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5010 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "610 KBytes",
#                 "Jitter": "0.018 ms",
#                 "Transfer": 624640,
#                 "Interval": (5.0, 6.0),
#                 "Bandwidth": 624750,
#                 "Lost_vs_Total_Datagrams": (0, 425),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "4998 Kbits/sec",
#             },
#             {
#                 "Transfer Raw": "3664 KBytes",
#                 "Jitter": "0.018 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Lost_Datagrams_ratio": "0%",
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             },
#         ],
#         ("192.168.0.12", "5016@192.168.0.10"): {
#             "report": {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.017 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Transfer Raw": "3664 KBytes",
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             }
#         },
#         ("192.168.0.10", "5016@192.168.0.12"): {
#             "report": {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.018 ms",
#                 "Transfer": 3751936,
#                 "Interval": (0.0, 6.0),
#                 "Transfer Raw": "3664 KBytes",
#                 "Bandwidth": 625000,
#                 "Lost_vs_Total_Datagrams": (0, 2552),
#                 "Bandwidth Raw": "5000 Kbits/sec",
#             }
#         },
#     },
#     "INFO": [
#         "Server listening on UDP port 5016",
#         "Receiving 1470 byte datagrams",
#         "UDP buffer size: 1024 KByte (default)",
#         "Client connecting to 192.168.0.10, UDP port 5016",
#         "Sending 1470 byte datagrams, IPG target: 2352.00 us (kalman adjust)",
#         "UDP buffer size: 1024 KByte (default)",
#         "[  5] Sent 2552 datagrams",
#     ],
# }


# COMMAND_OUTPUT_multiple_connections = """
# xyz@debian:~$ iperf -c 192.168.0.100 -P 20
# ------------------------------------------------------------
# Client connecting to 192.168.0.100, TCP port 5001
# TCP window size: 16.0 KByte (default)
# ------------------------------------------------------------
# [ 15] local 192.168.0.102 port 57258 connected with 192.168.0.100 port 5001
# [  3] local 192.168.0.102 port 57246 connected with 192.168.0.100 port 5001
# [  4] local 192.168.0.102 port 57247 connected with 192.168.0.100 port 5001
# [  5] local 192.168.0.102 port 57248 connected with 192.168.0.100 port 5001
# [  7] local 192.168.0.102 port 57250 connected with 192.168.0.100 port 5001
# [  6] local 192.168.0.102 port 57249 connected with 192.168.0.100 port 5001
# [ 10] local 192.168.0.102 port 57253 connected with 192.168.0.100 port 5001
# [  8] local 192.168.0.102 port 57251 connected with 192.168.0.100 port 5001
# [  9] local 192.168.0.102 port 57252 connected with 192.168.0.100 port 5001
# [ 16] local 192.168.0.102 port 57259 connected with 192.168.0.100 port 5001
# [ 19] local 192.168.0.102 port 57261 connected with 192.168.0.100 port 5001
# [ 18] local 192.168.0.102 port 57260 connected with 192.168.0.100 port 5001
# [ 20] local 192.168.0.102 port 57262 connected with 192.168.0.100 port 5001
# [ 17] local 192.168.0.102 port 57263 connected with 192.168.0.100 port 5001
# [ 21] local 192.168.0.102 port 57264 connected with 192.168.0.100 port 5001
# [ 11] local 192.168.0.102 port 57254 connected with 192.168.0.100 port 5001
# [ 12] local 192.168.0.102 port 57255 connected with 192.168.0.100 port 5001
# [ 13] local 192.168.0.102 port 57256 connected with 192.168.0.100 port 5001
# [ 14] local 192.168.0.102 port 57257 connected with 192.168.0.100 port 5001
# [ 22] local 192.168.0.102 port 57265 connected with 192.168.0.100 port 5001
# [ ID] Interval       Transfer     Bandwidth
# [  8]  0.0-10.6 sec  16.6 MBytes  13.1 Mbits/sec
# [ 16]  0.0-10.6 sec  16.6 MBytes  13.1 Mbits/sec
# [ 18]  0.0-10.6 sec  16.5 MBytes  13.1 Mbits/sec
# [ 17]  0.0-10.7 sec  16.6 MBytes  13.0 Mbits/sec
# [ 21]  0.0-10.7 sec  15.6 MBytes  12.3 Mbits/sec
# [ 12]  0.0-10.7 sec  17.5 MBytes  13.7 Mbits/sec
# [ 22]  0.0-10.7 sec  16.6 MBytes  13.0 Mbits/sec
# [ 15]  0.0-10.8 sec  17.8 MBytes  13.8 Mbits/sec
# [  3]  0.0-10.7 sec  18.5 MBytes  14.5 Mbits/sec
# [  4]  0.0-10.8 sec  18.1 MBytes  14.1 Mbits/sec
# [  5]  0.0-10.7 sec  17.6 MBytes  13.9 Mbits/sec
# [  7]  0.0-10.8 sec  18.4 MBytes  14.3 Mbits/sec
# [  6]  0.0-10.8 sec  17.0 MBytes  13.2 Mbits/sec
# [ 10]  0.0-10.8 sec  16.8 MBytes  13.1 Mbits/sec
# [  9]  0.0-10.8 sec  16.8 MBytes  13.0 Mbits/sec
# [ 19]  0.0-10.6 sec  16.5 MBytes  13.0 Mbits/sec
# [ 20]  0.0-10.7 sec  16.5 MBytes  12.9 Mbits/sec
# [ 11]  0.0-10.7 sec  18.0 MBytes  14.0 Mbits/sec
# [ 13]  0.0-10.7 sec  17.8 MBytes  13.9 Mbits/sec
# [ 14]  0.0-10.8 sec  18.2 MBytes  14.1 Mbits/sec
# [SUM]  0.0-10.8 sec   344 MBytes   266 Mbits/sec
# xyz@debian:~$"""

# COMMAND_KWARGS_multiple_connections = {"options": "-c 192.168.0.100 -P 20"}

# COMMAND_RESULT_multiple_connections = {
#     "CONNECTIONS": {
#         ("57246@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "14.5 Mbits/sec",
#                 "Bandwidth": 1812500,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "18.5 MBytes",
#                 "Transfer": 19398656,
#             }
#         ],
#         ("57247@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "14.1 Mbits/sec",
#                 "Bandwidth": 1762500,
#                 "Interval": (0.0, 10.8),
#                 "Transfer Raw": "18.1 MBytes",
#                 "Transfer": 18979225,
#             }
#         ],
#         ("57248@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.9 Mbits/sec",
#                 "Bandwidth": 1737500,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "17.6 MBytes",
#                 "Transfer": 18454937,
#             }
#         ],
#         ("57249@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.2 Mbits/sec",
#                 "Bandwidth": 1650000,
#                 "Interval": (0.0, 10.8),
#                 "Transfer Raw": "17.0 MBytes",
#                 "Transfer": 17825792,
#             }
#         ],
#         ("57250@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "14.3 Mbits/sec",
#                 "Bandwidth": 1787500,
#                 "Interval": (0.0, 10.8),
#                 "Transfer Raw": "18.4 MBytes",
#                 "Transfer": 19293798,
#             }
#         ],
#         ("57251@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.1 Mbits/sec",
#                 "Bandwidth": 1637500,
#                 "Interval": (0.0, 10.6),
#                 "Transfer Raw": "16.6 MBytes",
#                 "Transfer": 17406361,
#             }
#         ],
#         ("57252@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.0 Mbits/sec",
#                 "Bandwidth": 1625000,
#                 "Interval": (0.0, 10.8),
#                 "Transfer Raw": "16.8 MBytes",
#                 "Transfer": 17616076,
#             }
#         ],
#         ("57253@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.1 Mbits/sec",
#                 "Bandwidth": 1637500,
#                 "Interval": (0.0, 10.8),
#                 "Transfer Raw": "16.8 MBytes",
#                 "Transfer": 17616076,
#             }
#         ],
#         ("57254@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "14.0 Mbits/sec",
#                 "Bandwidth": 1750000,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "18.0 MBytes",
#                 "Transfer": 18874368,
#             }
#         ],
#         ("57255@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.7 Mbits/sec",
#                 "Bandwidth": 1712500,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "17.5 MBytes",
#                 "Transfer": 18350080,
#             }
#         ],
#         ("57256@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.9 Mbits/sec",
#                 "Bandwidth": 1737500,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "17.8 MBytes",
#                 "Transfer": 18664652,
#             }
#         ],
#         ("57257@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "14.1 Mbits/sec",
#                 "Bandwidth": 1762500,
#                 "Interval": (0.0, 10.8),
#                 "Transfer Raw": "18.2 MBytes",
#                 "Transfer": 19084083,
#             }
#         ],
#         ("57258@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.8 Mbits/sec",
#                 "Bandwidth": 1725000,
#                 "Interval": (0.0, 10.8),
#                 "Transfer Raw": "17.8 MBytes",
#                 "Transfer": 18664652,
#             }
#         ],
#         ("57259@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.1 Mbits/sec",
#                 "Bandwidth": 1637500,
#                 "Interval": (0.0, 10.6),
#                 "Transfer Raw": "16.6 MBytes",
#                 "Transfer": 17406361,
#             }
#         ],
#         ("57260@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.1 Mbits/sec",
#                 "Bandwidth": 1637500,
#                 "Interval": (0.0, 10.6),
#                 "Transfer Raw": "16.5 MBytes",
#                 "Transfer": 17301504,
#             }
#         ],
#         ("57261@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.0 Mbits/sec",
#                 "Bandwidth": 1625000,
#                 "Interval": (0.0, 10.6),
#                 "Transfer Raw": "16.5 MBytes",
#                 "Transfer": 17301504,
#             }
#         ],
#         ("57262@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "12.9 Mbits/sec",
#                 "Bandwidth": 1612500,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "16.5 MBytes",
#                 "Transfer": 17301504,
#             }
#         ],
#         ("57263@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.0 Mbits/sec",
#                 "Bandwidth": 1625000,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "16.6 MBytes",
#                 "Transfer": 17406361,
#             }
#         ],
#         ("57264@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "12.3 Mbits/sec",
#                 "Bandwidth": 1537500,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "15.6 MBytes",
#                 "Transfer": 16357785,
#             }
#         ],
#         ("57265@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Bandwidth Raw": "13.0 Mbits/sec",
#                 "Bandwidth": 1625000,
#                 "Interval": (0.0, 10.7),
#                 "Transfer Raw": "16.6 MBytes",
#                 "Transfer": 17406361,
#             }
#         ],
#         ("multiport@192.168.0.102", "5001@192.168.0.100"): [
#             {
#                 "Transfer": 360710144,
#                 "Bandwidth": 33250000,
#                 "Transfer Raw": "344 MBytes",
#                 "Bandwidth Raw": "266 Mbits/sec",
#                 "Interval": (0.0, 10.8),
#             }
#         ],
#         ("192.168.0.102", "5001@192.168.0.100"): {
#             "report": {
#                 "Transfer": 360710144,
#                 "Bandwidth": 33250000,
#                 "Transfer Raw": "344 MBytes",
#                 "Bandwidth Raw": "266 Mbits/sec",
#                 "Interval": (0.0, 10.8),
#             }
#         },
#     },
#     "INFO": [
#         "Client connecting to 192.168.0.100, TCP port 5001",
#         "TCP window size: 16.0 KByte (default)",
#     ],
# }


# COMMAND_OUTPUT_multiple_connections_server = """
# xyz@debian:~$ iperf -s -p 5016 -f k
# ------------------------------------------------------------
# Server listening on TCP port 5016
# TCP window size: 85.3 KByte (default)
# ------------------------------------------------------------
# [  4] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 42520
# [  5] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 42522
# [  6] local 192.168.0.12 port 5016 connected with 192.168.0.10 port 42524
# [ ID] Interval       Transfer     Bandwidth
# [  4]  0.0- 5.0 sec  2398848 KBytes  3926238 Kbits/sec
# [  5]  0.0- 5.0 sec  2160256 KBytes  3535024 Kbits/sec
# [  6]  0.0- 5.0 sec  2361856 KBytes  3864920 Kbits/sec
# [SUM]  0.0- 5.0 sec  6920960 KBytes  11325398 Kbits/sec
# xyz@debian:~$"""

# COMMAND_KWARGS_multiple_connections_server = {"options": "-s -p 5016 -f k"}

# COMMAND_RESULT_multiple_connections_server = {
#     "CONNECTIONS": {
#         ("42520@192.168.0.10", "5016@192.168.0.12"): [
#             {
#                 "Transfer": 2456420352,
#                 "Bandwidth": 490779750,
#                 "Transfer Raw": "2398848 KBytes",
#                 "Bandwidth Raw": "3926238 Kbits/sec",
#                 "Interval": (0.0, 5.0),
#             }
#         ],
#         ("42524@192.168.0.10", "5016@192.168.0.12"): [
#             {
#                 "Transfer": 2418540544,
#                 "Bandwidth": 483115000,
#                 "Transfer Raw": "2361856 KBytes",
#                 "Bandwidth Raw": "3864920 Kbits/sec",
#                 "Interval": (0.0, 5.0),
#             }
#         ],
#         ("42522@192.168.0.10", "5016@192.168.0.12"): [
#             {
#                 "Transfer": 2212102144,
#                 "Bandwidth": 441878000,
#                 "Transfer Raw": "2160256 KBytes",
#                 "Bandwidth Raw": "3535024 Kbits/sec",
#                 "Interval": (0.0, 5.0),
#             }
#         ],
#         ("multiport@192.168.0.10", "5016@192.168.0.12"): [
#             {
#                 "Transfer": 7087063040,
#                 "Bandwidth": 1415674750,
#                 "Transfer Raw": "6920960 KBytes",
#                 "Bandwidth Raw": "11325398 Kbits/sec",
#                 "Interval": (0.0, 5.0),
#             }
#         ],
#         ("192.168.0.10", "5016@192.168.0.12"): {
#             "report": {
#                 "Transfer": 7087063040,
#                 "Bandwidth": 1415674750,
#                 "Transfer Raw": "6920960 KBytes",
#                 "Bandwidth Raw": "11325398 Kbits/sec",
#                 "Interval": (0.0, 5.0),
#             }
#         },
#     },
#     "INFO": [
#         "Server listening on TCP port 5016",
#         "TCP window size: 85.3 KByte (default)",
#     ],
# }

# COMMAND_OUTPUT_multiple_connections_udp_server = """
# vagrant@app-svr:~$ iperf -s -u -p 5016 -f k -i 1 -P 3
# ------------------------------------------------------------
# Server listening on UDP port 5016
# Receiving 1470 byte datagrams
# UDP buffer size:  208 KByte (default)
# ------------------------------------------------------------
# [  3] local 192.168.44.130 port 5016 connected with 192.168.44.1 port 51914
# [  6] local 192.168.44.130 port 5016 connected with 192.168.44.1 port 51916
# [  4] local 192.168.44.130 port 5016 connected with 192.168.44.1 port 51915
# [ ID] Interval       Transfer     Bandwidth        Jitter   Lost/Total Datagrams
# [  3]  0.0- 1.0 sec   122 KBytes  1000 Kbits/sec   1.556 ms    0/   85 (0%)
# [  6]  0.0- 1.0 sec   122 KBytes  1000 Kbits/sec   1.541 ms    0/   85 (0%)
# [  4]  0.0- 1.0 sec   121 KBytes   988 Kbits/sec   1.464 ms    0/   84 (0%)
# [  3]  1.0- 2.0 sec   123 KBytes  1011 Kbits/sec   0.654 ms    0/   86 (0%)
# [  6]  1.0- 2.0 sec   123 KBytes  1011 Kbits/sec   0.719 ms    0/   86 (0%)
# [  4]  1.0- 2.0 sec   125 KBytes  1023 Kbits/sec   0.565 ms    0/   87 (0%)
# [  3]  2.0- 3.0 sec   121 KBytes   988 Kbits/sec   0.463 ms    0/   84 (0%)
# [  6]  2.0- 3.0 sec   121 KBytes   988 Kbits/sec   0.376 ms    0/   84 (0%)
# [  4]  2.0- 3.0 sec   121 KBytes   988 Kbits/sec   1.191 ms    0/   84 (0%)
# [  3]  3.0- 4.0 sec   123 KBytes  1011 Kbits/sec   0.951 ms    0/   86 (0%)
# [  6]  3.0- 4.0 sec   123 KBytes  1011 Kbits/sec   1.470 ms    0/   86 (0%)
# [  4]  3.0- 4.0 sec   123 KBytes  1011 Kbits/sec   1.225 ms    0/   86 (0%)
# [  6]  4.0- 5.0 sec   122 KBytes  1000 Kbits/sec   1.332 ms    0/   85 (0%)
# [  6]  0.0- 5.0 sec   612 KBytes  1000 Kbits/sec   1.332 ms    0/  426 (0%)
# [  3]  4.0- 5.0 sec   122 KBytes  1000 Kbits/sec   0.821 ms    0/   85 (0%)
# [  3]  0.0- 5.0 sec   612 KBytes  1000 Kbits/sec   0.821 ms    0/  426 (0%)
# [  4]  4.0- 5.0 sec   122 KBytes  1000 Kbits/sec   1.273 ms    0/   85 (0%)
# [  4]  0.0- 5.0 sec   612 KBytes  1000 Kbits/sec   1.273 ms    0/  426 (0%)
# [SUM]  0.0- 5.0 sec  2199 KBytes  3596 Kbits/sec   1.556 ms    0/ 1532 (0%)
# vagrant@app-svr:~$"""

# COMMAND_KWARGS_multiple_connections_udp_server = {
#     "options": "-s -u -p 5016 -f k -i 1 -P 3"
# }

# COMMAND_RESULT_multiple_connections_udp_server = {
#     "CONNECTIONS": {
#         ("51915@192.168.44.1", "5016@192.168.44.130"): [
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.464 ms",
#                 "Transfer": 123904,
#                 "Interval": (0.0, 1.0),
#                 "Transfer Raw": "121 KBytes",
#                 "Bandwidth": 123500,
#                 "Lost_vs_Total_Datagrams": (0, 84),
#                 "Bandwidth Raw": "988 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.565 ms",
#                 "Transfer": 128000,
#                 "Interval": (1.0, 2.0),
#                 "Transfer Raw": "125 KBytes",
#                 "Bandwidth": 127875,
#                 "Lost_vs_Total_Datagrams": (0, 87),
#                 "Bandwidth Raw": "1023 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.191 ms",
#                 "Transfer": 123904,
#                 "Interval": (2.0, 3.0),
#                 "Transfer Raw": "121 KBytes",
#                 "Bandwidth": 123500,
#                 "Lost_vs_Total_Datagrams": (0, 84),
#                 "Bandwidth Raw": "988 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.225 ms",
#                 "Transfer": 125952,
#                 "Interval": (3.0, 4.0),
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth": 126375,
#                 "Lost_vs_Total_Datagrams": (0, 86),
#                 "Bandwidth Raw": "1011 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.273 ms",
#                 "Transfer": 124928,
#                 "Interval": (4.0, 5.0),
#                 "Transfer Raw": "122 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 85),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.273 ms",
#                 "Transfer": 626688,
#                 "Interval": (0.0, 5.0),
#                 "Transfer Raw": "612 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 426),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#         ],
#         ("51916@192.168.44.1", "5016@192.168.44.130"): [
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.541 ms",
#                 "Transfer": 124928,
#                 "Interval": (0.0, 1.0),
#                 "Transfer Raw": "122 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 85),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.719 ms",
#                 "Transfer": 125952,
#                 "Interval": (1.0, 2.0),
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth": 126375,
#                 "Lost_vs_Total_Datagrams": (0, 86),
#                 "Bandwidth Raw": "1011 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.376 ms",
#                 "Transfer": 123904,
#                 "Interval": (2.0, 3.0),
#                 "Transfer Raw": "121 KBytes",
#                 "Bandwidth": 123500,
#                 "Lost_vs_Total_Datagrams": (0, 84),
#                 "Bandwidth Raw": "988 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.470 ms",
#                 "Transfer": 125952,
#                 "Interval": (3.0, 4.0),
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth": 126375,
#                 "Lost_vs_Total_Datagrams": (0, 86),
#                 "Bandwidth Raw": "1011 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.332 ms",
#                 "Transfer": 124928,
#                 "Interval": (4.0, 5.0),
#                 "Transfer Raw": "122 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 85),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.332 ms",
#                 "Transfer": 626688,
#                 "Interval": (0.0, 5.0),
#                 "Transfer Raw": "612 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 426),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#         ],
#         ("51914@192.168.44.1", "5016@192.168.44.130"): [
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.556 ms",
#                 "Transfer": 124928,
#                 "Interval": (0.0, 1.0),
#                 "Transfer Raw": "122 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 85),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.654 ms",
#                 "Transfer": 125952,
#                 "Interval": (1.0, 2.0),
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth": 126375,
#                 "Lost_vs_Total_Datagrams": (0, 86),
#                 "Bandwidth Raw": "1011 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.463 ms",
#                 "Transfer": 123904,
#                 "Interval": (2.0, 3.0),
#                 "Transfer Raw": "121 KBytes",
#                 "Bandwidth": 123500,
#                 "Lost_vs_Total_Datagrams": (0, 84),
#                 "Bandwidth Raw": "988 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.951 ms",
#                 "Transfer": 125952,
#                 "Interval": (3.0, 4.0),
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth": 126375,
#                 "Lost_vs_Total_Datagrams": (0, 86),
#                 "Bandwidth Raw": "1011 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.821 ms",
#                 "Transfer": 124928,
#                 "Interval": (4.0, 5.0),
#                 "Transfer Raw": "122 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 85),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.821 ms",
#                 "Transfer": 626688,
#                 "Interval": (0.0, 5.0),
#                 "Transfer Raw": "612 KBytes",
#                 "Bandwidth": 125000,
#                 "Lost_vs_Total_Datagrams": (0, 426),
#                 "Bandwidth Raw": "1000 Kbits/sec",
#             },
#         ],
#         ("multiport@192.168.44.1", "5016@192.168.44.130"): [
#             {
#                 "Lost_Datagrams_ratio": "0.00%",
#                 "Jitter": "{} ms".format(max(1.464, 1.541, 1.556)),
#                 "Transfer": 123904 + 124928 + 124928,
#                 "Interval": (0.0, 1.0),
#                 "Transfer Raw": "365.0 KBytes",
#                 "Bandwidth": 123500 + 125000 + 125000,
#                 "Lost_vs_Total_Datagrams": (0 + 0 + 0, 84 + 85 + 85),
#                 "Bandwidth Raw": "2988.0 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0.00%",
#                 "Jitter": "{} ms".format(max(0.565, 0.719, 0.654)),
#                 "Transfer": 128000 + 125952 + 125952,
#                 "Interval": (1.0, 2.0),
#                 "Transfer Raw": "371.0 KBytes",
#                 "Bandwidth": 127875 + 126375 + 126375,
#                 "Lost_vs_Total_Datagrams": (0 + 0 + 0, 87 + 86 + 86),
#                 "Bandwidth Raw": "3045.0 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0.00%",
#                 "Jitter": "{} ms".format(max(1.191, 0.376, 0.463)),
#                 "Transfer": 123904 + 123904 + 123904,
#                 "Interval": (2.0, 3.0),
#                 "Transfer Raw": "363.0 KBytes",
#                 "Bandwidth": 123500 + 123500 + 123500,
#                 "Lost_vs_Total_Datagrams": (0 + 0 + 0, 84 + 84 + 84),
#                 "Bandwidth Raw": "2964.0 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0.00%",
#                 "Jitter": "{} ms".format(max(1.225, 1.470, 0.951)),
#                 "Transfer": 125952 + 125952 + 125952,
#                 "Interval": (3.0, 4.0),
#                 "Transfer Raw": "369.0 KBytes",
#                 "Bandwidth": 126375 + 126375 + 126375,
#                 "Lost_vs_Total_Datagrams": (0 + 0 + 0, 86 + 86 + 86),
#                 "Bandwidth Raw": "3033.0 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0.00%",
#                 "Jitter": "{} ms".format(max(1.273, 1.332, 0.821)),
#                 "Transfer": 124928 + 124928 + 124928,
#                 "Interval": (4.0, 5.0),
#                 "Transfer Raw": "366.0 KBytes",
#                 "Bandwidth": 125000 + 125000 + 125000,
#                 "Lost_vs_Total_Datagrams": (0 + 0 + 0, 85 + 85 + 85),
#                 "Bandwidth Raw": "3000.0 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.556 ms",
#                 "Transfer": 2251776,
#                 "Interval": (0.0, 5.0),
#                 "Transfer Raw": "2199 KBytes",
#                 "Bandwidth": 449500,
#                 "Lost_vs_Total_Datagrams": (0, 1532),
#                 "Bandwidth Raw": "3596 Kbits/sec",
#             },
#         ],
#         ("192.168.44.1", "5016@192.168.44.130"): {
#             "report": {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "1.556 ms",
#                 "Transfer": 2251776,
#                 "Interval": (0.0, 5.0),
#                 "Transfer Raw": "2199 KBytes",
#                 "Bandwidth": 449500,
#                 "Lost_vs_Total_Datagrams": (0, 1532),
#                 "Bandwidth Raw": "3596 Kbits/sec",
#             }
#         },
#     },
#     "INFO": [
#         "Server listening on UDP port 5016",
#         "Receiving 1470 byte datagrams",
#         "UDP buffer size:  208 KByte (default)",
#     ],
# }

# COMMAND_OUTPUT_multiple_connections_udp_client = """
# vagrant@app-svr:~$ iperf -c 192.168.44.130 -u -p 5016 -f k -P 2 -i 1 -t 3.0 -b 1000.0k
# ------------------------------------------------------------
# Client connecting to 192.168.44.130, UDP port 5016
# Sending 1470 byte datagrams, IPG target: 11760.00 us (kalman adjust)
# UDP buffer size: 1024 KByte (default)
# ------------------------------------------------------------
# [  3] local 192.168.33.5 port 39154 connected with 192.168.44.130 port 5016
# [  4] local 192.168.33.5 port 55482 connected with 192.168.44.130 port 5016
# [ ID] Interval       Transfer     Bandwidth
# [  3]  0.0- 1.0 sec   123 KBytes  1011 Kbits/sec
# [  4]  0.0- 1.0 sec   123 KBytes  1011 Kbits/sec
# [SUM]  0.0- 1.0 sec   247 KBytes  2023 Kbits/sec
# [  3]  1.0- 2.0 sec   123 KBytes  1011 Kbits/sec
# [  4]  1.0- 2.0 sec   123 KBytes  1011 Kbits/sec
# [SUM]  1.0- 2.0 sec   247 KBytes  2023 Kbits/sec
# [  3]  0.0- 3.0 sec   368 KBytes   999 Kbits/sec
# [  3] Sent 256 datagrams
# [  3] Server Report:
# [  3]  0.0- 3.0 sec   369 KBytes  1003 Kbits/sec   0.188 ms    0/  256 (0%)
# [  3] 0.00-3.01 sec  1 datagrams received out-of-order
# [  4]  0.0- 3.0 sec   368 KBytes   999 Kbits/sec
# [  4] Sent 256 datagrams
# [SUM]  0.0- 3.0 sec   735 KBytes  1999 Kbits/sec
# [SUM] Sent 512 datagrams
# [  4] Server Report:
# [  4]  0.0- 3.0 sec   366 KBytes   995 Kbits/sec   0.097 ms    1/  256 (0.39%)
# vagrant@app-svr:~$"""

# COMMAND_KWARGS_multiple_connections_udp_client = {
#     "options": "-c 192.168.44.130 -u -p 5016 -f k -P 2 -i 1 -t 3.0 -b 1000.0k"
# }

# COMMAND_RESULT_multiple_connections_udp_client = {
#     "CONNECTIONS": {
#         ("55482@192.168.33.5", "5016@192.168.44.130"): [
#             {
#                 "Transfer": 125952,
#                 "Bandwidth": 126375,
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth Raw": "1011 Kbits/sec",
#                 "Interval": (0.0, 1.0),
#             },
#             {
#                 "Transfer": 125952,
#                 "Bandwidth": 126375,
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth Raw": "1011 Kbits/sec",
#                 "Interval": (1.0, 2.0),
#             },
#             {
#                 "Transfer": 376832,
#                 "Bandwidth": 124875,
#                 "Transfer Raw": "368 KBytes",
#                 "Bandwidth Raw": "999 Kbits/sec",
#                 "Interval": (0.0, 3.0),
#             },
#             {
#                 "Transfer": 374784,
#                 "Bandwidth": 124375,
#                 "Transfer Raw": "366 KBytes",
#                 "Bandwidth Raw": "995 Kbits/sec",
#                 "Interval": (0.0, 3.0),
#                 "Jitter": "0.097 ms",
#                 "Lost_vs_Total_Datagrams": (1, 256),
#                 "Lost_Datagrams_ratio": "0.39%",
#             },
#         ],
#         ("39154@192.168.33.5", "5016@192.168.44.130"): [
#             {
#                 "Transfer": 125952,
#                 "Bandwidth": 126375,
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth Raw": "1011 Kbits/sec",
#                 "Interval": (0.0, 1.0),
#             },
#             {
#                 "Transfer": 125952,
#                 "Bandwidth": 126375,
#                 "Transfer Raw": "123 KBytes",
#                 "Bandwidth Raw": "1011 Kbits/sec",
#                 "Interval": (1.0, 2.0),
#             },
#             {
#                 "Transfer": 376832,
#                 "Bandwidth": 124875,
#                 "Transfer Raw": "368 KBytes",
#                 "Bandwidth Raw": "999 Kbits/sec",
#                 "Interval": (0.0, 3.0),
#             },
#             {
#                 "Transfer": 377856,
#                 "Bandwidth": 125375,
#                 "Transfer Raw": "369 KBytes",
#                 "Bandwidth Raw": "1003 Kbits/sec",
#                 "Interval": (0.0, 3.0),
#                 "Jitter": "0.188 ms",
#                 "Lost_vs_Total_Datagrams": (0, 256),
#                 "Lost_Datagrams_ratio": "0%",
#             },
#         ],
#         ("multiport@192.168.33.5", "5016@192.168.44.130"): [
#             {
#                 "Transfer": 252928,
#                 "Bandwidth": 252875,
#                 "Transfer Raw": "247 KBytes",
#                 "Bandwidth Raw": "2023 Kbits/sec",
#                 "Interval": (0.0, 1.0),
#             },
#             {
#                 "Transfer": 252928,
#                 "Bandwidth": 252875,
#                 "Transfer Raw": "247 KBytes",
#                 "Bandwidth Raw": "2023 Kbits/sec",
#                 "Interval": (1.0, 2.0),
#             },
#             {
#                 "Transfer": 752640,
#                 "Bandwidth": 249875,
#                 "Transfer Raw": "735 KBytes",
#                 "Bandwidth Raw": "1999 Kbits/sec",
#                 "Interval": (0.0, 3.0),
#             },
#         ],
#         ("192.168.33.5", "5016@192.168.44.130"): {
#             "report": {
#                 "Transfer": 752640,
#                 "Bandwidth": 249875,
#                 "Transfer Raw": "735 KBytes",
#                 "Bandwidth Raw": "1999 Kbits/sec",
#                 "Interval": (0.0, 3.0),
#             }
#         },
#     },
#     "INFO": [
#         "Client connecting to 192.168.44.130, UDP port 5016",
#         "Sending 1470 byte datagrams, IPG target: 11760.00 us (kalman adjust)",
#         "UDP buffer size: 1024 KByte (default)",
#         "[  3] Sent 256 datagrams",
#         "[  3] 0.00-3.01 sec  1 datagrams received out-of-order",
#         "[  4] Sent 256 datagrams",
#         "[SUM] Sent 512 datagrams",
#     ],
# }

# COMMAND_OUTPUT_singlerun_server = """
# xyz@debian:~$ iperf -s -p 5001 -f k -i 1.0 -P 1
# ------------------------------------------------------------
# Server listening on TCP port 5001
# TCP window size: 85.3 KByte (default)
# ------------------------------------------------------------
# [  4] local 192.168.44.50 port 5001 connected with 192.168.44.100 port 57272
# [ ID] Interval       Transfer     Bandwidth
# [  4]  0.0- 1.0 sec  232124 KBytes  1901558 Kbits/sec
# [  4]  1.0- 2.0 sec  158626 KBytes  1299464 Kbits/sec
# [  4]  2.0- 3.0 sec  191597 KBytes  1569562 Kbits/sec
# [  4]  3.0- 4.0 sec  243509 KBytes  1994828 Kbits/sec
# [  4]  0.0- 4.0 sec  825856 KBytes  1690728 Kbits/sec
# [SUM]  0.0- 4.0 sec  1057980 KBytes  2165942 Kbits/sec
# xyz@debian:~$"""

# COMMAND_KWARGS_singlerun_server = {"options": "-s -p 5001 -f k -i 1.0 -P 1"}

# COMMAND_RESULT_singlerun_server = {
#     "CONNECTIONS": {
#         ("57272@192.168.44.100", "5001@192.168.44.50"): [
#             {
#                 "Transfer": 237694976,
#                 "Bandwidth": 237694750,
#                 "Transfer Raw": "232124 KBytes",
#                 "Bandwidth Raw": "1901558 Kbits/sec",
#                 "Interval": (0.0, 1.0),
#             },
#             {
#                 "Transfer": 162433024,
#                 "Bandwidth": 162433000,
#                 "Transfer Raw": "158626 KBytes",
#                 "Bandwidth Raw": "1299464 Kbits/sec",
#                 "Interval": (1.0, 2.0),
#             },
#             {
#                 "Transfer": 196195328,
#                 "Bandwidth": 196195250,
#                 "Transfer Raw": "191597 KBytes",
#                 "Bandwidth Raw": "1569562 Kbits/sec",
#                 "Interval": (2.0, 3.0),
#             },
#             {
#                 "Transfer": 249353216,
#                 "Bandwidth": 249353500,
#                 "Transfer Raw": "243509 KBytes",
#                 "Bandwidth Raw": "1994828 Kbits/sec",
#                 "Interval": (3.0, 4.0),
#             },
#             {
#                 "Transfer": 845676544,
#                 "Bandwidth": 211341000,
#                 "Transfer Raw": "825856 KBytes",
#                 "Bandwidth Raw": "1690728 Kbits/sec",
#                 "Interval": (0.0, 4.0),
#             },
#         ],
#         ("192.168.44.100", "5001@192.168.44.50"): {
#             "report": {
#                 "Transfer": 845676544,
#                 "Bandwidth": 211341000,
#                 "Transfer Raw": "825856 KBytes",
#                 "Bandwidth Raw": "1690728 Kbits/sec",
#                 "Interval": (0.0, 4.0),
#             }
#         },
#     },
#     "INFO": [
#         "Server listening on TCP port 5001",
#         "TCP window size: 85.3 KByte (default)",
#     ],
# }


# COMMAND_OUTPUT_singlerun_udp_server = """
# xyz@debian:~$ iperf -s -u -p 5001 -f k -i 1.0 -P 1
# ------------------------------------------------------------
# Server listening on UDP port 5001
# Receiving 1470 byte datagrams
# UDP buffer size:  208 KByte (default)
# ------------------------------------------------------------
# [  3] local 192.168.44.50 port 5001 connected with 192.168.44.100 port 42599
# [ ID] Interval       Transfer     Bandwidth        Jitter   Lost/Total Datagrams
# [  3]  0.0- 1.0 sec   129 KBytes  1058 Kbits/sec   0.033 ms    0/   90 (0%)
# [  3]  1.0- 2.0 sec   128 KBytes  1047 Kbits/sec   0.222 ms    0/   89 (0%)
# [  3]  2.0- 3.0 sec   128 KBytes  1047 Kbits/sec   0.022 ms    0/   89 (0%)
# [  3]  3.0- 4.0 sec   128 KBytes  1047 Kbits/sec   0.028 ms    0/   89 (0%)
# [  3]  0.0- 4.0 sec   512 KBytes  1049 Kbits/sec   0.028 ms    0/  357 (0%)
# [SUM]  0.0- 4.0 sec   642 KBytes  1313 Kbits/sec   0.033 ms    0/  447 (0%)
# xyz@debian:~$"""

# COMMAND_KWARGS_singlerun_udp_server = {
#     "options": "-s -u -p 5001 -f k -i 1.0 -P 1"}

# COMMAND_RESULT_singlerun_udp_server = {
#     "CONNECTIONS": {
#         ("42599@192.168.44.100", "5001@192.168.44.50"): [
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.033 ms",
#                 "Transfer": 132096,
#                 "Interval": (0.0, 1.0),
#                 "Transfer Raw": "129 KBytes",
#                 "Bandwidth": 132250,
#                 "Lost_vs_Total_Datagrams": (0, 90),
#                 "Bandwidth Raw": "1058 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.222 ms",
#                 "Transfer": 131072,
#                 "Interval": (1.0, 2.0),
#                 "Transfer Raw": "128 KBytes",
#                 "Bandwidth": 130875,
#                 "Lost_vs_Total_Datagrams": (0, 89),
#                 "Bandwidth Raw": "1047 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.022 ms",
#                 "Transfer": 131072,
#                 "Interval": (2.0, 3.0),
#                 "Transfer Raw": "128 KBytes",
#                 "Bandwidth": 130875,
#                 "Lost_vs_Total_Datagrams": (0, 89),
#                 "Bandwidth Raw": "1047 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.028 ms",
#                 "Transfer": 131072,
#                 "Interval": (3.0, 4.0),
#                 "Transfer Raw": "128 KBytes",
#                 "Bandwidth": 130875,
#                 "Lost_vs_Total_Datagrams": (0, 89),
#                 "Bandwidth Raw": "1047 Kbits/sec",
#             },
#             {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.028 ms",
#                 "Transfer": 524288,
#                 "Interval": (0.0, 4.0),
#                 "Transfer Raw": "512 KBytes",
#                 "Bandwidth": 131125,
#                 "Lost_vs_Total_Datagrams": (0, 357),
#                 "Bandwidth Raw": "1049 Kbits/sec",
#             },
#         ],
#         ("192.168.44.100", "5001@192.168.44.50"): {
#             "report": {
#                 "Lost_Datagrams_ratio": "0%",
#                 "Jitter": "0.028 ms",
#                 "Transfer": 524288,
#                 "Interval": (0.0, 4.0),
#                 "Transfer Raw": "512 KBytes",
#                 "Bandwidth": 131125,
#                 "Lost_vs_Total_Datagrams": (0, 357),
#                 "Bandwidth Raw": "1049 Kbits/sec",
#             }
#         },
#     },
#     "INFO": [
#         "Server listening on UDP port 5001",
#         "Receiving 1470 byte datagrams",
#         "UDP buffer size:  208 KByte (default)",
#     ],
# }
