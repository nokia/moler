# -*- coding: utf-8 -*-
"""
Tcpdump command module.
"""

__author__ = "Julia Patacz, Michal Ernst, Marcin Usielski"
__copyright__ = "Copyright (C) 2018-2020, Nokia"
__email__ = "julia.patacz@nokia.com, michal.ernst@nokia.com, marcin.usielski@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Tcpdump(GenericUnixCommand):
    def __init__(
        self,
        connection,
        options=None,
        prompt=None,
        newline_chars=None,
        runner=None,
        break_exec_regex=None,
    ):
        """
        Tcpdump command.

        :param connection: moler connection to device, terminal when command is executed.
        :param options: parameter with which the command will be executed.
        :param prompt: expected prompt sending by device after command execution.
        :param newline_chars: Characters to split lines.
        :param runner: Runner to run command.
        :param break_exec_regex: if set then if occurs in on_new_line then break_cmd will be called.
        """
        super(Tcpdump, self).__init__(connection, prompt, newline_chars, runner)
        # Parameters defined by calling the command
        self.options = options
        self.packets_counter = 0
        self.break_exec_regex = break_exec_regex
        self.ret_required = False

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "tcpdump"
        if self.options:
            cmd = f"{cmd} {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_class_payload_flowlabel(line)
                self._parse_class_payload(line)
                self._parse_port_linktype_capture_size(line)
                self._parse_timestamp_src_dst_details(line)
                self._parse_timestamp_tos_ttl_id_offset_flags_proto_length(line)
                self._parse_src_dst_details(line)
                self._parse_root_delay_root_dipersion_ref_id(line)
                self._parse_header_timestamp_details(line)
                self._parse_packets(line)
            except ParsingDone:
                pass

        return super(Tcpdump, self).on_new_line(line, is_full_line)

    # listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
    _re_port_linktype_capture_size = re.compile(
        r"(?P<LISTENING>listening)\s+on\s+(?P<PORT>\S+),\s+(?P<LINK>link-type)\s+(?P<TYPE>.*),\s+"
        r"(?P<CAPTURE>capture size)\s+(?P<SIZE>.*)"
    )

    def _parse_port_linktype_capture_size(self, line):
        if self._regex_helper.search_compiled(
            Tcpdump._re_port_linktype_capture_size, line
        ):
            self.current_ret[
                self._regex_helper.group("LISTENING")
            ] = self._regex_helper.group("PORT")
            self.current_ret[
                self._regex_helper.group("LINK")
            ] = self._regex_helper.group("TYPE")
            self.current_ret[
                self._regex_helper.group("CAPTURE")
            ] = self._regex_helper.group("SIZE")
            raise ParsingDone

    # 13:16:22.176856 IP debdev.ntp > fwdns2.vbctv.in.ntp: NTPv4, Client, length 48
    _re_timestamp_src_dst_details = re.compile(
        r"(?P<TIMESTAMP>\d+:\d+:\d+.\d+)\s+IP\s+(?P<SRC>\S+)\s+>\s+(?P<DEST>\S+):\s+(?P<DETAILS>.*)"
    )

    def _parse_timestamp_src_dst_details(self, line):
        if self._regex_helper.search_compiled(
            Tcpdump._re_timestamp_src_dst_details, line
        ):
            self.packets_counter += 1
            self.current_ret[str(self.packets_counter)] = {}
            self.current_ret[str(self.packets_counter)][
                "timestamp"
            ] = self._regex_helper.group("TIMESTAMP")
            self.current_ret[str(self.packets_counter)][
                "source"
            ] = self._regex_helper.group("SRC")
            self.current_ret[str(self.packets_counter)][
                "destination"
            ] = self._regex_helper.group("DEST")
            self.current_ret[str(self.packets_counter)][
                "details"
            ] = self._regex_helper.group("DETAILS")
            raise ParsingDone

    # 13:31:33.176710 IP (tos 0xc0, ttl 64, id 4236, offset 0, flags [DF], proto UDP (17), length 76)

    _re_timestamp_tos_ttl_id_offset_flags_proto_length = re.compile(
        r"(?P<TIMESTAMP>\d+:\d+:\d+.\d+)\s+IP\s+\(tos\s+(?P<TOS>\S+),\s+ttl\s+(?P<TTL>\S+),\s+id\s+(?P<ID>\S+),\s+"
        r"offset\s+(?P<OFFSET>\S+),\s+flags\s+(?P<FLAGS>\S+),\s+proto\s+(?P<PROTO>\S+.*\S+),\s+"
        r"length\s+(?P<LENGTH>\S+)\)"
    )

    def _parse_timestamp_tos_ttl_id_offset_flags_proto_length(self, line):
        if self._regex_helper.search_compiled(
            Tcpdump._re_timestamp_tos_ttl_id_offset_flags_proto_length, line
        ):
            self.packets_counter += 1
            self.current_ret[str(self.packets_counter)] = {}
            self.current_ret[str(self.packets_counter)][
                "timestamp"
            ] = self._regex_helper.group("TIMESTAMP")
            self.current_ret[str(self.packets_counter)][
                "tos"
            ] = self._regex_helper.group("TOS")
            self.current_ret[str(self.packets_counter)][
                "ttl"
            ] = self._regex_helper.group("TTL")
            self.current_ret[str(self.packets_counter)][
                "id"
            ] = self._regex_helper.group("ID")
            self.current_ret[str(self.packets_counter)][
                "offset"
            ] = self._regex_helper.group("OFFSET")
            self.current_ret[str(self.packets_counter)][
                "flags"
            ] = self._regex_helper.group("FLAGS")
            self.current_ret[str(self.packets_counter)][
                "proto"
            ] = self._regex_helper.group("PROTO")
            self.current_ret[str(self.packets_counter)][
                "length"
            ] = self._regex_helper.group("LENGTH")
            raise ParsingDone

    # 12:08:35.714577 IP6 (class 0xba, flowlabel 0x7cb99, hlim 255, next-header SCTP (132) payload length: 64) 2a00:2222:2222:2222:2222:2222:2222:102.38472 > 2a00:2222:2222:2222:2222:2222:2222:63.38472: sctp (1) [HB REQ]
    _re_class_payload_flowlabel = re.compile(
        r"(?P<TIMESTAMP>\d+:\d+:\d+.\d+)\s+(?P<IP>IP\S)\s+\(class\s+(?P<CLASS>\S+),\s+flowlabel\s+(?P<FLOWLABEL>\S+),"
        r"\s+hlim\s+(?P<HLIM>\S+),\s+next-header\s+(?P<NEXT_HEADER>\S.*\S)\s+"
        r"payload length:\s+(?P<PAYLOAD_LENGTH>\d+)\)\s+(?P<SRC>\S+)\s+>\s+"
        r"(?P<DST>\S+):\s+(?P<DETAILS>.*)"
    )

    def _parse_class_payload_flowlabel(self, line):
        if self._regex_helper.search_compiled(
            Tcpdump._re_class_payload_flowlabel, line
        ):
            self.packets_counter += 1
            str_packets_counter = str(self.packets_counter)
            self.current_ret[str_packets_counter] = {}
            self.current_ret[str_packets_counter][
                "timestamp"
            ] = self._regex_helper.group("TIMESTAMP")
            self.current_ret[str_packets_counter]["class"] = self._regex_helper.group(
                "CLASS"
            )
            self.current_ret[str_packets_counter][
                "flowlabel"
            ] = self._regex_helper.group("FLOWLABEL")
            self.current_ret[str_packets_counter]["hlim"] = self._regex_helper.group(
                "HLIM"
            )
            self.current_ret[str_packets_counter][
                "next-header"
            ] = self._regex_helper.group("NEXT_HEADER")
            self.current_ret[str_packets_counter][
                "payload-length"
            ] = self._regex_helper.group("PAYLOAD_LENGTH")
            self.current_ret[str_packets_counter]["source"] = self._regex_helper.group(
                "SRC"
            )
            self.current_ret[str_packets_counter][
                "destination"
            ] = self._regex_helper.group("DST")
            self.current_ret[str_packets_counter]["details"] = self._regex_helper.group(
                "DETAILS"
            )
            raise ParsingDone

    # 12:08:35.714577 IP6 (class 0xba, hlim 255, next-header SCTP (132) payload length: 64) 2a00:2222:2222:2222:2222:2222:2222:102.38472 > 2a00:2222:2222:2222:2222:2222:2222:63.38472: sctp (1) [HB REQ
    _re_class_payload = re.compile(
        r"(?P<TIMESTAMP>\d+:\d+:\d+.\d+)\s+(?P<IP>IP\S)\s+\(class\s+(?P<CLASS>\S+),\s+hlim\s+(?P<HLIM>\S+),\s+"
        r"next-header\s+(?P<NEXT_HEADER>\S.*\S)\s+payload length:\s+(?P<PAYLOAD_LENGTH>\d+)\)\s+(?P<SRC>\S+)\s+>\s+"
        r"(?P<DST>\S+):\s+(?P<DETAILS>.*)"
    )

    def _parse_class_payload(self, line):
        if self._regex_helper.search_compiled(Tcpdump._re_class_payload, line):
            self.packets_counter += 1
            str_packets_counter = str(self.packets_counter)
            self.current_ret[str_packets_counter] = {}
            self.current_ret[str_packets_counter][
                "timestamp"
            ] = self._regex_helper.group("TIMESTAMP")
            self.current_ret[str_packets_counter]["class"] = self._regex_helper.group(
                "CLASS"
            )
            self.current_ret[str_packets_counter]["hlim"] = self._regex_helper.group(
                "HLIM"
            )
            self.current_ret[str_packets_counter][
                "next-header"
            ] = self._regex_helper.group("NEXT_HEADER")
            self.current_ret[str_packets_counter][
                "payload-length"
            ] = self._regex_helper.group("PAYLOAD_LENGTH")
            self.current_ret[str_packets_counter]["source"] = self._regex_helper.group(
                "SRC"
            )
            self.current_ret[str_packets_counter][
                "destination"
            ] = self._regex_helper.group("DST")
            self.current_ret[str_packets_counter]["details"] = self._regex_helper.group(
                "DETAILS"
            )
            raise ParsingDone

    # debdev.ntp > ntp.wdc1.us.leaseweb.net.ntp: [bad udp cksum 0x7aab -> 0x9cd3!] NTPv4, length 48
    _re_src_dst_details = re.compile(
        r"(?P<SRC>\S+)\s+>\s+(?P<DST>\S+):\s+(?P<DETAILS>\S+.*\S+)"
    )

    def _parse_src_dst_details(self, line):
        if self._regex_helper.search_compiled(Tcpdump._re_src_dst_details, line):
            str_packets_counter = str(self.packets_counter)
            if str_packets_counter not in self.current_ret:
                self.current_ret[str_packets_counter] = {}
            self.current_ret[str_packets_counter]["source"] = self._regex_helper.group(
                "SRC"
            )
            self.current_ret[str_packets_counter][
                "destination"
            ] = self._regex_helper.group("DST")
            self.current_ret[str_packets_counter]["details"] = self._regex_helper.group(
                "DETAILS"
            )
            raise ParsingDone

    # Root Delay: 0.000000, Root dispersion: 1.031906, Reference-ID: (unspec)
    _re_root_delay_root_dispersion_ref_id = re.compile(
        r"(?P<ROOT>Root Delay):\s+(?P<DELAY>\S+),\s+(?P<ROOT_2>Root dispersion):\s+(?P<DISPERSION>\S+),\s+(?P<REF>Reference-ID):\s+(?P<ID>\S+)"
    )

    def _parse_root_delay_root_dipersion_ref_id(self, line):
        if self._regex_helper.search_compiled(
            Tcpdump._re_root_delay_root_dispersion_ref_id, line
        ):
            self.current_ret[str(self.packets_counter)][
                self._regex_helper.group("ROOT")
            ] = self._regex_helper.group("DELAY")
            self.current_ret[str(self.packets_counter)][
                self._regex_helper.group("ROOT_2")
            ] = self._regex_helper.group("DISPERSION")
            self.current_ret[str(self.packets_counter)][
                self._regex_helper.group("REF")
            ] = self._regex_helper.group("ID")
            raise ParsingDone

    # Reference Timestamp:  0.000000000
    _re_timestamp_header_details = re.compile(
        r"(?P<TIMESTAMP_HEADER>\S+.*\S+\s+Timestamp):\s+(?P<DETAILS>\S+.*\S+)"
    )

    def _parse_header_timestamp_details(self, line):
        if self._regex_helper.search_compiled(
            Tcpdump._re_timestamp_header_details, line
        ):
            self.current_ret[str(self.packets_counter)][
                self._regex_helper.group("TIMESTAMP_HEADER")
            ] = self._regex_helper.group("DETAILS")
            raise ParsingDone

    # 5 packets received by filter
    _re_packets = re.compile(
        r"(?P<PCKT>\d+)\s+(?P<GROUP>packets captured|packets received by filter|packets dropped by kernel)"
    )

    def _parse_packets(self, line):
        if self._regex_helper.search_compiled(Tcpdump._re_packets, line):
            temp_pckt = self._regex_helper.group("PCKT")
            temp_group = self._regex_helper.group("GROUP")
            self.current_ret[temp_group] = temp_pckt
            raise ParsingDone


COMMAND_OUTPUT = """
ute@debdev:~$ tcpdump -c 4
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
13:16:22.176856 IP debdev.ntp > fwdns2.vbctv.in.ntp: NTPv4, Client, length 48
13:16:22.178451 IP debdev.44321 > rumcdc001.nsn-intra.net.domain: 34347+ PTR? 124.200.108.123.in-addr.arpa. (46)
13:16:22.178531 IP debdev.44321 > fihedc002.emea.nsn-net.net.domain: 34347+ PTR? 124.200.108.123.in-addr.arpa. (46)
13:16:22.178545 IP debdev.44321 > fihedc001.emea.nsn-net.net.domain: 34347+ PTR? 124.200.108.123.in-addr.arpa. (46)
4 packets captured
5 packets received by filter
0 packets dropped by kernel
ute@debdev:~$ """
COMMAND_KWARGS = {
    "options": "-c 4",
}
COMMAND_RESULT = {
    "packets captured": "4",
    "packets received by filter": "5",
    "packets dropped by kernel": "0",
    "listening": "eth0",
    "link-type": "EN10MB (Ethernet)",
    "capture size": "262144 bytes",
    "1": {
        "destination": "fwdns2.vbctv.in.ntp",
        "details": "NTPv4, Client, length 48",
        "source": "debdev.ntp",
        "timestamp": "13:16:22.176856",
    },
    "2": {
        "destination": "rumcdc001.nsn-intra.net.domain",
        "details": "34347+ PTR? 124.200.108.123.in-addr.arpa. (46)",
        "source": "debdev.44321",
        "timestamp": "13:16:22.178451",
    },
    "3": {
        "destination": "fihedc002.emea.nsn-net.net.domain",
        "details": "34347+ PTR? 124.200.108.123.in-addr.arpa. (46)",
        "source": "debdev.44321",
        "timestamp": "13:16:22.178531",
    },
    "4": {
        "destination": "fihedc001.emea.nsn-net.net.domain",
        "details": "34347+ PTR? 124.200.108.123.in-addr.arpa. (46)",
        "source": "debdev.44321",
        "timestamp": "13:16:22.178545",
    },
}

COMMAND_OUTPUT_vv = """ute@debdev:~$ sudo tcpdump -c 4 -vv
tcpdump: listening on eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
13:31:33.176710 IP (tos 0xc0, ttl 64, id 4236, offset 0, flags [DF], proto UDP (17), length 76)
    debdev.ntp > ntp.wdc1.us.leaseweb.net.ntp: [bad udp cksum 0x7aab -> 0x9cd3!] NTPv4, length 48
    Client, Leap indicator: clock unsynchronized (192), Stratum 0 (unspecified), poll 10 (1024s), precision -23
    Root Delay: 0.000000, Root dispersion: 1.031906, Reference-ID: (unspec)
      Reference Timestamp:  0.000000000
      Originator Timestamp: 0.000000000
      Receive Timestamp:    0.000000000
      Transmit Timestamp:   3741593493.176683590 (2018/07/26 13:31:33)
        Originator - Receive Timestamp:  0.000000000
        Originator - Transmit Timestamp: 3741593493.176683590 (2018/07/26 13:31:33)
13:31:36.177597 IP (tos 0xc0, ttl 64, id 37309, offset 0, flags [DF], proto UDP (17), length 76)
    debdev.ntp > dream.multitronic.fi.ntp: [ba udp cksum 0x6b9b -> 0x0677!] NTPv4, length 48
    Client, Leap indicator: clock unsynchronized (192), Stratum 0 (unspecified), poll 10 (1024s), precision -23
    Root Delay: 0.000000, Root dispersion: 1.031951, Reference-ID: (unspec)
      Reference Timestamp:  0.000000000
      Originator Timestamp: 0.000000000
      Receive Timestamp:    0.000000000
      Transmit Timestamp:   3741593496.177547928 (2018/07/26 13:31:36)
        Originator - Receive Timestamp:  0.000000000
        Originator - Transmit Timestamp: 3741593496.177547928 (2018/07/26 13:31:36)
13:31:36.178110 IP (tos 0x0, ttl 64, id 3207, offset 0, flags [DF], proto UDP (17), length 72)
    debdev.6869 > rumcdc001.nsn-intra.net.domain: [bad udp cksum 0x96f8 -> 0x405b!] 61207+ PTR? 38.138.28.213.in-addr.arpa. (44)
13:31:36.178211 IP (tos 0x0, ttl 64, id 63672, offset 0, flags [DF], proto UDP (17), length 72)
    debdev.6869 > fihedc002.emea.nsn-net.net.domain: [bad udp cksum 0x49fe -> 0x8d55!] 61207+ PTR? 38.138.28.213.in-addr.arpa. (44)
4 packets captured
6 packets received by filter
0 packets dropped by kernel
ute@debdev:~$ """
COMMAND_KWARGS_vv = {"options": "-c 4 -vv"}
COMMAND_RESULT_vv = {
    "packets captured": "4",
    "packets received by filter": "6",
    "packets dropped by kernel": "0",
    "listening": "eth0",
    "link-type": "EN10MB (Ethernet)",
    "capture size": "262144 bytes",
    "1": {
        "Originator - Receive Timestamp": "0.000000000",
        "Originator - Transmit Timestamp": "3741593493.176683590 (2018/07/26 13:31:33)",
        "Originator Timestamp": "0.000000000",
        "Receive Timestamp": "0.000000000",
        "Reference Timestamp": "0.000000000",
        "Reference-ID": "(unspec)",
        "Root Delay": "0.000000",
        "Root dispersion": "1.031906",
        "Transmit Timestamp": "3741593493.176683590 (2018/07/26 13:31:33)",
        "destination": "ntp.wdc1.us.leaseweb.net.ntp",
        "details": "[bad udp cksum 0x7aab -> 0x9cd3!] NTPv4, length 48",
        "flags": "[DF]",
        "id": "4236",
        "length": "76",
        "offset": "0",
        "proto": "UDP (17)",
        "source": "debdev.ntp",
        "timestamp": "13:31:33.176710",
        "tos": "0xc0",
        "ttl": "64",
    },
    "2": {
        "Originator - Receive Timestamp": "0.000000000",
        "Originator - Transmit Timestamp": "3741593496.177547928 (2018/07/26 13:31:36)",
        "Originator Timestamp": "0.000000000",
        "Receive Timestamp": "0.000000000",
        "Reference Timestamp": "0.000000000",
        "Reference-ID": "(unspec)",
        "Root Delay": "0.000000",
        "Root dispersion": "1.031951",
        "Transmit Timestamp": "3741593496.177547928 (2018/07/26 13:31:36)",
        "destination": "dream.multitronic.fi.ntp",
        "details": "[ba udp cksum 0x6b9b -> 0x0677!] NTPv4, length 48",
        "flags": "[DF]",
        "id": "37309",
        "length": "76",
        "offset": "0",
        "proto": "UDP (17)",
        "source": "debdev.ntp",
        "timestamp": "13:31:36.177597",
        "tos": "0xc0",
        "ttl": "64",
    },
    "3": {
        "destination": "rumcdc001.nsn-intra.net.domain",
        "details": "[bad udp cksum 0x96f8 -> 0x405b!] 61207+ PTR? 38.138.28.213.in-addr.arpa. (44)",
        "flags": "[DF]",
        "id": "3207",
        "length": "72",
        "offset": "0",
        "proto": "UDP (17)",
        "source": "debdev.6869",
        "timestamp": "13:31:36.178110",
        "tos": "0x0",
        "ttl": "64",
    },
    "4": {
        "destination": "fihedc002.emea.nsn-net.net.domain",
        "details": "[bad udp cksum 0x49fe -> 0x8d55!] 61207+ PTR? 38.138.28.213.in-addr.arpa. (44)",
        "flags": "[DF]",
        "id": "63672",
        "length": "72",
        "offset": "0",
        "proto": "UDP (17)",
        "source": "debdev.6869",
        "timestamp": "13:31:36.178211",
        "tos": "0x0",
        "ttl": "64",
    },
}

COMMAND_KWARGS_break = {"break_exec_regex": r"PTR homerouter\.cpe"}

COMMAND_OUTPUT_break = """tcpdump
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on enp0s3, link-type EN10MB (Ethernet), capture size 262144 bytes
11:23:15.134680 IP debian > dns.google: ICMP echo request, id 24522, seq 7, length 64
11:23:15.135452 IP debian.38676 > homerouter.cpe.domain: 2034+ PTR? 8.8.8.8.in-addr.arpa. (38)
11:23:15.162925 IP dns.google > debian: ICMP echo reply, id 24522, seq 7, length 64
11:23:15.167852 IP homerouter.cpe.domain > debian.38676: 2034 1/0/0 PTR dns.google. (62)
11:23:15.168109 IP debian.59644 > homerouter.cpe.domain: 59898+ PTR? 15.2.0.10.in-addr.arpa. (40)
11:23:15.223710 IP homerouter.cpe.domain > debian.59644: 59898 NXDomain 0/0/0 (40)
11:23:15.224726 IP debian.57873 > homerouter.cpe.domain: 43660+ PTR? 1.8.168.192.in-addr.arpa. (42)
11:23:15.230351 IP homerouter.cpe.domain > debian.57873: 43660- 1/0/0 PTR homerouter.cpe. (70)
11:21:24.724157 IP6 (class 0xba, flowlabel 0x7cb99, hlim 255, next-header SCTP (132) payload length: 64) 2a00:2222:2222:2222:2222:2222:2222:102.38472 > 2a00:2222:2222:2222:2222:2222:2222:63.38472: sctp (1) [HB REQ]
^C
9 packets captured
9 packets received by filter
0 packets dropped by kernel
moler_bash#"""

COMMAND_RESULT_break = {
    "1": {
        "destination": "dns.google",
        "details": "ICMP echo request, id 24522, seq 7, length 64",
        "source": "debian",
        "timestamp": "11:23:15.134680",
    },
    "2": {
        "destination": "homerouter.cpe.domain",
        "details": "2034+ PTR? 8.8.8.8.in-addr.arpa. (38)",
        "source": "debian.38676",
        "timestamp": "11:23:15.135452",
    },
    "3": {
        "destination": "debian",
        "details": "ICMP echo reply, id 24522, seq 7, length 64",
        "source": "dns.google",
        "timestamp": "11:23:15.162925",
    },
    "4": {
        "destination": "debian.38676",
        "details": "2034 1/0/0 PTR dns.google. (62)",
        "source": "homerouter.cpe.domain",
        "timestamp": "11:23:15.167852",
    },
    "5": {
        "destination": "homerouter.cpe.domain",
        "details": "59898+ PTR? 15.2.0.10.in-addr.arpa. (40)",
        "source": "debian.59644",
        "timestamp": "11:23:15.168109",
    },
    "6": {
        "destination": "debian.59644",
        "details": "59898 NXDomain 0/0/0 (40)",
        "source": "homerouter.cpe.domain",
        "timestamp": "11:23:15.223710",
    },
    "7": {
        "destination": "homerouter.cpe.domain",
        "details": "43660+ PTR? 1.8.168.192.in-addr.arpa. (42)",
        "source": "debian.57873",
        "timestamp": "11:23:15.224726",
    },
    "8": {
        "destination": "debian.57873",
        "details": "43660- 1/0/0 PTR homerouter.cpe. (70)",
        "source": "homerouter.cpe.domain",
        "timestamp": "11:23:15.230351",
    },
    "9": {
        "class": "0xba",
        "destination": "2a00:2222:2222:2222:2222:2222:2222:63.38472",
        "details": "sctp (1) [HB REQ]",
        "flowlabel": "0x7cb99",
        "hlim": "255",
        "next-header": "SCTP (132)",
        "payload-length": "64",
        "source": "2a00:2222:2222:2222:2222:2222:2222:102.38472",
        "timestamp": "11:21:24.724157",
    },
    "capture size": "262144 bytes",
    "link-type": "EN10MB (Ethernet)",
    "listening": "enp0s3",
    "packets captured": "9",
    "packets dropped by kernel": "0",
    "packets received by filter": "9",
}

COMMAND_KWARGS_ni = {"options": "-ni enp0s3"}

COMMAND_OUTPUT_ni = """tcpdump -ni enp0s3

dropped privs to tcpdump
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on enp0s3, link-type EN10MB (Ethernet), capture size 262144 bytes

12:28:56.926353 IP6 :: > ff02::1:ff22:102: ICMP6, neighbor solicitation, who has 2a00:2222:2222:2222:2222:2222:2222:102, length 24
12:28:56.926391 IP6 :: > ff02::1:ffa5:aa39: ICMP6, neighbor solicitation, who has fe80::f816:3eff:fea5:aa39, length 24

12:29:14.431126 IP6 2a00:2222:2222:2222:2222:2222:2222:102.38472 > 2a00:2222:2222:2222:2222:2222:2222:63.38472: sctp (1) [HB REQ]
12:29:14.431656 IP6 2a00:2222:2222:2222:2222:2222:2222:63.38472 > 2a00:2222:2222:2222:2222:2222:2222:102.38472: sctp (1) [HB ACK]

12:29:14.582584 IP6 2a00:2222:2222:2222:2222:2222:2222:63.38472 > 2a00:2222:2222:2222:2222:2222:2222:102.38472: sctp (1) [HB REQ]
12:29:14.582642 IP6 2a00:2222:2222:2222:2222:2222:2222:102.38472 > 2a00:2222:2222:2222:2222:2222:2222:63.38472: sctp (1) [HB ACK]
12:29:14.714577 IP6 (class 0xba, hlim 255, next-header SCTP (132) payload length: 64) 2a00:2222:2222:2222:2222:2222:2222:102.38472 > 2a00:2222:2222:2222:2222:2222:2222:63.38472: sctp (1) [HB REQ

                 |Session terminated, terminating shell...
                 |6 packets captured
                 |6 packets received by filter
                 |0 packets dropped by kernel
moler_bash#"""

COMMAND_RESULT_ni = {
    "0": {
        "destination": "2a00:2222:2222:2222:2222:2222:2222:63.38472",
        "details": "sctp (1) [HB ACK]",
        "source": "2a00:2222:2222:2222:2222:2222:2222:102.38472",
    },
    "1": {
        "class": "0xba",
        "destination": "2a00:2222:2222:2222:2222:2222:2222:63.38472",
        "details": "sctp (1) [HB REQ",
        "hlim": "255",
        "next-header": "SCTP (132)",
        "payload-length": "64",
        "source": "2a00:2222:2222:2222:2222:2222:2222:102.38472",
        "timestamp": "12:29:14.714577",
    },
    "capture size": "262144 bytes",
    "link-type": "EN10MB (Ethernet)",
    "listening": "enp0s3",
    "packets captured": "6",
    "packets dropped by kernel": "0",
    "packets received by filter": "6",
}
