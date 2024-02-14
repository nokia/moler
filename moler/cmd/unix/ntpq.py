# -*- coding: utf-8 -*-
"""
Ntpq command module.
"""

__author__ = "Sylwester Golonka"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "sylwester.golonka@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Ntpq(GenericUnixCommand):
    def __init__(
        self, connection, options=None, prompt=None, newline_chars=None, runner=None
    ):
        super(Ntpq, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.headers = []
        self.row_nr = 0

    def build_command_string(self):
        cmd = "ntpq"
        if self.options:
            cmd = f"{cmd} {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_tab_details(line)
            except ParsingDone:
                pass
        return super(Ntpq, self).on_new_line(line, is_full_line)

    _re_parse_tab_details = re.compile(r"(?P<VALUE>\S+)")

    def _parse_tab_details(self, line):
        if self._regex_helper.search(Ntpq._re_parse_tab_details, line):
            parse_all = re.findall(Ntpq._re_parse_tab_details, line)
            if len(parse_all) > 4:
                if not self.headers:
                    for parse in parse_all:
                        self.headers.append(parse)
                else:
                    self.current_ret[parse_all[0]] = {}
                    for header, parse in zip(self.headers, parse_all):
                        self.current_ret[parse_all[0]][header] = parse
            raise ParsingDone


COMMAND_OUTPUT_parms_pn = """
host:~ # ntpq -pn
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 64.113.44.54    .INIT.          16 u    -   64    0    0.000    0.000   0.000
 62.241.198.253  .INIT.          16 u    -   64    0    0.000    0.000   0.000
 62.236.120.71   .INIT.          16 u    -   64    0    0.000    0.000   0.000
 83.145.237.222  .INIT.          16 u    -   64    0    0.000    0.000   0.000

host:~ #"""

COMMAND_RESULT_parms_pn = {
    "62.236.120.71": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "62.236.120.71",
        "st": "16",
        "t": "u",
        "when": "-",
    },
    "62.241.198.253": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "62.241.198.253",
        "st": "16",
        "t": "u",
        "when": "-",
    },
    "64.113.44.54": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "64.113.44.54",
        "st": "16",
        "t": "u",
        "when": "-",
    },
    "83.145.237.222": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "83.145.237.222",
        "st": "16",
        "t": "u",
        "when": "-",
    },
}

COMMAND_KWARGS_parms_pn = {"options": "-pn"}

COMMAND_OUTPUT_parms_p = """
ute@debdev:~$ ntpq -p
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 rolex.netservic .INIT.          16 u    -   64    0    0.000    0.000   0.000
 ntp3.dnainterne .INIT.          16 u    -   64    0    0.000    0.000   0.000
 ns2.posiona.net .INIT.          16 u    -   64    0    0.000    0.000   0.000
 heh.fi          .INIT.          16 u    -   64    0    0.000    0.000   0.000

host:~ #"""

COMMAND_RESULT_parms_p = {
    "heh.fi": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "heh.fi",
        "st": "16",
        "t": "u",
        "when": "-",
    },
    "ns2.posiona.net": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "ns2.posiona.net",
        "st": "16",
        "t": "u",
        "when": "-",
    },
    "ntp3.dnainterne": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "ntp3.dnainterne",
        "st": "16",
        "t": "u",
        "when": "-",
    },
    "rolex.netservic": {
        "delay": "0.000",
        "jitter": "0.000",
        "offset": "0.000",
        "poll": "64",
        "reach": "0",
        "refid": ".INIT.",
        "remote": "rolex.netservic",
        "st": "16",
        "t": "u",
        "when": "-",
    },
}

COMMAND_KWARGS_parms_p = {"options": "-p"}
