# -*- coding: utf-8 -*-
"""
Ntpq command module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Ntpq(GenericUnixCommand):
    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None):
        super(Ntpq, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self.headers = []
        self.row_nr = 0

    def build_command_string(self):
        cmd = "ntpq"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_tab_details(line)
            except ParsingDone:
                pass
        return super(Ntpq, self).on_new_line(line, is_full_line)

    _re_parse_tab_details = re.compile(r'(?P<VALUE>\S+)')

    def _parse_tab_details(self, line):
        if self._regex_helper.search(Ntpq._re_parse_tab_details, line):
            parse_all = re.findall(Ntpq._re_parse_tab_details, line)
            if (len(parse_all) > 4):
                if not self.headers:
                    for parse in parse_all:
                        self.headers.append(parse)
                else:
                    self.current_ret[parse_all[0]] = dict()
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
    u'62.236.120.71': {u'delay': u'0.000',
                       u'jitter': u'0.000',
                       u'offset': u'0.000',
                       u'poll': u'64',
                       u'reach': u'0',
                       u'refid': u'.INIT.',
                       u'remote': u'62.236.120.71',
                       u'st': u'16',
                       u't': u'u',
                       u'when': u'-'},
    u'62.241.198.253': {u'delay': u'0.000',
                        u'jitter': u'0.000',
                        u'offset': u'0.000',
                        u'poll': u'64',
                        u'reach': u'0',
                        u'refid': u'.INIT.',
                        u'remote': u'62.241.198.253',
                        u'st': u'16',
                        u't': u'u',
                        u'when': u'-'},
    u'64.113.44.54': {u'delay': u'0.000',
                      u'jitter': u'0.000',
                      u'offset': u'0.000',
                      u'poll': u'64',
                      u'reach': u'0',
                      u'refid': u'.INIT.',
                      u'remote': u'64.113.44.54',
                      u'st': u'16',
                      u't': u'u',
                      u'when': u'-'},
    u'83.145.237.222': {u'delay': u'0.000',
                        u'jitter': u'0.000',
                        u'offset': u'0.000',
                        u'poll': u'64',
                        u'reach': u'0',
                        u'refid': u'.INIT.',
                        u'remote': u'83.145.237.222',
                        u'st': u'16',
                        u't': u'u',
                        u'when': u'-'}
}

COMMAND_KWARGS_parms_pn = {
    "options": "-pn"
}

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
    u'heh.fi': {u'delay': u'0.000',
                u'jitter': u'0.000',
                u'offset': u'0.000',
                u'poll': u'64',
                u'reach': u'0',
                u'refid': u'.INIT.',
                u'remote': u'heh.fi',
                u'st': u'16',
                u't': u'u',
                u'when': u'-'},
    u'ns2.posiona.net': {u'delay': u'0.000',
                         u'jitter': u'0.000',
                         u'offset': u'0.000',
                         u'poll': u'64',
                         u'reach': u'0',
                         u'refid': u'.INIT.',
                         u'remote': u'ns2.posiona.net',
                         u'st': u'16',
                         u't': u'u',
                         u'when': u'-'},
    u'ntp3.dnainterne': {u'delay': u'0.000',
                         u'jitter': u'0.000',
                         u'offset': u'0.000',
                         u'poll': u'64',
                         u'reach': u'0',
                         u'refid': u'.INIT.',
                         u'remote': u'ntp3.dnainterne',
                         u'st': u'16',
                         u't': u'u',
                         u'when': u'-'},
    u'rolex.netservic': {u'delay': u'0.000',
                         u'jitter': u'0.000',
                         u'offset': u'0.000',
                         u'poll': u'64',
                         u'reach': u'0',
                         u'refid': u'.INIT.',
                         u'remote': u'rolex.netservic',
                         u'st': u'16',
                         u't': u'u',
                         u'when': u'-'}
}

COMMAND_KWARGS_parms_p = {
    "options": "-p"
}
