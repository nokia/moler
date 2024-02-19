# -*- coding: utf-8 -*-
"""
Service command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Service(GenericUnixCommand):

    def __init__(self, connection, options, prompt=None, newline_chars=None, runner=None):
        super(Service, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                      runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.ret_required = False

        self.arr = False

    def build_command_string(self):
        cmd = f"service {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_service_description(line)
                self._parse_status_service(line)
                self._parse_log(line)
                self._parse_key_value(line)
            except ParsingDone:
                pass
        return super(Service, self).on_new_line(line, is_full_line)

    #  [ + ]  acpid
    _re_status_service = re.compile(r"\s+(?P<STATUS>\[.*\])\s+(?P<SERVICE>\S+)")

    def _parse_status_service(self, line):
        if self._regex_helper.search_compiled(Service._re_status_service, line):
            self.current_ret[self._regex_helper.group('SERVICE')] = self._regex_helper.group('STATUS')
            raise ParsingDone

    # ● ssh.service - OpenBSD Secure Shell server
    _re_service_description = re.compile(r"[^A-Za-z0-9\s]\s+(?P<SERVICE>\S+)\s+-\s+(?P<DESCRIPTION>\S.*\S)")

    def _parse_service_description(self, line):
        if self._regex_helper.search_compiled(Service._re_service_description, line):
            self.current_ret['Service'] = self._regex_helper.group('SERVICE')
            self.current_ret['Description'] = self._regex_helper.group('DESCRIPTION')
            raise ParsingDone

    # Loaded: loaded (/lib/systemd/system/ssh.service; enabled)
    _re_key_value = re.compile(r"\s+(?P<KEY>\S.*\S+):\s+(?P<VALUE>.*)")

    def _parse_key_value(self, line):
        if self._regex_helper.search_compiled(Service._re_key_value, line):
            if self.arr and self._regex_helper.group('KEY') in self.current_ret.keys():
                self.current_ret[self._regex_helper.group('KEY')].append(self._regex_helper.group('VALUE'))
            elif self._regex_helper.group('KEY') in self.current_ret.keys():
                temp_value = self.current_ret[self._regex_helper.group('KEY')]
                self.current_ret[self._regex_helper.group('KEY')] = []
                self.current_ret[self._regex_helper.group('KEY')].append(temp_value)
                self.current_ret[self._regex_helper.group('KEY')].append(self._regex_helper.group('VALUE'))
                self.arr = True
            else:
                self.current_ret[self._regex_helper.group('KEY')] = self._regex_helper.group('VALUE')
            raise ParsingDone

    # Jul 19 15:15:42 debdev systemd[1]: Started OpenBSD Secure Shell server.
    _re_log = re.compile(r"\S+\s+\d+\s+\d+:\d+:\d+\s+(.*)")

    def _parse_log(self, line):
        if self._regex_helper.search_compiled(Service._re_log, line):
            if "Log" not in self.current_ret.keys():
                self.current_ret['Log'] = []
            self.current_ret['Log'].append(line)
            raise ParsingDone


COMMAND_OUTPUT_status_all = """service --status-all
 [ + ]  acpid
 [ - ]  alsa-utils
 [ - ]  anacron
 [ + ]  atd
 [ + ]  avahi-daemon
 [ - ]  bluetooth
 [ - ]  bootlogs
 [ - ]  bootmisc.sh
 [ - ]  checkfs.sh
 [ - ]  checkroot-bootclean.sh
 [ - ]  checkroot.sh
 [ + ]  console-setup
 [ + ]  cron
 [ + ]  cups
 [ + ]  cups-browsed
 [ + ]  dbus
 [ + ]  dnsmasq
 [ + ]  exim4
 [ + ]  gdm3
 [ + ]  gdomap
 [ - ]  hostname.sh
 [ - ]  hwclock.sh
 [ - ]  isc-dhcp-server
 [ + ]  kbd
 [ + ]  keyboard-setup
 [ - ]  killprocs
 [ + ]  kmod
 [ - ]  logstash
 [ - ]  lvm2
 [ + ]  minissdpd
 [ - ]  motd
 [ - ]  mountall-bootclean.sh
 [ - ]  mountall.sh
 [ - ]  mountdevsubfs.sh
 [ - ]  mountkernfs.sh
 [ - ]  mountnfs-bootclean.sh
 [ - ]  mountnfs.sh
 [ - ]  netfilter-persistent
 [ + ]  network-manager
 [ + ]  networking
 [ + ]  nfs-common
 [ + ]  nmbd
 [ + ]  ntp
 [ - ]  open-vm-tools
 [ - ]  pppd-dns
 [ + ]  procps
 [ + ]  rc.local
 [ + ]  resolvconf
 [ - ]  rmnologin
 [ + ]  rpcbind
 [ - ]  rsync
 [ + ]  rsyslog
 [ + ]  samba
 [ + ]  samba-ad-dc
 [ - ]  saned
 [ - ]  screen-cleanup
 [ - ]  sendsigs
 [ + ]  smbd
 [ + ]  snmpd
 [ + ]  speech-dispatcher
 [ + ]  ssh
 [ - ]  sudo
 [ - ]  tftpd-hpa
 [ + ]  udev
 [ + ]  udev-finish
 [ - ]  umountfs
 [ - ]  umountnfs.sh
 [ - ]  umountroot
 [ + ]  urandom
 [ + ]  winbind
 [ - ]  x11-common
moler_bash#"""

COMMAND_KWARGS_status_all = {
    'options': '--status-all'
}
COMMAND_RESULT_status_all = {
    'acpid': '[ + ]',
    'alsa-utils': '[ - ]',
    'anacron': '[ - ]',
    'atd': '[ + ]',
    'avahi-daemon': '[ + ]',
    'bluetooth': '[ - ]',
    'bootlogs': '[ - ]',
    'bootmisc.sh': '[ - ]',
    'checkfs.sh': '[ - ]',
    'checkroot-bootclean.sh': '[ - ]',
    'checkroot.sh': '[ - ]',
    'console-setup': '[ + ]',
    'cron': '[ + ]',
    'cups': '[ + ]',
    'cups-browsed': '[ + ]',
    'dbus': '[ + ]',
    'dnsmasq': '[ + ]',
    'exim4': '[ + ]',
    'gdm3': '[ + ]',
    'gdomap': '[ + ]',
    'hostname.sh': '[ - ]',
    'hwclock.sh': '[ - ]',
    'isc-dhcp-server': '[ - ]',
    'kbd': '[ + ]',
    'keyboard-setup': '[ + ]',
    'killprocs': '[ - ]',
    'kmod': '[ + ]',
    'logstash': '[ - ]',
    'lvm2': '[ - ]',
    'minissdpd': '[ + ]',
    'motd': '[ - ]',
    'mountall-bootclean.sh': '[ - ]',
    'mountall.sh': '[ - ]',
    'mountdevsubfs.sh': '[ - ]',
    'mountkernfs.sh': '[ - ]',
    'mountnfs-bootclean.sh': '[ - ]',
    'mountnfs.sh': '[ - ]',
    'netfilter-persistent': '[ - ]',
    'network-manager': '[ + ]',
    'networking': '[ + ]',
    'nfs-common': '[ + ]',
    'nmbd': '[ + ]',
    'ntp': '[ + ]',
    'open-vm-tools': '[ - ]',
    'pppd-dns': '[ - ]',
    'procps': '[ + ]',
    'rc.local': '[ + ]',
    'resolvconf': '[ + ]',
    'rmnologin': '[ - ]',
    'rpcbind': '[ + ]',
    'rsync': '[ - ]',
    'rsyslog': '[ + ]',
    'samba': '[ + ]',
    'samba-ad-dc': '[ + ]',
    'saned': '[ - ]',
    'screen-cleanup': '[ - ]',
    'sendsigs': '[ - ]',
    'smbd': '[ + ]',
    'snmpd': '[ + ]',
    'speech-dispatcher': '[ + ]',
    'ssh': '[ + ]',
    'sudo': '[ - ]',
    'tftpd-hpa': '[ - ]',
    'udev': '[ + ]',
    'udev-finish': '[ + ]',
    'umountfs': '[ - ]',
    'umountnfs.sh': '[ - ]',
    'umountroot': '[ - ]',
    'urandom': '[ + ]',
    'winbind': '[ + ]',
    'x11-common': '[ - ]'
}

COMMAND_OUTPUT_status = """service ssh status
● ssh.service - OpenBSD Secure Shell server
   Loaded: loaded (/lib/systemd/system/ssh.service; enabled)
   Active: active (running) since Thu 2018-07-19 15:15:42 CEST; 32s ago
  Process: 1231 ExecReload=/bin/kill -HUP $MAINPID (code=exited, status=0/SUCCESS)
  Process: 1227 ExecReload=/usr/sbin/sshd -t (code=exited, status=0/SUCCESS)
  Process: 2543 ExecStartPre=/usr/sbin/sshd -t (code=exited, status=0/SUCCESS)
 Main PID: 2544 (sshd)
   CGroup: /system.slice/ssh.service
           └─2544 /usr/sbin/sshd -D

Jul 19 15:15:42 debdev systemd[1]: Started OpenBSD Secure Shell server.
Jul 19 15:15:42 debdev sshd[2544]: Server listening on 0.0.0.0 port 22.
Jul 19 15:15:43 debdev sshd[2544]: Server listening on :: port 22.
moler_bash#"""

COMMAND_KWARGS_status = {
    'options': 'ssh status',
}
COMMAND_RESULT_status = {
    'Description': 'OpenBSD Secure Shell server',
    'Service': 'ssh.service',
    'Loaded': 'loaded (/lib/systemd/system/ssh.service; enabled)',
    'Active': 'active (running) since Thu 2018-07-19 15:15:42 CEST; 32s ago',
    'Process': ['1231 ExecReload=/bin/kill -HUP $MAINPID (code=exited, status=0/SUCCESS)',
                '1227 ExecReload=/usr/sbin/sshd -t (code=exited, status=0/SUCCESS)',
                '2543 ExecStartPre=/usr/sbin/sshd -t (code=exited, status=0/SUCCESS)',
                ],
    'Main PID': '2544 (sshd)',
    'CGroup': '/system.slice/ssh.service',
    'Log': ['Jul 19 15:15:42 debdev systemd[1]: Started OpenBSD Secure Shell server.',
            'Jul 19 15:15:42 debdev sshd[2544]: Server listening on 0.0.0.0 port 22.',
            'Jul 19 15:15:43 debdev sshd[2544]: Server listening on :: port 22.'],
}

COMMAND_OUTPUT = """service ssh start
moler_bash#"""

COMMAND_KWARGS = {
    'options': 'ssh start',
}
COMMAND_RESULT = {}
