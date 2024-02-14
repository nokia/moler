# -*- coding: utf-8 -*-
"""
Nmap command module.
"""

__author__ = "Yeshu Yang, Marcin Usielski, Bartosz Odziomek, Marcin Szlapa"
__copyright__ = "Copyright (C) 2018-2022, Nokia"
__email__ = (
    "yeshu.yang@nokia-sbell.com, marcin.usielski@nokia.com, bartosz.odziomek@nokia.com,"
    "marcin.szlapa@nokia.com"
)

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone
from moler.util.converterhelper import ConverterHelper


class Nmap(GenericUnixCommand):
    def __init__(
        self,
        connection,
        ip,
        is_ping=False,
        options=None,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param ip: IP address of host.
        :param is_ping: If True then skip host discovery.
        :param options: Options of command nmap.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Nmap, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.ip = ip
        self.is_ping = is_ping
        self.timeout = 120  # Time in seconds
        self._converter_helper = ConverterHelper.get_converter_helper()
        self._current_crypto_proto = None
        self._current_crypto_proto_type = None
        self._indent = 0

    def build_command_string(self):
        """
        :return: String representation of command to send over connection to device.
        """
        cmd = "nmap"
        if self.options:
            cmd = f"{cmd} {self.options}"
        cmd = f"{cmd} {self.ip}"
        if not self.is_ping:
            cmd = f"{cmd} -PN"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            self._parse_extend_timeout(line)
            try:
                self._parse_error(line)
                self._parse_ports_line(line)
                self._parse_raw_packets(line)
                self._parse_scan_report(line)
                self._parse_scan_reports(line)
                self._parse_syn_stealth_scan(line)
                self._parse_skipping_host(line)
                self._parse_ciphers(line)
                self._parse_ssl_types(line)
                self._parse_cipher_preference(line)
                self._parse_compressors(line)
                self._parse_compressors_header(line)
            except ParsingDone:
                pass
        return super(Nmap, self).on_new_line(line, is_full_line)

    # TLSv1.2:
    _re_ssl_type = re.compile(r"(?P<PROTO>(TLS|SSL)\S+):")

    def _parse_ssl_types(self, line):
        if self._regex_helper.search_compiled(Nmap._re_ssl_type, line):
            key = "CRYPTO_PROTOCOLS"
            if key not in self.current_ret:
                self.current_ret[key] = []
            self._current_crypto_proto = self._regex_helper.group("PROTO")
            self.current_ret[key].append(self._current_crypto_proto)
            if "CRYPTO" not in self.current_ret:
                self.current_ret["CRYPTO"] = {}
            self.current_ret["CRYPTO"][self._current_crypto_proto] = {}
            self._current_crypto_proto_type = None
            raise ParsingDone()

    # cipher preference: server
    _re_cipher_preference = re.compile(r"cipher preference:\s+(?P<CP>\S.*\S)\s*$")

    def _parse_cipher_preference(self, line):
        if self._current_crypto_proto and self._regex_helper.search_compiled(
            Nmap._re_cipher_preference, line
        ):
            self.current_ret["CRYPTO"][self._current_crypto_proto][
                "cipher preference"
            ] = [self._regex_helper.group("CP")]
            self._current_crypto_proto_type = "cipher preference"
            raise ParsingDone()

    # |       NULL
    _re_indent = re.compile(r"^\s*\|(?P<INDENT>\s*)(?P<VALUE>\S.*\S|\S+)")

    def _parse_compressors(self, line):
        if self._current_crypto_proto and 'compressors' == self._current_crypto_proto_type and self._indent > 0 \
                and self._regex_helper.search_compiled(Nmap._re_indent, line):
            current_indent = len(self._regex_helper.group("INDENT"))
            if current_indent < self._indent:
                self._indent = 0
                self._current_crypto_proto_type = None
            else:
                if (
                    "compressors"
                    not in self.current_ret["CRYPTO"][self._current_crypto_proto]
                ):
                    self.current_ret["CRYPTO"][self._current_crypto_proto][
                        "compressors"
                    ] = []
                self.current_ret["CRYPTO"][self._current_crypto_proto][
                    "compressors"
                ].append(self._regex_helper.group("VALUE").strip())
            raise ParsingDone()

    _re_compressors_preference = re.compile(
        r"^\s*\|(?P<INDENT>\s+)(?P<TYPE>compressors):\s*$"
    )

    def _parse_compressors_header(self, line):
        if self._current_crypto_proto and self._regex_helper.search_compiled(
            Nmap._re_compressors_preference, line
        ):
            self._current_crypto_proto_type = self._regex_helper.group("TYPE")
            self._indent = len(self._regex_helper.group("INDENT"))
            raise ParsingDone()

    # def _parse_compressors_preference_data(self, line):

    _re_ports_line = re.compile(
        r"^(?P<LINES>(?P<PORTS>(?P<PORT>\d+)\/(?P<TYPE>\w+))\s+"
        r"(?P<STATE>\S+)\s+(?P<SERVICE>\S+)\s*(?P<REASON>\S+)?\s*)$"
    )

    def _parse_ports_line(self, line):
        if self._regex_helper.search_compiled(Nmap._re_ports_line, line):
            if "PORTS" not in self.current_ret:
                self.current_ret["PORTS"] = {}
            if "LINES" not in self.current_ret["PORTS"]:
                self.current_ret["PORTS"]["LINES"] = []
            ports = self._regex_helper.group("PORTS")
            self.current_ret["PORTS"][ports] = self._regex_helper.groupdict()
            self.current_ret["PORTS"]["LINES"].append(self._regex_helper.group("LINES"))
            del self.current_ret["PORTS"][ports]["PORTS"]
            del self.current_ret["PORTS"][ports]["LINES"]
            raise ParsingDone

    #    Raw packets sent: 65544 (2.884MB) | Rcvd: 65528 (2.621MB)
    _re_raw_packets = re.compile(
        r"Raw packets sent: (?P<SENT_NO>\d+)\s+\((?P<SENT_SIZE>\S+)\)\s+"
        r"\|\s+Rcvd:\s+(?P<RCVD_NO>\d+)\s+\((?P<RCVD_SIZE>\S+)\)"
    )

    def _parse_raw_packets(self, line):
        if self._regex_helper.search_compiled(Nmap._re_raw_packets, line):
            if "RAW_PACKETS" not in self.current_ret:
                self.current_ret["RAW_PACKETS"] = {}
            self.current_ret["RAW_PACKETS"] = self._regex_helper.groupdict()
            raise ParsingDone

    #    Nmap scan report for 192.168.255.4 [host down, received no-response]
    _re_scan_report = re.compile(
        r"(?P<LINE>Nmap scan report for (?P<ADDRESS>\S+)\s+\[host\s+"
        r"(?P<HOST>\S+),\s+received\s+(?P<RECEIVED>\S+)\])"
    )

    def _parse_scan_report(self, line):
        if self._regex_helper.search_compiled(Nmap._re_scan_report, line):
            if "SCAN_REPORT" not in self.current_ret:
                self.current_ret["SCAN_REPORT"] = {}
            self.current_ret["SCAN_REPORT"] = self._regex_helper.groupdict()
            raise ParsingDone

    #   Nmap scan report for 192.168.255.132
    _re_scan_reports = re.compile(
        r"(?P<LINE>Nmap scan report for (?P<ADDRESS>\S+)"
        r"(?:\s+\[host\s+(?P<HOST>\S+),\s+received\s+(?P<RECEIVED>\S+)\])?)"
    )

    def _parse_scan_reports(self, line):
        if self._regex_helper.search_compiled(Nmap._re_scan_reports, line):
            if "SCAN_REPORTS" not in self.current_ret:
                self.current_ret["SCAN_REPORTS"] = []
            self.current_ret["SCAN_REPORTS"].append(self._regex_helper.groupdict())
            raise ParsingDone

    # if "HOST" not in self.current_ret["SKIPPING_HOST"]:
    #     self.current_ret["SKIPPING_HOST"]["HOST"] = []
    # self.current_ret["SKIPPING_HOST"]["HOST"].append(self._regex_helper.group("HOST"))

    #    SYN Stealth Scan Timing: About 78.01% done; ETC: 23:30 (0:00:52 remaining)
    _re_syn_stealth_scan = re.compile(
        r"SYN Stealth Scan Timing: About (?P<DONE>[\d\.]+)% done; "
        r"ETC: (?P<ETC>[\d:]+) \((?P<REMAINING>[\d:]+) remaining\)"
    )

    def _parse_syn_stealth_scan(self, line):
        if self._regex_helper.search_compiled(Nmap._re_syn_stealth_scan, line):
            if "SYN_STEALTH_SCAN" not in self.current_ret:
                self.current_ret["SYN_STEALTH_SCAN"] = {}
            self.current_ret["SYN_STEALTH_SCAN"] = self._regex_helper.groupdict()
            raise ParsingDone

    # Failed to open normal output file /logs/IP_Protocol_Discovery_BH_IPv4.nmap for writing
    _re_fail_file = re.compile(r"Failed to open.*file", re.I)

    def _parse_error(self, line):
        if self._regex_helper.search_compiled(Nmap._re_fail_file, line):
            self.set_exception(CommandFailure(self, f"Fail in line: '{line}'"))
            raise ParsingDone()

    #    Skipping host 10.9.134.1 due to host timeout
    _re_skipping_host = re.compile(r"Skipping host (?P<HOST>\S+) due to host timeout")

    def _parse_skipping_host(self, line):
        if self._regex_helper.search_compiled(Nmap._re_skipping_host, line):
            if "SKIPPING_HOST" not in self.current_ret:
                self.current_ret["SKIPPING_HOST"] = {}
            if "HOST" not in self.current_ret["SKIPPING_HOST"]:
                self.current_ret["SKIPPING_HOST"]["HOST"] = []
            self.current_ret["SKIPPING_HOST"]["HOST"].append(
                self._regex_helper.group("HOST")
            )
            raise ParsingDone

    #    UDP Scan Timing: About 61.09% done; ETC: 14:18 (0:21:04 remaining)
    _re_extend_timeout = re.compile(
        r"\((?P<HOURS>\d+):(?P<MINUTES>\d+):(?P<SECONDS>\d+)\s+remaining\)"
    )

    def _parse_extend_timeout(self, line):
        if self._regex_helper.search_compiled(Nmap._re_extend_timeout, line):
            timedelta = self._converter_helper.to_number(
                self._regex_helper.group("HOURS")) * 3600 + self._converter_helper.to_number(
                self._regex_helper.group("MINUTES")) * 60 + self._converter_helper.to_number(
                self._regex_helper.group("SECONDS"))
            self.extend_timeout(timedelta=timedelta)

    # |       TLS_ABC_RSA_WITH_AED_256_GCB_SHA123
    _re_cipher = re.compile(r"\|\s*(?P<CIPHER>TLS_[^\s]+)")

    def _parse_ciphers(self, line):
        if self._regex_helper.search_compiled(Nmap._re_cipher, line):
            cipher = self._regex_helper.group("CIPHER")
            if "CIPHERS" not in self.current_ret:
                self.current_ret["CIPHERS"] = []
            self.current_ret["CIPHERS"].append(cipher)
            if self._current_crypto_proto:
                if (
                    "ciphers"
                    not in self.current_ret["CRYPTO"][self._current_crypto_proto]
                ):
                    self.current_ret["CRYPTO"][self._current_crypto_proto][
                        "ciphers"
                    ] = []
                self.current_ret["CRYPTO"][self._current_crypto_proto][
                    "ciphers"
                ].append(cipher)
                self._current_crypto_proto_type = "ciphers"
            raise ParsingDone


COMMAND_OUTPUT_host_up = """
root@cp19-nj:/home/ute# nmap -d1 -p- -S 192.168.255.126 192.168.255.129 -PN

Starting Nmap 6.00 ( http://nmap.org ) at 2018-05-23 08:36 CST
--------------- Timing report ---------------
  hostgroups: min 1, max 100000
  rtt-timeouts: init 1000, min 100, max 10000
  max-scan-delay: TCP 1000, UDP 1000, SCTP 1000
  parallelism: min 0, max 0
  max-retries: 10, host-timeout: 0
  min-rate: 0, max-rate: 0
---------------------------------------------
Initiating ARP Ping Scan at 08:36
Scanning 192.168.255.129 [1 port]
Packet capture filter (device eth1): arp and arp[18:4] = 0xFE365EB1 and arp[22:2] = 0x1AE6
Completed ARP Ping Scan at 08:36, 0.03s elapsed (1 total hosts)
Overall sending rates: 34.08 packets / s, 1431.20 bytes / s.
mass_rdns: Using DNS server 135.251.124.100
mass_rdns: Using DNS server 135.251.38.218
Initiating Parallel DNS resolution of 1 host. at 08:36
mass_rdns: 13.00s 0/1 [#: 2, OK: 0, NX: 0, DR: 0, SF: 0, TR: 4]
Completed Parallel DNS resolution of 1 host. at 08:36, 13.00s elapsed
DNS resolution of 1 IPs took 13.00s. Mode: Async [#: 2, OK: 0, NX: 0, DR: 1, SF: 0, TR: 4, CN: 0]
Initiating SYN Stealth Scan at 08:36
Scanning 192.168.255.129 [65535 ports]
Packet capture filter (device eth1): dst host 192.168.255.126 and (icmp or icmp6 or ((tcp or udp or sctp) and (src host 192.168.255.129)))
Discovered open port 443/tcp on 192.168.255.129
Discovered open port 6001/tcp on 192.168.255.129
Discovered open port 12000/tcp on 192.168.255.129
Discovered open port 3300/tcp on 192.168.255.129
Discovered open port 12001/tcp on 192.168.255.129
Completed SYN Stealth Scan at 08:36, 4.31s elapsed (65535 total ports)
Overall sending rates: 15200.28 packets / s, 668812.33 bytes / s.
Nmap scan report for 192.168.255.129
Host is up, received arp-response (0.00049s latency).
Scanned at 2018-05-23 08:36:34 CST for 18s
Not shown: 65522 closed ports
Reason: 65522 resets
PORT      STATE    SERVICE     REASON
21/tcp    filtered ftp         no-response
22/tcp    filtered ssh         no-response
443/tcp   open     https       syn-ack
3300/tcp  open     unknown     syn-ack
6001/tcp  open     X11:1       syn-ack
12000/tcp open     cce4x       syn-ack
12001/tcp open     entextnetwk syn-ack
15001/tcp filtered unknown     no-response
15002/tcp filtered unknown     no-response
15003/tcp filtered unknown     no-response
15004/tcp filtered unknown     no-response
15005/tcp filtered unknown     no-response
15007/tcp filtered unknown     no-response
MAC Address: 74:DA:EA:53:D6:24 (Unknown)
Final times for host: srtt: 490 rttvar: 90  to: 100000

Read from /usr/bin/../share/nmap: nmap-mac-prefixes nmap-payloads nmap-services.
Nmap done: 1 IP address (1 host up) scanned in 17.52 seconds
           Raw packets sent: 65544 (2.884MB) | Rcvd: 65528 (2.621MB)
root@cp19-nj:/home/ute# """

COMMAND_KWARGS_host_up = {
    "options": "-d1 -p- -S 192.168.255.126",
    "ip": "192.168.255.129",
}

COMMAND_RESULT_host_up = {
    "PORTS": {
        "LINES": [
            "21/tcp    filtered ftp         no-response",
            "22/tcp    filtered ssh         no-response",
            "443/tcp   open     https       syn-ack",
            "3300/tcp  open     unknown     syn-ack",
            "6001/tcp  open     X11:1       syn-ack",
            "12000/tcp open     cce4x       syn-ack",
            "12001/tcp open     entextnetwk syn-ack",
            "15001/tcp filtered unknown     no-response",
            "15002/tcp filtered unknown     no-response",
            "15003/tcp filtered unknown     no-response",
            "15004/tcp filtered unknown     no-response",
            "15005/tcp filtered unknown     no-response",
            "15007/tcp filtered unknown     no-response",
        ],
        "21/tcp": {
            "PORT": "21",
            "REASON": "no-response",
            "SERVICE": "ftp",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
        "22/tcp": {
            "PORT": "22",
            "REASON": "no-response",
            "SERVICE": "ssh",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
        "443/tcp": {
            "PORT": "443",
            "REASON": "syn-ack",
            "SERVICE": "https",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "3300/tcp": {
            "PORT": "3300",
            "REASON": "syn-ack",
            "SERVICE": "unknown",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "6001/tcp": {
            "PORT": "6001",
            "REASON": "syn-ack",
            "SERVICE": "X11:1",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "12000/tcp": {
            "PORT": "12000",
            "REASON": "syn-ack",
            "SERVICE": "cce4x",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "12001/tcp": {
            "PORT": "12001",
            "REASON": "syn-ack",
            "SERVICE": "entextnetwk",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "15001/tcp": {
            "PORT": "15001",
            "REASON": "no-response",
            "SERVICE": "unknown",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
        "15002/tcp": {
            "PORT": "15002",
            "REASON": "no-response",
            "SERVICE": "unknown",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
        "15003/tcp": {
            "PORT": "15003",
            "REASON": "no-response",
            "SERVICE": "unknown",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
        "15004/tcp": {
            "PORT": "15004",
            "REASON": "no-response",
            "SERVICE": "unknown",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
        "15005/tcp": {
            "PORT": "15005",
            "REASON": "no-response",
            "SERVICE": "unknown",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
        "15007/tcp": {
            "PORT": "15007",
            "REASON": "no-response",
            "SERVICE": "unknown",
            "STATE": "filtered",
            "TYPE": "tcp",
        },
    },
    "RAW_PACKETS": {
        "RCVD_NO": "65528",
        "RCVD_SIZE": "2.621MB",
        "SENT_NO": "65544",
        "SENT_SIZE": "2.884MB",
    },
    "SCAN_REPORTS": [
        {
            "ADDRESS": "192.168.255.129",
            "HOST": None,
            "LINE": "Nmap scan report for 192.168.255.129",
            "RECEIVED": None,
        }
    ],
}

COMMAND_OUTPUT_host_down = """root@cp19-nj:/home/ute# nmap -d1 -p- -S 192.168.255.126 192.168.255.4 -PN

Starting Nmap 6.00 ( http://nmap.org ) at 2018-05-25 08:40 CST
--------------- Timing report ---------------
  hostgroups: min 1, max 100000
  rtt-timeouts: init 1000, min 100, max 10000
  max-scan-delay: TCP 1000, UDP 1000, SCTP 1000
  parallelism: min 0, max 0
  max-retries: 10, host-timeout: 0
  min-rate: 0, max-rate: 0
---------------------------------------------
Initiating ARP Ping Scan at 08:40
Scanning 192.168.255.4 [1 port]
Packet capture filter (device eth1): arp and arp[18:4] = 0xFE365EB1 and arp[22:2] = 0x1AE6
Completed ARP Ping Scan at 08:40, 0.43s elapsed (1 total hosts)
Overall sending rates: 4.61 packets / s, 193.61 bytes / s.
mass_rdns: Using DNS server 135.251.124.100
mass_rdns: Using DNS server 135.251.38.218
Nmap scan report for 192.168.255.4 [host down, received no-response]
Read from /usr/bin/../share/nmap: nmap-payloads nmap-services.
Nmap done: 1 IP address (0 hosts up) scanned in 0.54 seconds
           Raw packets sent: 2 (56B) | Rcvd: 0 (0B)
root@cp19-nj:/home/ute# """

COMMAND_KWARGS_host_down = {
    "options": "-d1 -p- -S 192.168.255.126",
    "ip": "192.168.255.4",
}

COMMAND_RESULT_host_down = {
    "RAW_PACKETS": {
        "RCVD_NO": "0",
        "RCVD_SIZE": "0B",
        "SENT_NO": "2",
        "SENT_SIZE": "56B",
    },
    "SCAN_REPORT": {
        "ADDRESS": "192.168.255.4",
        "HOST": "down",
        "LINE": "Nmap scan report for 192.168.255.4 [host down, received no-response]",
        "RECEIVED": "no-response",
    },
}

COMMAND_OUTPUT = """root@cp19-nj:/home/ute#  nmap -d1 -p- --host-timeout 100 10.9.134.0/28 -PN

Starting Nmap 6.00 ( http://nmap.org ) at 2018-05-31 03:23 CST
--------------- Timing report ---------------
  hostgroups: min 1, max 100000
  rtt-timeouts: init 1000, min 100, max 10000
  max-scan-delay: TCP 1000, UDP 1000, SCTP 1000
  parallelism: min 0, max 0
  max-retries: 10, host-timeout: 100000
  min-rate: 0, max-rate: 0
---------------------------------------------
mass_rdns: Using DNS server 135.251.124.100
mass_rdns: Using DNS server 135.251.38.218
Initiating Parallel DNS resolution of 16 hosts. at 03:23
mass_rdns: 0.01s 0/16 [#: 2, OK: 0, NX: 0, DR: 0, SF: 0, TR: 16]
Completed Parallel DNS resolution of 16 hosts. at 03:23, 9.08s elapsed
DNS resolution of 16 IPs took 9.08s. Mode: Async [#: 2, OK: 0, NX: 16, DR: 0, SF: 0, TR: 36, CN: 0]
Initiating SYN Stealth Scan at 03:23
Scanning 4 hosts [65535 ports/host]
Packet capture filter (device eth0): dst host 10.9.132.16 and (icmp or icmp6 or ((tcp or udp or sctp) and (src host 10.9.134.0 or src host 10.9.134.1 or src host 10.9.134.2 or src host 10.9.134.3)))
Discovered open port 23/tcp on 10.9.134.1
Discovered open port 80/tcp on 10.9.134.1
Discovered open port 22/tcp on 10.9.134.1
Discovered open port 443/tcp on 10.9.134.1
Discovered open port 21/tcp on 10.9.134.1
Increased max_successful_tryno for 10.9.134.1 to 1 (packet drop)
Increased max_successful_tryno for 10.9.134.1 to 2 (packet drop)
Increased max_successful_tryno for 10.9.134.1 to 3 (packet drop)
Increased max_successful_tryno for 10.9.134.1 to 4 (packet drop)
Increasing send delay for 10.9.134.1 from 0 to 5 due to max_successful_tryno increase to 4
Increased max_successful_tryno for 10.9.134.1 to 5 (packet drop)
Increasing send delay for 10.9.134.1 from 5 to 10 due to max_successful_tryno increase to 5
Increased max_successful_tryno for 10.9.134.1 to 6 (packet drop)
Increasing send delay for 10.9.134.1 from 10 to 20 due to max_successful_tryno increase to 6
SYN Stealth Scan Timing: About 0.49% done
SYN Stealth Scan Timing: About 1.98% done; ETC: 04:15 (0:50:16 remaining)
Increased max_successful_tryno for 10.9.134.1 to 7 (packet drop)
Increasing send delay for 10.9.134.1 from 20 to 40 due to max_successful_tryno increase to 7
Increased max_successful_tryno for 10.9.134.1 to 8 (packet drop)
Increasing send delay for 10.9.134.1 from 40 to 80 due to max_successful_tryno increase to 8
SYN Stealth Scan Timing: About 3.32% done; ETC: 04:09 (0:44:09 remaining)
10.9.134.0 timed out during SYN Stealth Scan (3 hosts left)
10.9.134.1 timed out during SYN Stealth Scan (2 hosts left)
10.9.134.2 timed out during SYN Stealth Scan (1 host left)
10.9.134.3 timed out during SYN Stealth Scan (0 hosts left)
Completed SYN Stealth Scan at 03:25, 100.05s elapsed (4 hosts timed out)
Overall sending rates: 230.05 packets / s, 10122.35 bytes / s.
Nmap scan report for 10.9.134.0
Host is up, received user-set.
Skipping host 10.9.134.0 due to host timeout
Nmap scan report for 10.9.134.1
Host is up, received user-set (0.0035s latency).
Skipping host 10.9.134.1 due to host timeout
Nmap scan report for 10.9.134.2
Host is up, received user-set.
Skipping host 10.9.134.2 due to host timeout
Nmap scan report for 10.9.134.3
Host is up, received user-set.
Skipping host 10.9.134.3 due to host timeout
Initiating SYN Stealth Scan at 03:25
Scanning 12 hosts [65535 ports/host]
Packet capture filter (device eth0): dst host 10.9.132.16 and (icmp or icmp6 or ((tcp or udp or sctp) and (src host 10.9.134.4 or src host 10.9.134.5 or src host 10.9.134.6 or src host 10.9.134.7 or src host 10.9.134.8 or src host 10.9.134.9 or src host 10.9.134.10 or src host 10.9.134.11 or src host 10.9.134.12 or src host 10.9.134.13 or src host 10.9.134.14 or src host 10.9.134.15)))
Discovered open port 23/tcp on 10.9.134.4
Discovered open port 445/tcp on 10.9.134.12
Discovered open port 445/tcp on 10.9.134.13
Discovered open port 3389/tcp on 10.9.134.12
Discovered open port 3389/tcp on 10.9.134.13
Discovered open port 135/tcp on 10.9.134.12
Discovered open port 443/tcp on 10.9.134.12
Discovered open port 135/tcp on 10.9.134.13
Discovered open port 139/tcp on 10.9.134.12
Discovered open port 443/tcp on 10.9.134.13
Discovered open port 139/tcp on 10.9.134.13
Increased max_successful_tryno for 10.9.134.12 to 1 (packet drop)
Discovered open port 22/tcp on 10.9.134.4
Increased max_successful_tryno for 10.9.134.13 to 1 (packet drop)
Discovered open port 443/tcp on 10.9.134.4
Discovered open port 22/tcp on 10.9.134.15
Discovered open port 21/tcp on 10.9.134.4
SYN Stealth Scan Timing: About 1.04% done; ETC: 04:15 (0:49:20 remaining)
SYN Stealth Scan Timing: About 4.44% done; ETC: 03:48 (0:21:52 remaining)
SYN Stealth Scan Timing: About 11.04% done; ETC: 03:39 (0:12:13 remaining)
10.9.134.4 timed out during SYN Stealth Scan (11 hosts left)
10.9.134.5 timed out during SYN Stealth Scan (10 hosts left)
10.9.134.6 timed out during SYN Stealth Scan (9 hosts left)
10.9.134.7 timed out during SYN Stealth Scan (8 hosts left)
10.9.134.8 timed out during SYN Stealth Scan (7 hosts left)
10.9.134.9 timed out during SYN Stealth Scan (6 hosts left)
10.9.134.10 timed out during SYN Stealth Scan (5 hosts left)
10.9.134.11 timed out during SYN Stealth Scan (4 hosts left)
10.9.134.12 timed out during SYN Stealth Scan (3 hosts left)
10.9.134.13 timed out during SYN Stealth Scan (2 hosts left)
10.9.134.14 timed out during SYN Stealth Scan (1 host left)
10.9.134.15 timed out during SYN Stealth Scan (0 hosts left)
Completed SYN Stealth Scan at 03:27, 100.00s elapsed (12 hosts timed out)
Overall sending rates: 1876.97 packets / s, 82586.62 bytes / s.
Nmap scan report for 10.9.134.4
Host is up, received user-set (0.00045s latency).
Skipping host 10.9.134.4 due to host timeout
Nmap scan report for 10.9.134.5
Host is up, received user-set.
Skipping host 10.9.134.5 due to host timeout
Nmap scan report for 10.9.134.6
Host is up, received user-set.
Skipping host 10.9.134.6 due to host timeout
Nmap scan report for 10.9.134.7
Host is up, received user-set.
Skipping host 10.9.134.7 due to host timeout
Nmap scan report for 10.9.134.8
Host is up, received user-set.
Skipping host 10.9.134.8 due to host timeout
Nmap scan report for 10.9.134.9
Host is up, received user-set.
Skipping host 10.9.134.9 due to host timeout
Nmap scan report for 10.9.134.10
Host is up, received user-set.
Skipping host 10.9.134.10 due to host timeout
Nmap scan report for 10.9.134.11
Host is up, received user-set.
Skipping host 10.9.134.11 due to host timeout
Nmap scan report for 10.9.134.12
Host is up, received user-set (0.00023s latency).
Skipping host 10.9.134.12 due to host timeout
Nmap scan report for 10.9.134.13
Host is up, received user-set (0.00030s latency).
Skipping host 10.9.134.13 due to host timeout
Nmap scan report for 10.9.134.14
Host is up, received user-set.
Skipping host 10.9.134.14 due to host timeout
Nmap scan report for 10.9.134.15
Host is up, received user-set (0.00030s latency).
Skipping host 10.9.134.15 due to host timeout
Read from /usr/bin/../share/nmap: nmap-payloads nmap-services.
Nmap done: 16 IP addresses (16 hosts up) scanned in 209.25 seconds
           Raw packets sent: 210722 (9.272MB) | Rcvd: 18224 (730.812KB)
root@cp19-nj:/home/ute# """

COMMAND_KWARGS = {"options": "-d1 -p- --host-timeout 100", "ip": "10.9.134.0/28"}

COMMAND_RESULT = {
    "RAW_PACKETS": {
        "RCVD_NO": "18224",
        "RCVD_SIZE": "730.812KB",
        "SENT_NO": "210722",
        "SENT_SIZE": "9.272MB",
    },
    "SKIPPING_HOST": {
        "HOST": [
            "10.9.134.0",
            "10.9.134.1",
            "10.9.134.2",
            "10.9.134.3",
            "10.9.134.4",
            "10.9.134.5",
            "10.9.134.6",
            "10.9.134.7",
            "10.9.134.8",
            "10.9.134.9",
            "10.9.134.10",
            "10.9.134.11",
            "10.9.134.12",
            "10.9.134.13",
            "10.9.134.14",
            "10.9.134.15",
        ]
    },
    "SYN_STEALTH_SCAN": {"DONE": "11.04", "ETC": "03:39", "REMAINING": "0:12:13"},
    "SCAN_REPORTS": [
        {
            "ADDRESS": "10.9.134.0",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.0",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.1",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.1",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.2",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.2",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.3",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.3",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.4",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.4",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.5",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.5",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.6",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.6",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.7",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.7",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.8",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.8",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.9",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.9",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.10",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.10",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.11",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.11",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.12",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.12",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.13",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.13",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.14",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.14",
            "RECEIVED": None,
        },
        {
            "ADDRESS": "10.9.134.15",
            "HOST": None,
            "LINE": "Nmap scan report for 10.9.134.15",
            "RECEIVED": None,
        },
    ],
}

COMMAND_OUTPUT_CIPHERS = """root@cp19-nj:# nmap --script ssl-enum-ciphers -p 443 10.83.180.140 -PN
Starting Nmap 7.80 ( https://nmap.org ) at 2020-11-13 10:43 CET
Nmap scan report for 10.83.182.143
Host is up (0.000067s latency).

PORT    STATE SERVICE
443/tcp open  https
| ssl-enum-ciphers:
|   TLSv1.2:
|     ciphers:
|       TLS_DHE_RSA_WITH_AES_128_GCM_SHA256 (dh 4096) - A
|     compressors:
|       NULL
|     cipher preference: client
|_  least strength: A

Nmap done: 1 IP address (1 host up) scanned in 0.44 seconds
root@cp19-nj:#"""

COMMAND_KWARGS_CIPHERS = {
    "options": "--script ssl-enum-ciphers -p 443",
    "ip": "10.83.180.140",
}

COMMAND_RESULT_CIPHERS = {
    "CRYPTO_PROTOCOLS": ["TLSv1.2"],
    "CRYPTO": {
        "TLSv1.2": {
            "cipher preference": ["client"],
            "ciphers": ["TLS_DHE_RSA_WITH_AES_128_GCM_SHA256"],
            "compressors": ["NULL"],
        }
    },
    "CIPHERS": ["TLS_DHE_RSA_WITH_AES_128_GCM_SHA256"],
    "PORTS": {
        "443/tcp": {
            "PORT": "443",
            "REASON": None,
            "SERVICE": "https",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "LINES": ["443/tcp open  https"],
    },
    "SCAN_REPORTS": [
        {
            "ADDRESS": "10.83.182.143",
            "HOST": None,
            "LINE": "Nmap scan report for 10.83.182.143",
            "RECEIVED": None,
        }
    ],
}

COMMAND_KWARGS_two_cryptoprotocols = {
    "options": "--script ssl-enum-ciphers",
    "ip": "10.83.182.238",
}

COMMAND_RESULT_two_cryptoprotocols = {
    "CIPHERS": [
        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_DHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_RSA_WITH_AES_256_CBC_SHA",
        "TLS_DHE_RSA_WITH_AES_128_CBC_SHA",
        "TLS_RSA_WITH_AES_128_CBC_SHA",
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_DHE_RSA_WITH_AES_256_CBC_SHA256",
        "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_DHE_RSA_WITH_AES_256_CBC_SHA",
        "TLS_RSA_WITH_AES_256_GCM_SHA384",
        "TLS_RSA_WITH_AES_256_CBC_SHA256",
        "TLS_RSA_WITH_AES_256_CBC_SHA",
        "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256",
        "TLS_DHE_RSA_WITH_AES_128_CBC_SHA256",
        "TLS_DHE_RSA_WITH_AES_128_CBC_SHA",
        "TLS_RSA_WITH_AES_128_GCM_SHA256",
        "TLS_RSA_WITH_AES_128_CBC_SHA256",
        "TLS_RSA_WITH_AES_128_CBC_SHA",
    ],
    "CRYPTO_PROTOCOLS": ["TLSv1.1", "TLSv1.2"],
    "CRYPTO": {
        "TLSv1.1": {
            "ciphers": [
                "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
                "TLS_DHE_RSA_WITH_AES_256_CBC_SHA",
                "TLS_RSA_WITH_AES_256_CBC_SHA",
                "TLS_DHE_RSA_WITH_AES_128_CBC_SHA",
                "TLS_RSA_WITH_AES_128_CBC_SHA",
            ],
            "compressors": [
                "NULL",
            ],
            "cipher preference": ["server"],
        },
        "TLSv1.2": {
            "ciphers": [
                "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
                "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384",
                "TLS_DHE_RSA_WITH_AES_256_CBC_SHA256",
                "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
                "TLS_DHE_RSA_WITH_AES_256_CBC_SHA",
                "TLS_RSA_WITH_AES_256_GCM_SHA384",
                "TLS_RSA_WITH_AES_256_CBC_SHA256",
                "TLS_RSA_WITH_AES_256_CBC_SHA",
                "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_DHE_RSA_WITH_AES_128_CBC_SHA256",
                "TLS_DHE_RSA_WITH_AES_128_CBC_SHA",
                "TLS_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_RSA_WITH_AES_128_CBC_SHA256",
                "TLS_RSA_WITH_AES_128_CBC_SHA",
            ],
            "compressors": [
                "NULL",
            ],
            "cipher preference": ["server"],
        },
    },
    "PORTS": {
        "111/tcp": {
            "PORT": "111",
            "REASON": None,
            "SERVICE": "rpcbind",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "15002/tcp": {
            "PORT": "15002",
            "REASON": None,
            "SERVICE": "onep-tls",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "15003/tcp": {
            "PORT": "15003",
            "REASON": None,
            "SERVICE": "unknown",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "15004/tcp": {
            "PORT": "15004",
            "REASON": None,
            "SERVICE": "unknown",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "2049/tcp": {
            "PORT": "2049",
            "REASON": None,
            "SERVICE": "nfs",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "21/tcp": {
            "PORT": "21",
            "REASON": None,
            "SERVICE": "ftp",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "22/tcp": {
            "PORT": "22",
            "REASON": None,
            "SERVICE": "ssh",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "443/tcp": {
            "PORT": "443",
            "REASON": None,
            "SERVICE": "https",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "80/tcp": {
            "PORT": "80",
            "REASON": None,
            "SERVICE": "http",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "8080/tcp": {
            "PORT": "8080",
            "REASON": None,
            "SERVICE": "http-proxy",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "8443/tcp": {
            "PORT": "8443",
            "REASON": None,
            "SERVICE": "https-alt",
            "STATE": "open",
            "TYPE": "tcp",
        },
        "LINES": [
            "21/tcp    open  ftp",
            "22/tcp    open  ssh",
            "80/tcp    open  http",
            "111/tcp   open  rpcbind",
            "443/tcp   open  https",
            "2049/tcp  open  nfs",
            "8080/tcp  open  http-proxy",
            "8443/tcp  open  https-alt",
            "15002/tcp open  onep-tls",
            "15003/tcp open  unknown",
            "15004/tcp open  unknown",
        ],
    },
    "SCAN_REPORTS": [
        {
            "ADDRESS": "10.83.182.238",
            "HOST": None,
            "LINE": "Nmap scan report for 10.83.182.238",
            "RECEIVED": None,
        }
    ],
}

COMMAND_OUTPUT_two_cryptoprotocols = """nmap --script ssl-enum-ciphers 10.83.182.238 -PN
nmap --script ssl-enum-ciphers 10.83.182.238 -PN
Starting Nmap 7.70 ( https://nmap.org ) at 2020-12-08 12:41 CET
Nmap scan report for 10.83.182.238
Host is up (0.00046s latency).
Not shown: 989 closed ports
PORT      STATE SERVICE
21/tcp    open  ftp
22/tcp    open  ssh
80/tcp    open  http
111/tcp   open  rpcbind
443/tcp   open  https
| ssl-enum-ciphers:
|   TLSv1.1:
|     ciphers:
|       TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA (ecdh_x25519) - A
|       TLS_DHE_RSA_WITH_AES_256_CBC_SHA (dh 2048) - A
|       TLS_RSA_WITH_AES_256_CBC_SHA (rsa 2048) - A
|       TLS_DHE_RSA_WITH_AES_128_CBC_SHA (dh 2048) - A
|       TLS_RSA_WITH_AES_128_CBC_SHA (rsa 2048) - A
|     cipher preference: server
|     compressors:
|       NULL
|   TLSv1.2:
|     ciphers:
|       TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (ecdh_x25519) - A
|       TLS_DHE_RSA_WITH_AES_256_GCM_SHA384 (dh 2048) - A
|       TLS_DHE_RSA_WITH_AES_256_CBC_SHA256 (dh 2048) - A
|       TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA (ecdh_x25519) - A
|       TLS_DHE_RSA_WITH_AES_256_CBC_SHA (dh 2048) - A
|       TLS_RSA_WITH_AES_256_GCM_SHA384 (rsa 2048) - A
|       TLS_RSA_WITH_AES_256_CBC_SHA256 (rsa 2048) - A
|       TLS_RSA_WITH_AES_256_CBC_SHA (rsa 2048) - A
|       TLS_DHE_RSA_WITH_AES_128_GCM_SHA256 (dh 2048) - A
|       TLS_DHE_RSA_WITH_AES_128_CBC_SHA256 (dh 2048) - A
|       TLS_DHE_RSA_WITH_AES_128_CBC_SHA (dh 2048) - A
|       TLS_RSA_WITH_AES_128_GCM_SHA256 (rsa 2048) - A
|       TLS_RSA_WITH_AES_128_CBC_SHA256 (rsa 2048) - A
|       TLS_RSA_WITH_AES_128_CBC_SHA (rsa 2048) - A
|     cipher preference: server
|     compressors:
|       NULL
|_  least strength: A
2049/tcp  open  nfs
8080/tcp  open  http-proxy
8443/tcp  open  https-alt
15002/tcp open  onep-tls
15003/tcp open  unknown
15004/tcp open  unknown
user@host$ """
