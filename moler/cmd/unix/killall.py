# -*- coding: utf-8 -*-
"""
Killall command module.
"""

__author__ = "Yeshu Yang"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "yeshu.yang@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Killall(GenericUnixCommand):
    def __init__(
        self,
        connection,
        name,
        is_verbose=False,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        super(Killall, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.is_verbose = is_verbose
        self.name = name
        self.ret_required = False

    def build_command_string(self):
        if self.is_verbose:
            cmd = f"killall -v {self.name}"
        else:
            cmd = f"killall {self.name}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_no_permit(line)
                self._parse_killall_verbose(line)
            except ParsingDone:
                pass
        return super(Killall, self).on_new_line(line, is_full_line)

    def _parse_no_permit(self, line):
        if self._regex_helper.search(r"(Operation not permitted)", line):
            self.set_exception(
                CommandFailure(self, f"ERROR: {self._regex_helper.group(1)}")
            )
            raise ParsingDone

    _re_killall = re.compile(r"Killed (?P<Name>[^\(]+)\((?P<Pid>\d+)\) with signal")

    def _parse_killall_verbose(self, line):
        if self.is_verbose:
            if self._regex_helper.search_compiled(Killall._re_killall, line):
                if "Detail" not in self.current_ret:
                    self.current_ret["Detail"] = {}
                pid = self._regex_helper.group("Pid")
                self.current_ret["Detail"][pid] = self._regex_helper.group("Name")
                raise ParsingDone


COMMAND_OUTPUT_no_verbose = """
Pclinux90:~ #  killall iperf
Pclinux90:~ # """

COMMAND_KWARGS_no_verbose = {"name": "iperf"}

COMMAND_RESULT_no_verbose = {}

COMMAND_OUTPUT_no_process = """
PClinux110:/home/runner # killall tshark
tshark: no process found
PClinux110:/home/runner #"""

COMMAND_KWARGS_no_process = {"name": "tshark"}

COMMAND_RESULT_no_process = {}

COMMAND_OUTPUT_verbose = """
Pclinux90:~ #  killall -v iperf
Killed iperf(15054) with signal 15
Pclinux90:~ # """

COMMAND_KWARGS_verbose = {"name": "iperf", "is_verbose": True}

COMMAND_RESULT_verbose = {"Detail": {"15054": "iperf"}}
