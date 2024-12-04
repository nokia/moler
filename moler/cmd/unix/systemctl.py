# -*- coding: utf-8 -*-
"""
Systemctl command module.
"""

__author__ = "Michal Ernst"
__copyright__ = "Copyright (C) 2019, Nokia"
__email__ = "michal.ernst@nokia.com"

import re

from moler.cmd.unix.service import Service
from moler.exceptions import ParsingDone


class Systemctl(Service):
    def __init__(
        self,
        connection,
        options=None,
        service=None,
        password=None,
        prompt=None,
        newline_chars=None,
        runner=None,
        encrypt_password=True,
    ):
        """
        Constructs object for Unix command systemctl.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: systemctl command options.
        :param service: service to manipulate.
        :param password: password for root if cmd run by not root user.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param encrypt_password: If True then * will be in logs when password is sent, otherwise plain text.
        """
        super(Systemctl, self).__init__(
            connection=connection,
            options=options,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        # Parameters defined by calling the command
        self.service = service
        self.password = password
        self.encrypt_password = encrypt_password

        self.ret_required = False
        self._password_sent = False
        self._header_found = False
        self._space_or_q_sent = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "systemctl"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.service:
            cmd = f"{cmd} {self.service}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        """
        try:
            self._parse_password(line)
            self._parse_authenticating_as(line, is_full_line)
            self._parse_header(line, is_full_line)
            self._parse_line(line, is_full_line)
            self._parse_send_space_or_q(line)

            return super(Systemctl, self).on_new_line(line, is_full_line)
        except ParsingDone:
            pass
        if is_full_line:
            self._space_or_q_sent = False

    # Password:
    _re_password = re.compile(r"Password:", re.I)

    def _parse_password(self, line):
        """
        Parses if waits for password.

        :param line: Line from device.
        :return: None
        :raises: ParsingDone if regex matches the line.
        """
        if re.search(Systemctl._re_password, line):
            if not self._password_sent:
                self.connection.sendline(self.password, encrypt=self.encrypt_password)
                self._password_sent = True
            raise ParsingDone()

    # Authenticating as: root
    _re_authenticating_as = re.compile(r"Authenticating as: (?P<USER>\S+)", re.I)

    def _parse_authenticating_as(self, line, is_full_line):
        """
        Parse authenticating as other user.

        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        :raises: ParsingDone if regex matches the line.
        """
        if is_full_line and self._regex_helper.search_compiled(
            Systemctl._re_authenticating_as, line
        ):
            self.current_ret["USER"] = self._regex_helper.group("USER")
            raise ParsingDone

    _columns = ["UNIT", "LOAD", "ACTIVE", "SUB", "DESCRIPTION"]

    # UNIT                                                                    LOAD   ACTIVE     SUB          DESCRIPTION
    _re_header = re.compile(r"\s+".join(map(str, _columns)), re.I)

    def _parse_header(self, line, is_full_line):
        if is_full_line and self._regex_helper.search_compiled(
            Systemctl._re_header, line
        ):
            self._header_found = True

            raise ParsingDone

    # basic.target                                                           loaded active     active       Basic System
    _re_line = re.compile(
        r"^\s+(?P<UNIT>\S+)\s+(?P<LOAD>\S+)\s+(?P<ACTIVE>\S+)\s+(?P<SUB>\S+)\s+(?P<DESCRIPTION>.+)",
        re.I,
    )

    def _parse_line(self, line, is_full_line):
        """
        Parse single line from command output.

        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None
        :raises: ParsingDone if regex matches the line.
        """

        if is_full_line and self._header_found and self._regex_helper.search_compiled(Systemctl._re_line, line):
            service = self._regex_helper.group(Systemctl._columns[0])
            self.current_ret[service] = {}

            for column in Systemctl._columns[1:]:
                self.current_ret[service][column] = self._regex_helper.group(
                    column.strip()
                )

            raise ParsingDone

    # lines 1-99
    _re_send_space_or_q = re.compile(r"^lines.+")

    def _parse_send_space_or_q(self, line):
        if not self._space_or_q_sent and self._regex_helper.search_compiled(
            Systemctl._re_send_space_or_q, line
        ):
            if "END" in line:
                self.connection.sendline("q")
            else:
                self.connection.send(" ")

            self._space_or_q_sent = True
            raise ParsingDone


COMMAND_OUTPUT_status = """user@debdev:/home/ute# systemctl status ssh.service
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
user@debdev:/home/ute# """

COMMAND_KWARGS_status = {"options": "status", "service": "ssh.service"}

COMMAND_RESULT_status = {
    "Description": "OpenBSD Secure Shell server",
    "Service": "ssh.service",
    "Loaded": "loaded (/lib/systemd/system/ssh.service; enabled)",
    "Active": "active (running) since Thu 2018-07-19 15:15:42 CEST; 32s ago",
    "Process": [
        "1231 ExecReload=/bin/kill -HUP $MAINPID (code=exited, status=0/SUCCESS)",
        "1227 ExecReload=/usr/sbin/sshd -t (code=exited, status=0/SUCCESS)",
        "2543 ExecStartPre=/usr/sbin/sshd -t (code=exited, status=0/SUCCESS)",
    ],
    "Main PID": "2544 (sshd)",
    "CGroup": "/system.slice/ssh.service",
    "Log": [
        "Jul 19 15:15:42 debdev systemd[1]: Started OpenBSD Secure Shell server.",
        "Jul 19 15:15:42 debdev sshd[2544]: Server listening on 0.0.0.0 port 22.",
        "Jul 19 15:15:43 debdev sshd[2544]: Server listening on :: port 22.",
    ],
}

COMMAND_OUTPUT_start = """user@debdev:/home/ute# systemctl start ssh.service
==== AUTHENTICATING FOR org.freedesktop.systemd1.manage-units ===
Authentication is required to start 'ssh.service'.
Authenticating as: root
Password:
==== AUTHENTICATION COMPLETE ===
user@debdev:/home/ute#"""

COMMAND_KWARGS_start = {
    "options": "start",
    "service": "ssh.service",
    "password": "password",
}

COMMAND_RESULT_start = {"USER": "root"}

COMMAND_OUTPUT = """user@debdev:/home/ute# systemctl
  UNIT                                                                                      LOAD   ACTIVE     SUB          DESCRIPTION
  basic.target                                                                              loaded active     active       Basic System
  cryptsetup.target                                                                         loaded active     active       Encrypted Volumes
  getty.target                                                                              loaded active     active       Login Prompts
  graphical.target                                                                          loaded active     active       Graphical Interface
  local-fs-pre.target                                                                       loaded active     active       Local File Systems (Pre)
  local-fs.target                                                                           loaded active     active       Local File Systems
  multi-user.target                                                                         loaded active     active       Multi-User System
  network-online.target                                                                     loaded active     active       Network is Online
  network-pre.target                                                                        loaded active     active       Network (Pre)
  network.target                                                                            loaded active     active       Network
  nss-lookup.target                                                                         loaded active     active       Host and Network Name Lookups
  nss-user-lookup.target                                                                    loaded active     active       User and Group Name Lookups
  paths.target                                                                              loaded active     active       Paths
  remote-fs.target                                                                          loaded active     active       Remote File Systems
  slices.target                                                                             loaded active     active       Slices
  sockets.target                                                                            loaded active     active       Sockets
  sound.target                                                                              loaded active     active       Sound Card
  swap.target                                                                               loaded active     active       Swap
  sysinit.target                                                                            loaded active     active       System Initialization
  time-sync.target                                                                          loaded active     active       System Time Synchronized
  timers.target                                                                             loaded active     active       Timers
  anacron.timer                                                                             loaded active     waiting      Trigger anacron every hour
  apt-daily-upgrade.timer                                                                   loaded active     waiting      Daily apt upgrade and clean activities
  apt-daily.timer                                                                           loaded active     waiting      Daily apt download activities
  systemd-tmpfiles-clean.timer                                                              loaded active     waiting      Daily Cleanup of Temporary Directories
LOAD   = Reflects whether the unit definition was properly loaded.
ACTIVE = The high-level unit activation state, i.e. generalization of SUB.
SUB    = The low-level unit activation state, values depend on unit type.

141 loaded units listed. Pass --all to see loaded but inactive units, too.
To show all installed unit files use 'systemctl list-unit-files'.
user@debdev:/home/ute# """

COMMAND_KWARGS = {}

COMMAND_RESULT = {
    "anacron.timer": {
        "ACTIVE": "active",
        "DESCRIPTION": "Trigger anacron every hour",
        "LOAD": "loaded",
        "SUB": "waiting",
    },
    "apt-daily-upgrade.timer": {
        "ACTIVE": "active",
        "DESCRIPTION": "Daily apt upgrade and clean " "activities",
        "LOAD": "loaded",
        "SUB": "waiting",
    },
    "apt-daily.timer": {
        "ACTIVE": "active",
        "DESCRIPTION": "Daily apt download activities",
        "LOAD": "loaded",
        "SUB": "waiting",
    },
    "basic.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Basic System",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "cryptsetup.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Encrypted Volumes",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "getty.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Login Prompts",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "graphical.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Graphical Interface",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "local-fs-pre.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Local File Systems (Pre)",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "local-fs.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Local File Systems",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "multi-user.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Multi-User System",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "network-online.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Network is Online",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "network-pre.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Network (Pre)",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "network.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Network",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "nss-lookup.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Host and Network Name Lookups",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "nss-user-lookup.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "User and Group Name Lookups",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "paths.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Paths",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "remote-fs.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Remote File Systems",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "slices.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Slices",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "sockets.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Sockets",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "sound.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Sound Card",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "swap.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Swap",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "sysinit.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "System Initialization",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "systemd-tmpfiles-clean.timer": {
        "ACTIVE": "active",
        "DESCRIPTION": "Daily Cleanup of " "Temporary Directories",
        "LOAD": "loaded",
        "SUB": "waiting",
    },
    "time-sync.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "System Time Synchronized",
        "LOAD": "loaded",
        "SUB": "active",
    },
    "timers.target": {
        "ACTIVE": "active",
        "DESCRIPTION": "Timers",
        "LOAD": "loaded",
        "SUB": "active",
    },
}
