# -*- coding: utf-8 -*-
"""
Nmap command module.
"""

__author__ = 'Yeshu Yang'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'yeshu.yang@nokia-sbell.com'

import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import ParsingDone


class Nmap(GenericUnix):

    def __init__(self, connection, ip, is_ping=False, option=None, prompt=None, new_line_chars=None):
        super(Nmap, self).__init__(connection, prompt, new_line_chars)
        self.option = option
        self.ip = ip
        self.is_ping = is_ping
        self.timeout = 120  # Time in seconds

    def build_command_string(self):
        cmd = "nmap"
        if self.option:
            cmd = cmd + " " + self.option
        cmd = cmd + " " + self.ip
        if not self.is_ping:
            cmd = cmd + " -PN"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_ports_line(line)
                self._parse_scan_report(line)
                self._parse_raw_packets(line)
            except ParsingDone:
                pass
        return super(Nmap, self).on_new_line(line, is_full_line)

    _re_ports_line = re.compile(r"^(?P<LINES>(?P<PORTS>(?P<PORT>\d+)\/(?P<TYPE>\w+))\s+"
                                r"(?P<STATE>\S+)\s+(?P<SERVICE>\S+)\s+(?P<REASON>\S+)\s*)$")

    def _parse_ports_line(self, line):
        if self._regex_helper.search_compiled(Nmap._re_ports_line, line):
            if "PORTS" not in self.current_ret:
                self.current_ret["PORTS"] = dict()
            if "LINES" not in self.current_ret["PORTS"]:
                self.current_ret["PORTS"]["LINES"] = list()
            ports = self._regex_helper.group("PORTS")
            self.current_ret["PORTS"][ports] = self._regex_helper.groupdict()
            self.current_ret["PORTS"]["LINES"]. append(self._regex_helper.group("LINES"))
            del(self.current_ret["PORTS"][ports]["PORTS"])
            del(self.current_ret["PORTS"][ports]["LINES"])
            raise ParsingDone

    #Raw packets sent: 65544 (2.884MB) | Rcvd: 65528 (2.621MB)
    _re_raw_packets = re.compile(r"Raw packets sent: (?P<SENT_NO>\d+)\s+\((?P<SENT_SIZE>\S+)\)\s+"
                                 r"\|\s+Rcvd:\s+(?P<RCVD_NO>\d+)\s+\((?P<RCVD_SIZE>\S+)\)")

    def _parse_raw_packets(self,line):
        if self._regex_helper.search_compiled(Nmap._re_raw_packets, line):
            if "RAW_PACKETS" not in self.current_ret:
                self.current_ret["RAW_PACKETS"] = dict()
            self.current_ret["RAW_PACKETS"] = self._regex_helper.groupdict()
            raise ParsingDone

    # Nmap scan report for 192.168.255.4 [host down, received no-response]
    _re_scan_report = re.compile(r"(?P<LINE>Nmap scan report for (?P<ADDRESS>\S+)\s+\[host\s+"
                                 r"(?P<HOST>\S+),\s+received\s+(?P<RECEIVED>\S+)\])")

    def _parse_scan_report(self, line):
        if self._regex_helper.search_compiled(Nmap._re_scan_report, line):
            if "SCAN_REPORT" not in self.current_ret:
                self.current_ret["SCAN_REPORT"] = dict()
            self.current_ret["SCAN_REPORT"] = self._regex_helper.groupdict()
            raise ParsingDone

    # SYN Stealth Scan Timing: About 52.55% done; ETC: 14:18 (0:10:24 remaining)
    _re_syn_stealth_scan = re.compile(r"SYN Stealth Scan Timing: About (?P<DONE>[\d\.]+)% done; "
                                      r"ETC: (?P<ETC>[\d:]+) \((?P<REMAINING>[\d:]+) remaining\)")

    def _parse_syn_stealth_scan(self, line):
        if self._regex_helper.search_compiled(Nmap._re_syn_stealth_scan, line):
            if "SYN_STEALTH_SCAN" not in self.current_ret:
                self.current_ret["SYN_STEALTH_SCAN"] = dict()
            self.current_ret["SYN_STEALTH_SCAN"] = self._regex_helper.groupdict()
            raise ParsingDone

    _re_skipping_host = re.compile(r"Skipping host (?P<HOST>\S+) due to host timeout")

    def _parse_skipping_host(self, line):
        if self._regex_helper.search_compiled(Nmap._re_skipping_host, line):
            if "SKIPPING_HOST" not in self.current_ret:
                self.current_ret["SKIPPING_HOST"] = dict()
            self.current_ret["SKIPPING_HOST"] = self._regex_helper.groupdict()
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

COMMAND_KWARGS_host_up = {'option': '-d1 -p- -S 192.168.255.126',
                          'ip': '192.168.255.129'}

COMMAND_RESULT_host_up = {
    'PORTS': {
        'LINES': [
            '21/tcp    filtered ftp         no-response',
            '22/tcp    filtered ssh         no-response',
            '443/tcp   open     https       syn-ack',
            '3300/tcp  open     unknown     syn-ack',
            '6001/tcp  open     X11:1       syn-ack',
            '12000/tcp open     cce4x       syn-ack',
            '12001/tcp open     entextnetwk syn-ack',
            '15001/tcp filtered unknown     no-response',
            '15002/tcp filtered unknown     no-response',
            '15003/tcp filtered unknown     no-response',
            '15004/tcp filtered unknown     no-response',
            '15005/tcp filtered unknown     no-response',
            '15007/tcp filtered unknown     no-response'
        ],
        '21/tcp': {
            'PORT': '21',
            'REASON': 'no-response',
            'SERVICE': 'ftp',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        },
        '22/tcp': {
            'PORT': '22',
            'REASON': 'no-response',
            'SERVICE': 'ssh',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        },
        '443/tcp': {
            'PORT': '443',
            'REASON': 'syn-ack',
            'SERVICE': 'https',
            'STATE': 'open',
            'TYPE': 'tcp'
        },
        '3300/tcp': {
            'PORT': '3300',
            'REASON': 'syn-ack',
            'SERVICE': 'unknown',
            'STATE': 'open',
            'TYPE': 'tcp'
        },
        '6001/tcp': {
            'PORT': '6001',
            'REASON': 'syn-ack',
            'SERVICE': 'X11:1',
            'STATE': 'open',
            'TYPE': 'tcp'
        },
        '12000/tcp': {
            'PORT': '12000',
            'REASON': 'syn-ack',
            'SERVICE': 'cce4x',
            'STATE': 'open',
            'TYPE': 'tcp'
        },
        '12001/tcp': {
            'PORT': '12001',
            'REASON': 'syn-ack',
            'SERVICE': 'entextnetwk',
            'STATE': 'open',
            'TYPE': 'tcp'
        },
        '15001/tcp': {
            'PORT': '15001',
            'REASON': 'no-response',
            'SERVICE': 'unknown',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        },
        '15002/tcp': {
            'PORT': '15002',
            'REASON': 'no-response',
            'SERVICE': 'unknown',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        },
        '15003/tcp': {
            'PORT': '15003',
            'REASON': 'no-response',
            'SERVICE': 'unknown',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        },
        '15004/tcp': {
            'PORT': '15004',
            'REASON': 'no-response',
            'SERVICE': 'unknown',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        },
        '15005/tcp': {
            'PORT': '15005',
            'REASON': 'no-response',
            'SERVICE': 'unknown',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        },
        '15007/tcp': {
            'PORT': '15007',
            'REASON': 'no-response',
            'SERVICE': 'unknown',
            'STATE': 'filtered',
            'TYPE': 'tcp'
        }
    },
    'RAW_PACKETS': {
        'RCVD_NO': '65528',
        'RCVD_SIZE': '2.621MB',
        'SENT_NO': '65544',
        'SENT_SIZE': '2.884MB'
    }
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

COMMAND_KWARGS_host_down = {'option': '-d1 -p- -S 192.168.255.126',
                            'ip': '192.168.255.4'}

COMMAND_RESULT_host_down = {
    'RAW_PACKETS': {
        'RCVD_NO': '0',
        'RCVD_SIZE': '0B',
        'SENT_NO': '2',
        'SENT_SIZE': '56B'
    },
    'SCAN_REPORT': {
        'ADDRESS': '192.168.255.4',
        'HOST': 'down',
        'LINE': 'Nmap scan report for 192.168.255.4 [host down, received no-response]',
        'RECEIVED': 'no-response'
    }
}
