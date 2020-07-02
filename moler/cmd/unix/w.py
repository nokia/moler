# -*- coding: utf-8 -*-
__author__ = 'Mateusz Szczurek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'mateusz.m.szczurek@nokia.com'

import re
import datetime

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class W(GenericUnixCommand):
    """W command class."""

    def __init__(self, connection, options="", prompt=None, newline_chars=None, runner=None):
        """
        W command.

        :param connection: Moler connection to device, terminal when command is executed.
        :param options: Options of w command.
        :param prompt: Expected prompt that has been sent by device after command execution.
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(W, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.ret_required = False
        self._is_overwritten = False
        self.current_ret['GENERAL_INFO'] = dict()
        self.current_ret['RESULT'] = list()
        self.headers = list()

    # -hs -h -sh
    _re_h = re.compile(r"(?P<BEGINNING>-h)\S|(?P<SOLO>-h)|(?P<MIDDLE>h)")

    def build_command_string(self):
        """
        Build command string from parameters passed to object. Usage of paramter -h in options is going to be ignored.

        :return: String representation of the command to send over a connection to the device.
        """
        if self._regex_helper.search_compiled(W._re_h, self.options):
            if self._regex_helper.group("SOLO"):
                self.options = self.options.replace('-h', '')
            else:
                self.options = self.options.replace('h', '')

            cmd = "{} {}".format("w", self.options)
        else:
            cmd = "{}".format("w")
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            if is_full_line:
                self._parse_v_option(line)
                self._parse_general_info(line)
                self._parse_header(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        return super(W, self).on_new_line(line, is_full_line)

    # 09:07:41 up 148 days, 21:57, 11 users,  load average: 1.92, 1.82, 1.81
    _re_general_info = re.compile(r"(?P<TIME>\d{2}:\d{2}:\d{2})\s*up\s*(?P<UPTIME>.*),\s*(?P<USER_NUMBER>\d*)\s*users,"
                                  r"\s*load\s*average:\s(?P<L_AVERAGE>\S*,\s*\S*,\s*\S*)")

    def _parse_general_info(self, line):
        """
        Parse general information in line and update it to GENERAL_INFO dictionary.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._regex_helper.search_compiled(W._re_general_info, line):
            self.current_ret['GENERAL_INFO'].update({
                'time': datetime.datetime.strptime(self._regex_helper.group("TIME"), '%H:%M:%S').time(),
                'uptime': self._regex_helper.group("UPTIME"),
                'user_number': self._regex_helper.group("USER_NUMBER"),
                'load_average': self._regex_helper.group("L_AVERAGE")
            })
            raise ParsingDone

    # w from procps-ng 3.3.9
    _re_v_option = re.compile(r"(?P<V_OPTION>w from.*)")

    def _parse_v_option(self, line):
        """
        Parse -V option output in line and append it to RESULT list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._regex_helper.search_compiled(W._re_v_option, line):
            self.current_ret['RESULT'].append(self._regex_helper.group("V_OPTION"))
            raise ParsingDone

    # USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
    # ute      pts/1    :0               07:14    0.00s  0.05s  0.00s w
    _re_header = re.compile(r'(?P<HEADERS>\S+(\s\S+)*?)')

    def _parse_header(self, line):
        """
        Parse headers and entries in line, create dictionary and append it to RESULT list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._regex_helper.search_compiled(W._re_header, line):
            if not self.headers:
                for value in re.findall(W._re_header, line):
                    self.headers.append(value[0])
                raise ParsingDone
            else:
                # Dictionary which is going to be appended to the returned list
                ret = dict()
                # List of entries
                _entries = list()
                # List of values in WHAT entry
                _what_entry = list()
                for value in re.findall(W._re_header, line):
                    _entries.append(value[0])
                for what_index in range(len(self.headers) - 1, len(_entries)):
                    _what_entry.append(_entries[what_index])
                _what_entry_string = ' '.join(_what_entry)
                for index in range(len(self.headers)):
                    if index < len(self.headers) - 1:
                        ret.update({self.headers[index]: _entries[index]})
                    else:
                        ret.update({self.headers[index]: _what_entry_string})
                self.current_ret['RESULT'].append(ret)
                raise ParsingDone


COMMAND_OUTPUT_parse_general_case = """
host:~ #  w
 14:40:19 up  7:12,  5 users,  load average: 0.50, 0.33, 0.14
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
ute      :0       :0               07:28   ?xdm?  29:23   0.04s gdm-session-worker [pam/gdm-password]
ute      pts/0    :0               07:28    4:35m  0.08s  0.08s bash
host:~ # """

COMMAND_RESULT_parse_general_case = {
    'GENERAL_INFO': {'load_average': '0.50, 0.33, 0.14',
                     'time': datetime.time(14, 40, 19),
                     'uptime': '7:12',
                     'user_number': '5'},
    'RESULT': [{'FROM': ':0',
                'IDLE': '?xdm?',
                'JCPU': '29:23',
                'LOGIN@': '07:28',
                'PCPU': '0.04s',
                'TTY': ':0',
                'USER': 'ute',
                'WHAT': 'gdm-session-worker [pam/gdm-password]'},
               {'FROM': ':0',
                'IDLE': '4:35m',
                'JCPU': '0.08s',
                'LOGIN@': '07:28',
                'PCPU': '0.08s',
                'TTY': 'pts/0',
                'USER': 'ute',
                'WHAT': 'bash'}]

}

COMMAND_KWARGS_parse_general_case = {
}

COMMAND_OUTPUT_s_option = """
host:~ #  w -s
 10:22:30 up  3:09,  3 users,  load average: 0.22, 0.33, 0.32
USER     TTY      FROM              IDLE WHAT
ute      :0       :0               ?xdm?  gdm-session-worker [pam/gdm-password]
ute      pts/0    :0                6:19  bash
host:~ # """

COMMAND_RESULT_s_option = {
    'GENERAL_INFO': {'load_average': '0.22, 0.33, 0.32',
                     'time': datetime.time(10, 22, 30),
                     'uptime': '3:09',
                     'user_number': '3'},
    'RESULT': [{'FROM': ':0',
                'IDLE': '?xdm?',
                'TTY': ':0',
                'USER': 'ute',
                'WHAT': 'gdm-session-worker [pam/gdm-password]'},
               {'FROM': ':0',
                'IDLE': '6:19',
                'TTY': 'pts/0',
                'USER': 'ute',
                'WHAT': 'bash'}]
}

COMMAND_KWARGS_s_option = {
    "options": "-s"
}

COMMAND_OUTPUT_V_option = """
host:~ #  w -V
w from procps-ng 3.3.9
host:~ # """

COMMAND_RESULT_V_option = {
    'GENERAL_INFO': {},
    'RESULT': ['w from procps-ng 3.3.9']
}

COMMAND_KWARGS_V_option = {
    "options": "-V"
}

COMMAND_OUTPUT_h_option_solo = """
host:~ #  w -h
 14:40:19 up  7:12,  5 users,  load average: 0.50, 0.33, 0.14
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
ute      :0       :0               07:28   ?xdm?  29:23   0.04s gdm-session-worker [pam/gdm-password]
host:~ # """

COMMAND_RESULT_h_option_solo = {
    'GENERAL_INFO': {'load_average': '0.50, 0.33, 0.14',
                     'time': datetime.time(14, 40, 19),
                     'uptime': '7:12',
                     'user_number': '5'},
    'RESULT': [{'FROM': ':0',
                'IDLE': '?xdm?',
                'JCPU': '29:23',
                'LOGIN@': '07:28',
                'PCPU': '0.04s',
                'TTY': ':0',
                'USER': 'ute',
                'WHAT': 'gdm-session-worker [pam/gdm-password]'}]
}

COMMAND_KWARGS_h_option_solo = {
    "options": "-h"
}

COMMAND_OUTPUT_h_option_middle = """
host:~ #  w -sh
 14:40:19 up  7:12,  5 users,  load average: 0.50, 0.33, 0.14
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
ute      :0       :0               07:28   ?xdm?  29:23   0.04s gdm-session-worker [pam/gdm-password]
host:~ # """

COMMAND_RESULT_h_option_middle = {
    'GENERAL_INFO': {'load_average': '0.50, 0.33, 0.14',
                     'time': datetime.time(14, 40, 19),
                     'uptime': '7:12',
                     'user_number': '5'},
    'RESULT': [{'FROM': ':0',
                'IDLE': '?xdm?',
                'JCPU': '29:23',
                'LOGIN@': '07:28',
                'PCPU': '0.04s',
                'TTY': ':0',
                'USER': 'ute',
                'WHAT': 'gdm-session-worker [pam/gdm-password]'}]
}

COMMAND_KWARGS_h_option_middle = {
    "options": "-sh"
}
