# -*- coding: utf-8 -*-
"""
Nping command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper


class Nping(GenericUnixCommand):

    def __init__(self, connection, destination, options=None, prompt=None, newline_chars=None, runner=None):
        """
        Nping command.
        :param connection: moler connection to device, terminal when command is executed.
        :param destination: address (IP v4 or v6) of unit to ping.
        :param options: options of ping command for unix.
        :param prompt: prompt on system where ping is executed.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command
        """
        super(Nping, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.destination = destination
        self._converter_helper = ConverterHelper.get_converter_helper()
        self._current_statistics = None

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "nping"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        cmd = "{} {}".format(cmd, self.destination)
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
                self._parse_packets_summary(line=line)
                self._parse_addresses(line=line)
                self._parse_statistics_header(line=line)
                self._parse_statistics(line=line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Nping, self).on_new_line(line, is_full_line)

    # Raw packets sent: 4 (160B) | Rcvd: 3 (128B) | Lost: 1 (25.00%)
    _re_packets_sent = re.compile(r"Raw packets sent:\s+(?P<PKT_SENT>\d+)\s+\((?P<SENT_SIZE>\d+)(?P<SENT_UNIT>\w)\)\s+"
                                  r"\|\s+Rcvd:\s+(?P<PKT_RCVD>\d+)\s+\((?P<RCVD_SIZE>\d+)(?P<RCVD_UNIT>\w)\)\s+\|"
                                  r"\s+Lost:\s+(?P<LOST_PKT>\d+)\s+\((?P<LOST_PERCENTAGE>\d+\.\d+)%\)")

    def _parse_packets_summary(self, line):
        if self._regex_helper.search_compiled(Nping._re_packets_sent, line):
            self.current_ret['STATISTICS'] = dict() if 'STATISTICS' not in self.current_ret else \
                self.current_ret['STATISTICS']
            self.current_ret['STATISTICS']['PKT_SENT'] = self._converter_helper.to_number(
                self._regex_helper.group("PKT_SENT"), raise_exception=False)
            self.current_ret['STATISTICS']['PKT_SENT_SIZE'] = self._converter_helper.to_number(
                self._regex_helper.group("SENT_SIZE"), raise_exception=False)
            self.current_ret['STATISTICS']['PKT_SENT_UNIT'] = self._regex_helper.group("SENT_UNIT")
            self.current_ret['STATISTICS']['PKT_RCVD'] = self._converter_helper.to_number(
                self._regex_helper.group("PKT_RCVD"), raise_exception=False)
            self.current_ret['STATISTICS']['PKT_RCVD_SIZE'] = self._converter_helper.to_number(
                self._regex_helper.group("RCVD_SIZE"), raise_exception=False)
            self.current_ret['STATISTICS']['PKT_RCVD_UNIT'] = self._regex_helper.group("RCVD_UNIT")
            self.current_ret['STATISTICS']['LOST_PKT'] = self._converter_helper.to_number(
                self._regex_helper.group("LOST_PKT"), raise_exception=False)
            self.current_ret['STATISTICS']['LOST_PERCENTAGE'] = self._converter_helper.to_number(
                self._regex_helper.group("LOST_PERCENTAGE"), raise_exception=False)
            raise ParsingDone()

    # Statistics for host nokia.com (162.13.40.196):
    _re_statistics_header = re.compile(
        r"Statistics for host (?P<HOST>\S+) \((?P<ADDRESS>\S+)\):")

    def _parse_statistics_header(self, line):
        if self._regex_helper.search_compiled(Nping._re_statistics_header, line):
            host = self._regex_helper.group("HOST")
            self._current_statistics = host
            if 'STATISTICS' not in self.current_ret:
                self.current_ret['STATISTICS'] = dict()
            if 'HOSTS' not in self.current_ret['STATISTICS']:
                self.current_ret['STATISTICS']['HOSTS'] = dict()
            self.current_ret['STATISTICS']['HOSTS'][host] = dict()
            self.current_ret['STATISTICS']['HOSTS'][host]['address'] = self._regex_helper.group("ADDRESS")
            raise ParsingDone()

    # Probes Sent: 2 | Rcvd: 2 | Lost: 0  (0.00%)
    _re_statistics = re.compile(r"(\w.*\w|\S+):\s+\S+\s+\|\s+(\w.*\w|\S+):\s+\S+")

    # Lost: 0  (0.00%)
    _re_statistics_part = re.compile(r'(?!_)(?P<KEY>\w.*\w|\S+)\s*:\s*(?P<VALUE>\S.*\S|\S+)')

    def _parse_statistics(self, line):
        if self._regex_helper.search_compiled(Nping._re_statistics, line):
            for part in line.split('|'):
                if self._regex_helper.search_compiled(Nping._re_statistics_part, part):
                    key = self._regex_helper.group("KEY")
                    value = self._regex_helper.group("VALUE")
                    if self._current_statistics:
                        self.current_ret['STATISTICS']['HOSTS'][self._current_statistics][key] = value
                    else:
                        if 'STATISTICS' not in self.current_ret:
                            self.current_ret['STATISTICS'] = dict()
                        if 'HOST' not in self.current_ret['STATISTICS']:
                            self.current_ret['STATISTICS']['HOST'] = dict()
                        self.current_ret['STATISTICS']['HOST'][key] = value
            raise ParsingDone()

    # Nping done: 2 IP addresses pinged in 3.77 seconds
    _re_addresses = re.compile(r"(?P<ADDRESSES>\d+) IP address(e?s?) pinged in\s+(?P<TIME>\d+\.\d+)\s+(?P<UNIT>\w+)")

    def _parse_addresses(self, line):
        if self._regex_helper.search_compiled(Nping._re_addresses, line):
            self.current_ret['STATISTICS']['NO_OF_ADDRESSES'] = self._converter_helper.to_number(
                self._regex_helper.group("ADDRESSES"), raise_exception=False)
            self.current_ret['STATISTICS']['PING_TIME'] = self._converter_helper.to_number(
                self._regex_helper.group("TIME"), raise_exception=False)
            self.current_ret['STATISTICS']['PING_TIME_UNIT'] = self._regex_helper.group("UNIT")
            raise ParsingDone()


COMMAND_OUTPUT_options = """nping -c 1 --tcp -p 80,433 scanme.nmap.org nokia.com

Starting Nping 0.7.40 ( https://nmap.org/nping ) at 2021-06-14 10:50 CEST
SENT (0.0809s) TCP 10.0.2.15:49537 > 45.33.32.156:80 S ttl=64 id=14176 iplen=40  seq=4066470806 win=1480
RCVD (0.4684s) TCP 45.33.32.156:80 > 10.0.2.15:49537 SA ttl=64 id=22 iplen=44  seq=1856001 win=65535 <mss 1460>
SENT (1.0812s) TCP 10.0.2.15:49537 > 162.13.40.196:80 S ttl=64 id=14176 iplen=40  seq=4066470806 win=1480
RCVD (1.2853s) TCP 162.13.40.196:80 > 10.0.2.15:49537 SA ttl=64 id=23 iplen=44  seq=1984001 win=65535 <mss 1460>
SENT (2.0836s) TCP 10.0.2.15:49537 > 45.33.32.156:433 S ttl=64 id=14176 iplen=40  seq=4066470806 win=1480
SENT (3.0850s) TCP 10.0.2.15:49537 > 162.13.40.196:433 S ttl=64 id=14176 iplen=40  seq=4066470806 win=1480
RCVD (3.7339s) TCP 45.33.32.156:433 > 10.0.2.15:49537 RA ttl=255 id=24 iplen=40  seq=0 win=0

Statistics for host scanme.nmap.org (45.33.32.156):
 |  Probes Sent: 2 | Rcvd: 2 | Lost: 0  (0.00%)
 |_ Max rtt: 1650.226ms | Min rtt: 387.435ms | Avg rtt: 1018.830ms
Statistics for host nokia.com (162.13.40.196):
 |  Probes Sent: 2 | Rcvd: 1 | Lost: 1  (50.00%)
 |_ Max rtt: 203.962ms | Min rtt: 203.962ms | Avg rtt: 203.962ms
Raw packets sent: 4 (160B) | Rcvd: 3 (128B) | Lost: 1 (25.00%)
Nping done: 2 IP addresses pinged in 3.77 seconds
moler_bash#"""

COMMAND_KWARGS_options = {'destination': 'scanme.nmap.org nokia.com', 'options': '-c 1 --tcp -p 80,433'}

COMMAND_RESULT_options = {
    'STATISTICS': {
        'HOSTS': {
            'nokia.com': {
                'Lost': '1  (50.00%)',
                'Probes Sent': '2',
                'Rcvd': '1',
                'Avg rtt': '203.962ms',
                'Max rtt': '203.962ms',
                'Min rtt': '203.962ms',
                'address': '162.13.40.196'
            },
            'scanme.nmap.org': {
                'Lost': '0  (0.00%)',
                'Probes Sent': '2',
                'Rcvd': '2',
                'Avg rtt': '1018.830ms',
                'Max rtt': '1650.226ms',
                'Min rtt': '387.435ms',
                'address': '45.33.32.156'
            }
        },
        'LOST_PERCENTAGE': 25.0,
        'LOST_PKT': 1,
        'PKT_RCVD': 3,
        'PKT_RCVD_SIZE': 128,
        'PKT_RCVD_UNIT': 'B',
        'PKT_SENT': 4,
        'PKT_SENT_SIZE': 160,
        'PKT_SENT_UNIT': 'B',
        'NO_OF_ADDRESSES': 2,
        'PING_TIME': 3.77,
        'PING_TIME_UNIT': 'seconds',

    }
}

COMMAND_OUTPUT_no_options = """nping nokia.com

Starting Nping 0.7.40 ( https://nmap.org/nping ) at 2021-06-14 13:57 CEST
SENT (0.0337s) ICMP [10.0.2.15 > 162.13.40.196 Echo request (type=8/code=0) id=21967 seq=1] IP [ttl=64 id=45170 iplen=28 ]
RCVD (0.2219s) ICMP [162.13.40.196 > 10.0.2.15 Echo reply (type=0/code=0) id=21967 seq=1] IP [ttl=45 id=195 iplen=28 ]
SENT (1.0352s) ICMP [10.0.2.15 > 162.13.40.196 Echo request (type=8/code=0) id=21967 seq=2] IP [ttl=64 id=45170 iplen=28 ]
RCVD (1.2407s) ICMP [162.13.40.196 > 10.0.2.15 Echo reply (type=0/code=0) id=21967 seq=2] IP [ttl=45 id=196 iplen=28 ]
SENT (2.0368s) ICMP [10.0.2.15 > 162.13.40.196 Echo request (type=8/code=0) id=21967 seq=3] IP [ttl=64 id=45170 iplen=28 ]
RCVD (2.2604s) ICMP [162.13.40.196 > 10.0.2.15 Echo reply (type=0/code=0) id=21967 seq=3] IP [ttl=45 id=197 iplen=28 ]
SENT (3.0396s) ICMP [10.0.2.15 > 162.13.40.196 Echo request (type=8/code=0) id=21967 seq=4] IP [ttl=64 id=45170 iplen=28 ]
RCVD (3.2800s) ICMP [162.13.40.196 > 10.0.2.15 Echo reply (type=0/code=0) id=21967 seq=4] IP [ttl=45 id=198 iplen=28 ]
SENT (4.0409s) ICMP [10.0.2.15 > 162.13.40.196 Echo request (type=8/code=0) id=21967 seq=5] IP [ttl=64 id=45170 iplen=28 ]
RCVD (4.3039s) ICMP [162.13.40.196 > 10.0.2.15 Echo reply (type=0/code=0) id=21967 seq=5] IP [ttl=45 id=199 iplen=28 ]

Max rtt: 262.930ms | Min rtt: 188.069ms | Avg rtt: 224.007ms
Raw packets sent: 5 (140B) | Rcvd: 5 (140B) | Lost: 0 (0.00%)
Nping done: 1 IP address pinged in 4.34 seconds
moler_bash#"""

COMMAND_KWARGS_no_options = {
    'destination': 'nokia.com',
}

COMMAND_RESULT_no_options = {
    'STATISTICS': {
        'HOST': {
            'Avg rtt': '224.007ms',
            'Max rtt': '262.930ms',
            'Min rtt': '188.069ms'
        },
        'LOST_PERCENTAGE': 0.0,
        'LOST_PKT': 0,
        'NO_OF_ADDRESSES': 1,
        'PING_TIME': 4.34,
        'PING_TIME_UNIT': 'seconds',
        'PKT_RCVD': 5,
        'PKT_RCVD_SIZE': 140,
        'PKT_RCVD_UNIT': 'B',
        'PKT_SENT': 5,
        'PKT_SENT_SIZE': 140,
        'PKT_SENT_UNIT': 'B'
    }
}
