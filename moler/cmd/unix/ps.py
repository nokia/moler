# -*- coding: utf-8 -*-

__author__ = 'Dariusz Rosinski, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'dariusz.rosinski@nokia.com, marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.parser.table_text import TableText


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
        self._cmd_line_found = False
        self._column_line_found = False
        self._columns = list()
        self._space_columns = list()
        self._parser = None

    def on_new_line(self, line, is_full_line):
        """
        Parses output from command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            # splitting columns according to column number
            splitted_columns = self._split_columns_in_line(line)
            # when columns names are set proceed with putting data to dictionary list
            if self._columns and splitted_columns is not None:
                # put correct value to specific column
                parsed_line = self._parser.parse(line)
                if parsed_line is not None:
                    self.current_ret.append(parsed_line)
            # assign splitted columns to parameter in Ps class; columns are printed as first line after ps command execution
            if not self._column_line_found:
                self._columns = splitted_columns
                self._column_line_found = True
                self._parser = TableText(self._columns, self._columns)
                self._parser.parse(line)
        # execute generic on_new_line
        return super(Ps, self).on_new_line(line, is_full_line)

    def _split_columns_in_line(self, line):
        """
        Split line according to columns number.

        :param line: line from device to process
        :return: list of columns or None
        """
        parsed_line = str.strip(str(line))
        # split with whitespaces
        parsed_line = re.split(r'\s+', parsed_line)
        # If no enough columns leave this line
        if len(self._columns) > len(parsed_line) or parsed_line == ['']:
            parsed_line = None
        # When data is avaliable proceed with parsing
        return parsed_line

    def build_command_string(self):
        cmd = "ps"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd


COMMAND_OUTPUT = '''
root@DMICTRL:~# ps -o user,pid,vsz,osz,pmem,rss,cmd -e
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
 root@DMICTRL:~#
 '''

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

COMMAND_OUTPUT_V2 = '''FZM-FDD-086-ws-kvm:/home/rtg # ps -ef
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
FZM-FDD-086-ws-kvm:/home/rtg #
'''

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

COMMAND_OUTPUT_V3 = '''FZM-FDD-086-ws-kvm:/home/rtg # ps -ef
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
FZM-FDD-086-ws-kvm:/home/rtg #
'''

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
