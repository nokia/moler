# -*- coding: utf-8 -*-

__author__ = 'Dariusz Rosinski, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'dariusz.rosinski@nokia.com, marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone

"""
ps command module.
Commad Ps is parsed to list of dictionary.
Each dictionary in list contains all columns defined in columns printed in first line of command result
Last column may contain more parameters while this field is responsible for process name
Form of line result:
{'UID' : 'avahi-a+', 'PID' : 3597, 'PPID' : 1, 'C' : 0, 'STIME' : 2017, 'TTY' : '?', 'TIME' : ' 00:00:45',
'CMD': 'avahi-autoipd: [ens4] sleeping'}
Each key is derived from first line of executed ps command so accessing it needs ps command with option
result knowledge
"""


class Ps(GenericUnixCommand):
    """Unix command ps."""

    def __init__(self, connection=None, options='', prompt=None, newline_chars=None, runner=None):
        """
        Represents Unix command ps.

        :param connection: moler connection to device, terminal where command is executed
        :param options: ps command options as string
        :param prompt: prompt (on system where command runs).
        :param newline_chars: characters to split lines
        :param runner: Runner to run command
        """
        super(Ps, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.current_ret = list()
        self.options = options
        self._headers = None
        self._header_pos = None

    def on_new_line(self, line, is_full_line):
        """
        Parses output from command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_headers(line=line)
                self._parse_line_data(line=line)
            except ParsingDone:
                pass
        return super(Ps, self).on_new_line(line, is_full_line)

    # USER       PID    VSZ SZ  MEM   RSS COMMAND
    _re_headers = re.compile(r"(?P<HEADERS>\s*(\S+)\s*)")

    def _parse_headers(self, line):
        """
        Parse headers from line of output.

        :param line: Line from connection.
        :return: None
        """
        if self._headers is None:
            if self._regex_helper.search_compiled(Ps._re_headers, line):
                matched = re.findall(r"\s*(\S+)\s*", line)
                if matched:
                    self._headers = matched
                    self._header_pos = list()
                    previous_pos = 0
                    for header in self._headers:
                        position = line.find(header, previous_pos)
                        self._header_pos.append(position)
                        previous_pos = position + len(header)
                    raise ParsingDone()

    # 123
    _re_integer = re.compile(r"^[+\-]?\d+$")

    # 2.5
    _re_float = re.compile(r"^[+\-]?(\d+\.\d+|\.\d+|\d+\.)$")

    def _parse_line_data(self, line):
        """
        Parse data from output.

        :param line: Line from connection.
        :return: None
        """
        if self._headers:
            item = dict()
            max_column = len(self._headers)
            previous_end_pos = 0
            for column_nr in range(max_column):
                org_start_pos = self._header_pos[column_nr]
                start_pos = line.find(" ", previous_end_pos)
                if start_pos > org_start_pos or start_pos < 0:
                    start_pos = org_start_pos
                if column_nr < max_column - 1:
                    end_pos = self._header_pos[column_nr + 1]
                    end_pos = line.rfind(" ", start_pos, end_pos + 1)
                else:
                    end_pos = len(line)

                content = line[start_pos:end_pos]
                content = content.strip()
                if self._regex_helper.match_compiled(Ps._re_float, content):
                    content = float(content)
                elif self._regex_helper.match_compiled(Ps._re_integer, content):
                    content = int(content)
                item[self._headers[column_nr]] = content
                previous_end_pos = end_pos
            self.current_ret.append(item)
            raise ParsingDone()

    def build_command_string(self):
        """
        Builds string with command.

        :return: String with command.
        """
        cmd = "ps"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd


COMMAND_OUTPUT = '''ps -o user,pid,vsz,osz,pmem,rss,cmd -e
 USER       PID    VSZ SZ  MEM   RSS COMMAND
 root         1   1664  -  0.1   572 init [3]
 root         2      0  -  0.0     0 [ksoftirqd/0]
 root         3      0  -  0.0     0 [desched/0]
 root         4      0  -  0.0     0 [events/0]
 root         5      0  -  0.0     0 [khelper]
 root        10      0  -  0.0     0 [kthread]
 root        34      0  -  0.0     0 [kblockd/0]
 root        67      0  -  0.0     0 [pdflush]
 root        68      0  -  0.0     0 [pdflush]
 root        70      0  -  0.0     0 [aio/0]
 root        69      0  -  0.0     0 [kswapd0]
 root       665      0  -  0.0     0 [kjournald]
 bin        814   1908  -  0.1   544 /sbin/portmap
 root       847   1772  -  0.1   712 /sbin/syslogd -r
 root       855   1664  -  0.0   500 /sbin/klogd -x
 client@server>'''

COMMAND_KWARGS = {"options": "-o user,pid,vsz,osz,pmem,rss,cmd -e"}

COMMAND_RESULT = [
    {'USER': 'root', 'PID': 1, 'VSZ': 1664, 'SZ': '-', 'MEM': 0.1, 'RSS': 572, 'COMMAND': 'init [3]'},
    {'USER': 'root', 'PID': 2, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[ksoftirqd/0]'},
    {'USER': 'root', 'PID': 3, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[desched/0]'},
    {'USER': 'root', 'PID': 4, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[events/0]'},
    {'USER': 'root', 'PID': 5, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[khelper]'},
    {'USER': 'root', 'PID': 10, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[kthread]'},
    {'USER': 'root', 'PID': 34, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[kblockd/0]'},
    {'USER': 'root', 'PID': 67, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[pdflush]'},
    {'USER': 'root', 'PID': 68, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[pdflush]'},
    {'USER': 'root', 'PID': 70, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[aio/0]'},
    {'USER': 'root', 'PID': 69, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[kswapd0]'},
    {'USER': 'root', 'PID': 665, 'VSZ': 0, 'SZ': '-', 'MEM': 0.0, 'RSS': 0, 'COMMAND': '[kjournald]'},
    {'USER': 'bin', 'PID': 814, 'VSZ': 1908, 'SZ': '-', 'MEM': 0.1, 'RSS': 544, 'COMMAND': '/sbin/portmap'},
    {'USER': 'root', 'PID': 847, 'VSZ': 1772, 'SZ': '-', 'MEM': 0.1, 'RSS': 712, 'COMMAND': '/sbin/syslogd -r'},
    {'USER': 'root', 'PID': 855, 'VSZ': 1664, 'SZ': '-', 'MEM': 0.0, 'RSS': 500, 'COMMAND': '/sbin/klogd -x'}]

COMMAND_OUTPUT_V2 = '''ps -ef
UID        PID  PPID  C STIME TTY          TIME CMD
avahi-a+  3597     1  0  2017 ?        00:00:45 avahi-autoipd: [ens4] sleeping
root      3598  3597  0  2017 ?        00:00:00 avahi-autoipd: [ens4] callout dispatcher
root      3681     1  0  2017 ?        00:00:17 /sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf
root      3812     1  0  2017 ?        00:00:00 /usr/sbin/xinetd -stayalive -dontfork
root      3814     1  0  2017 ?        00:00:00 /usr/sbin/vsftpd /etc/vsftpd.conf
root      3826     1  0  2017 ?        00:00:02 /usr/sbin/sshd -D
root      3835     2  0  2017 ?        00:00:00 [cifsiod]
root      3867     1  0  2017 ?        00:00:18 /usr/sbin/cron -n
root      3870     1  0  2017 tty1     00:00:00 /sbin/agetty --noclear tty1 linux
avahi-a+  4592     1  0  2017 ?        00:17:15 avahi-autoipd: [ens3] sleeping
root      4593  4592  0  2017 ?        00:00:00 avahi-autoipd: [ens3] callout dispatcher
root      4648     1  0  2017 ?        00:00:00 /sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-
root      5823     2  0 Mar09 ?        00:00:03 [kworker/u8:2]
client@server>'''

COMMAND_KWARGS_V2 = {"options": "-ef"}

COMMAND_RESULT_V2 = [
    {'UID': 'avahi-a+', 'PID': 3597, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:45',
     'CMD': 'avahi-autoipd: [ens4] sleeping'},
    {'UID': 'root', 'PID': 3598, 'PPID': 3597, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': 'avahi-autoipd: [ens4] callout dispatcher'},
    {'UID': 'root', 'PID': 3681, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:17',
     'CMD': '/sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf'},
    {'UID': 'root', 'PID': 3812, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': '/usr/sbin/xinetd -stayalive -dontfork'},
    {'UID': 'root', 'PID': 3814, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': '/usr/sbin/vsftpd /etc/vsftpd.conf'},
    {'UID': 'root', 'PID': 3826, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:02',
     'CMD': '/usr/sbin/sshd -D'},
    {'UID': 'root', 'PID': 3835, 'PPID': 2, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00', 'CMD': '[cifsiod]'},
    {'UID': 'root', 'PID': 3867, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:18',
     'CMD': '/usr/sbin/cron -n'},
    {'UID': 'root', 'PID': 3870, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': 'tty1', 'TIME': '00:00:00',
     'CMD': '/sbin/agetty --noclear tty1 linux'},
    {'UID': 'avahi-a+', 'PID': 4592, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:17:15',
     'CMD': 'avahi-autoipd: [ens3] sleeping'},
    {'UID': 'root', 'PID': 4593, 'PPID': 4592, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': 'avahi-autoipd: [ens3] callout dispatcher'},
    {'UID': 'root', 'PID': 4648, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': '/sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-'},
    {'UID': 'root', 'PID': 5823, 'PPID': 2, 'C': 0, 'STIME': 'Mar09', 'TTY': '?', 'TIME': '00:00:03',
     'CMD': '[kworker/u8:2]'},

]

COMMAND_OUTPUT_V3 = '''ps -ef
UID        PID  PPID  C STIME TTY   CMD                                                                                                                 TIME
avahi-a+  3597     1  0  2017 ?     avahi-autoipd: [ens4] sleeping                                                                                      00:00:45
root      3598  3597  0  2017 ?     avahi-autoipd: [ens4] callout dispatcher                                                                            00:00:00
root      3681     1  0  2017 ?     /sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf               00:00:17
root      3812     1  0  2017 ?     /usr/sbin/xinetd -stayalive -dontfork                                                                               00:00:00
root      3814     1  0  2017 ?     /usr/sbin/vsftpd /etc/vsftpd.conf                                                                                   00:00:00
root      3826     1  0  2017 ?     /usr/sbin/sshd -D                                                                                                   00:00:02
root      3835     2  0  2017 ?     [cifsiod]                                                                                                           00:00:00
root      3867     1  0  2017 ?     /usr/sbin/cron -n                                                                                                   00:00:18
root      3870     1  0  2017 tty1  /sbin/agetty --noclear tty1 linux                                                                                   00:00:00
avahi-a+  4592     1  0  2017 ?     avahi-autoipd: [ens3] sleeping                                                                                      00:17:15
root      4593  4592  0  2017 ?     avahi-autoipd: [ens3] callout dispatcher                                                                            00:00:00
root      4648     1  0  2017 ?     /sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-              00:00:00
root      5823     2  0 Mar09 ?     [kworker/u8:2]                                                                                                      00:00:03
client@server>'''

COMMAND_KWARGS_V3 = {"options": "-ef"}

COMMAND_RESULT_V3 = [
    {'UID': 'avahi-a+', 'PID': 3597, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:45',
     'CMD': 'avahi-autoipd: [ens4] sleeping'},
    {'UID': 'root', 'PID': 3598, 'PPID': 3597, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': 'avahi-autoipd: [ens4] callout dispatcher'},
    {'UID': 'root', 'PID': 3681, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:17',
     'CMD': '/sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf'},
    {'UID': 'root', 'PID': 3812, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': '/usr/sbin/xinetd -stayalive -dontfork'},
    {'UID': 'root', 'PID': 3814, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': '/usr/sbin/vsftpd /etc/vsftpd.conf'},
    {'UID': 'root', 'PID': 3826, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:02',
     'CMD': '/usr/sbin/sshd -D'},
    {'UID': 'root', 'PID': 3835, 'PPID': 2, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00', 'CMD': '[cifsiod]'},
    {'UID': 'root', 'PID': 3867, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:18',
     'CMD': '/usr/sbin/cron -n'},
    {'UID': 'root', 'PID': 3870, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': 'tty1', 'TIME': '00:00:00',
     'CMD': '/sbin/agetty --noclear tty1 linux'},
    {'UID': 'avahi-a+', 'PID': 4592, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:17:15',
     'CMD': 'avahi-autoipd: [ens3] sleeping'},
    {'UID': 'root', 'PID': 4593, 'PPID': 4592, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': 'avahi-autoipd: [ens3] callout dispatcher'},
    {'UID': 'root', 'PID': 4648, 'PPID': 1, 'C': 0, 'STIME': 2017, 'TTY': '?', 'TIME': '00:00:00',
     'CMD': '/sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-'},
    {'UID': 'root', 'PID': 5823, 'PPID': 2, 'C': 0, 'STIME': 'Mar09', 'TTY': '?', 'TIME': '00:00:03',
     'CMD': '[kworker/u8:2]'},
]

COMMAND_OUTPUT_aux = '''ps -aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 139360  7220 ?        Ss   Mar01   1:16 /sbin/init
client@server>'''

COMMAND_KWARGS_aux = {"options": "-aux"}

COMMAND_RESULT_aux = [
    {'USER': 'root', 'PID': 1, '%CPU': float("0.0"), "%MEM": float("0.1"), 'VSZ': 139360, 'RSS': 7220, 'TTY': '?',
     'STAT': 'Ss', 'START': 'Mar01', 'TIME': '1:16', 'COMMAND': '/sbin/init'}
]
