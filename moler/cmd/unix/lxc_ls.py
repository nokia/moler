# -*- coding: utf-8 -*-
"""
LxcLs command module.
"""

__author__ = "Agnieszka Bylica, Marcin Usielski"
__copyright__ = "Copyright (C) 2019-2020, Nokia"
__email__ = "agnieszka.bylica@nokia.com, marcin.usielski@nokia.com"


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class LxcLs(GenericUnixCommand):
    """Lxcls command class."""

    def __init__(
        self, connection, prompt=None, newline_chars=None, runner=None, options=None
    ):
        """
        Lxcls command lists containers.

        :param connection: moler connection to device, terminal when command is executed.
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        :param options: command options as string
        """
        super(LxcLs, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )

        self.options = options
        self.current_ret["RESULT"] = []
        self._headers = []

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "lxc-ls"
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
                self._command_error(line)
                self._parse_table_headers(line)
                self._parse_table_row(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(LxcLs, self).on_new_line(line, is_full_line)

    _re_command_error = re.compile(r"(?P<ERROR>lxc-ls:\s+.+)", re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(LxcLs._re_command_error, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('ERROR')}"
                )
            )

    _re_headers = re.compile(r"NAME\s+STATE\s+AUTOSTART\s+GROUPS\s+IPV4\s+IPV6", re.I)

    def _parse_table_headers(self, line):
        if self._regex_helper.search_compiled(LxcLs._re_headers, line):
            self._headers = ["Name", "State", "Autostart", "Groups", "IPv4", "IPv6"]
            raise ParsingDone

    def _parse_table_row(self, line):
        if self._headers:
            values = re.split(r"([^,])\s+", line)
            striped_values = []
            values_size = len(values)
            i = 0
            while i < values_size - 1:
                striped_values.append(values[i] + values[i + 1])
                i += 2
            if values_size % 2 != 0:
                striped_values.append(values[-1])

            self.current_ret["RESULT"].append(dict(zip(self._headers, striped_values)))
            raise ParsingDone

    def _parse_line(self, line):
        self.current_ret["RESULT"].append(line.split())
        raise ParsingDone


COMMAND_OUTPUT = """root@server~ >lxc-ls
0xe000 0xe001 0xe002 0xe003 0xe004 0xe009 0xe00a 0xe00b 0xe00c 0xe00d 0xe019
root@server~ >"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {
    "RESULT": [
        [
            "0xe000",
            "0xe001",
            "0xe002",
            "0xe003",
            "0xe004",
            "0xe009",
            "0xe00a",
            "0xe00b",
            "0xe00c",
            "0xe00d",
            "0xe019",
        ]
    ]
}


COMMAND_OUTPUT_2 = """
root@server~ >lxc-ls -f
NAME   STATE   AUTOSTART GROUPS IPV4                                                                                                                                                                                                                                                                                                                                       IPV6
0xe000 RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe001 RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe002 RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe003 RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe004 RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe009 RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe00a RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe00b RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe00c RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe00d RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
0xe019 RUNNING 0         -      10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253 -
root@server~ >"""

COMMAND_KWARGS_2 = {"options": "-f"}

COMMAND_RESULT_2 = {
    "RESULT": [
        {
            "Name": "0xe000",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe001",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe002",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe003",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe004",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe009",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe00a",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe00b",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe00c",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe00d",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
        {
            "Name": "0xe019",
            "State": "RUNNING",
            "Autostart": "0",
            "Groups": "-",
            "IPv4": "10.1.1.1, 10.1.1.2, 10.83.182.49, 192.168.2.60, 192.168.253.1, 192.168.253.16, 192.168.253.193, 192.168.253.217, 192.168.253.224, 192.168.253.225, 192.168.253.226, 192.168.253.227, 192.168.253.228, 192.168.253.233, 192.168.253.234, 192.168.253.235, 192.168.253.236, 192.168.253.237, 192.168.255.1, 192.168.255.129, 192.168.255.253",
            "IPv6": "-",
        },
    ]
}

COMMAND_OUTPUT_3 = """
root@server~ >lxc-ls --nesting=3
0xe000         0xe000/0xe000  0xe000/0xe001  0xe000/0xe002  0xe000/0xe003  0xe000/0xe004  0xe000/0xe009  0xe000/0xe00a  0xe000/0xe00b  0xe000/0xe00c  0xe000/0xe00d
0xe000/0xe019  0xe001         0xe002         0xe002/0xe000  0xe002/0xe001  0xe002/0xe002  0xe002/0xe003  0xe002/0xe004  0xe002/0xe009  0xe002/0xe00a  0xe002/0xe00b
0xe002/0xe00c  0xe002/0xe00d  0xe002/0xe019  0xe003         0xe003/0xe000  0xe003/0xe001  0xe003/0xe002  0xe003/0xe003  0xe003/0xe004  0xe003/0xe009  0xe003/0xe00a
0xe003/0xe00b  0xe003/0xe00c  0xe003/0xe00d  0xe003/0xe019  0xe004         0xe004/0xe000  0xe004/0xe001  0xe004/0xe002  0xe004/0xe003  0xe004/0xe004  0xe004/0xe009
0xe004/0xe00a  0xe004/0xe00b  0xe004/0xe00c  0xe004/0xe00d  0xe004/0xe019  0xe009         0xe00a         0xe00a/0xe000  0xe00a/0xe001  0xe00a/0xe002  0xe00a/0xe003
0xe00a/0xe004  0xe00a/0xe009  0xe00a/0xe00a  0xe00a/0xe00b  0xe00a/0xe00c  0xe00a/0xe00d  0xe00a/0xe019  0xe00b         0xe00c         0xe00d         0xe019
0xe019/0xe000  0xe019/0xe001  0xe019/0xe002  0xe019/0xe003  0xe019/0xe004  0xe019/0xe009  0xe019/0xe00a  0xe019/0xe00b  0xe019/0xe00c  0xe019/0xe00d  0xe019/0xe019
root@server~ >"""

COMMAND_KWARGS_3 = {"options": "--nesting=3"}

COMMAND_RESULT_3 = {
    "RESULT": [
        [
            "0xe000",
            "0xe000/0xe000",
            "0xe000/0xe001",
            "0xe000/0xe002",
            "0xe000/0xe003",
            "0xe000/0xe004",
            "0xe000/0xe009",
            "0xe000/0xe00a",
            "0xe000/0xe00b",
            "0xe000/0xe00c",
            "0xe000/0xe00d",
        ],
        [
            "0xe000/0xe019",
            "0xe001",
            "0xe002",
            "0xe002/0xe000",
            "0xe002/0xe001",
            "0xe002/0xe002",
            "0xe002/0xe003",
            "0xe002/0xe004",
            "0xe002/0xe009",
            "0xe002/0xe00a",
            "0xe002/0xe00b",
        ],
        [
            "0xe002/0xe00c",
            "0xe002/0xe00d",
            "0xe002/0xe019",
            "0xe003",
            "0xe003/0xe000",
            "0xe003/0xe001",
            "0xe003/0xe002",
            "0xe003/0xe003",
            "0xe003/0xe004",
            "0xe003/0xe009",
            "0xe003/0xe00a",
        ],
        [
            "0xe003/0xe00b",
            "0xe003/0xe00c",
            "0xe003/0xe00d",
            "0xe003/0xe019",
            "0xe004",
            "0xe004/0xe000",
            "0xe004/0xe001",
            "0xe004/0xe002",
            "0xe004/0xe003",
            "0xe004/0xe004",
            "0xe004/0xe009",
        ],
        [
            "0xe004/0xe00a",
            "0xe004/0xe00b",
            "0xe004/0xe00c",
            "0xe004/0xe00d",
            "0xe004/0xe019",
            "0xe009",
            "0xe00a",
            "0xe00a/0xe000",
            "0xe00a/0xe001",
            "0xe00a/0xe002",
            "0xe00a/0xe003",
        ],
        [
            "0xe00a/0xe004",
            "0xe00a/0xe009",
            "0xe00a/0xe00a",
            "0xe00a/0xe00b",
            "0xe00a/0xe00c",
            "0xe00a/0xe00d",
            "0xe00a/0xe019",
            "0xe00b",
            "0xe00c",
            "0xe00d",
            "0xe019",
        ],
        [
            "0xe019/0xe000",
            "0xe019/0xe001",
            "0xe019/0xe002",
            "0xe019/0xe003",
            "0xe019/0xe004",
            "0xe019/0xe009",
            "0xe019/0xe00a",
            "0xe019/0xe00b",
            "0xe019/0xe00c",
            "0xe019/0xe00d",
            "0xe019/0xe019",
        ],
    ]
}


# ==================================================HELP=MESSAGE==========================================================
# root@0xe000:~ >lxc-ls --help
# Usage: lxc-ls
# [-P lxcpath] [--active] [--running] [--frozen] [--stopped] [--nesting] [-g groups] [--filter regex]
# [-1] [-P lxcpath] [--active] [--running] [--frozen] [--stopped] [--nesting] [-g groups] [--filter regex]
# [-f] [-P lxcpath] [--active] [--running] [--frozen] [--stopped] [--nesting] [-g groups] [--filter regex]

# lxc-ls list containers

# Options :
#   -1, --line         show one entry per line
#   -f, --fancy        use a fancy, column-based output
#   -F, --fancy-format comma separated list of columns to show in the fancy output
#                      valid columns are: NAME, STATE, PID, RAM, SWAP, AUTOSTART,
#                      GROUPS, INTERFACE, IPV4 and IPV6
#   --active           list only active containers
#   --running          list only running containers
#   --frozen           list only frozen containers
#   --stopped          list only stopped containers
#   --defined          list only defined containers
#   --nesting=NUM      list nested containers up to NUM (default is 5) levels of nesting
#   --filter=REGEX     filter container names by regular expression
#   -g --groups        comma separated list of groups a container must have to be displayed

# Common options :
#   -o, --logfile=FILE               Output log to FILE instead of stderr
#   -l, --logpriority=LEVEL          Set log priority to LEVEL
#   -q, --quiet                      Don't produce any output
#   -P, --lxcpath=PATH               Use specified container path
#   -?, --help                       Give this help list
#       --usage                      Give a short usage message
#       --version                    Print the version number

# Mandatory or optional arguments to long options are also mandatory or optional
# for any corresponding short options.

# See the lxc-ls man page for further information.

# root@0xe000:~ >
