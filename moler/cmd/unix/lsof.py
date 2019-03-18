# -*- coding: utf-8 -*-
"""
lsof command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
import re
import sys


class Lsof(GenericUnixCommand):

    """Unix lsof command"""

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None, options=None):
        """
        Unix lsof command

        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: Prompt of the starting shell
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param options: Options for command lsof
        """
        super(Lsof, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self._headers = list()
        self._header_pos = list()
        self.current_ret["VALUES"] = list()
        self.current_ret["NUMBER"] = 0

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "lsof"
        if self.options:
            cmd = "lsof {}".format(self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                self._parse_warning(line)
                self._parse_number(line)
                self._parse_headers(line)
                self._parse_data(line)
            except ParsingDone:
                pass
        super(Lsof, self).on_new_line(line=line, is_full_line=is_full_line)

    # Output information may be incomplete.
    _re_warnings = re.compile(r"can't stat|may be incomplete")

    def _parse_warning(self, line):
        if self._regex_helper.search_compiled(Lsof._re_warnings, line):
            raise ParsingDone()

    # 15695
    _re_number = re.compile(r"^\s*(?P<NUMBER>\d+)\s*$")

    def _parse_number(self, line):
        if self._regex_helper.match_compiled(Lsof._re_number, line):
            self.current_ret["NUMBER"] = int(self._regex_helper.group("NUMBER"))
            raise ParsingDone()

    # COMMAND     PID   TID        USER   FD      TYPE             DEVICE  SIZE/OFF       NODE NAME
    _re_output_line = re.compile(r"\S+")

    def _parse_headers(self, line):
        if not self._headers:
            last_pos = 0
            self._headers = re.findall(Lsof._re_output_line, line)
            for header in self._headers:
                position = line.find(header, last_pos)
                last_pos = position + len(header)
                self._header_pos.append(position)
            raise ParsingDone()

    def _parse_data(self, line):
        if self._headers:
            item = dict()
            for header in self._headers:
                item[header] = None
            splitted_values = re.findall(Lsof._re_output_line, line)
            last_value_position = 0
            if len(splitted_values) > 1:
                data_index = 0
                for header_index, header in enumerate(self._headers, 0):
                    value = splitted_values[data_index]
                    value_position = line.find(value, last_value_position)
                    if self._proper_position_value(header_index=header_index, value_position=value_position):
                        item[header] = value
                        data_index += 1
                        last_value_position = value_position
                self.current_ret["VALUES"].append(item)
                self.current_ret["NUMBER"] += 1
                raise ParsingDone()

    def _proper_position_value(self, header_index, value_position):
        ret = False
        if header_index < len(self._headers):
            current_header_pos = self._header_pos[header_index]
            if current_header_pos == value_position:
                ret = True
            else:
                prev_header_pos = -1
                if header_index > 0:
                    prev_header_pos = self._header_pos[header_index - 1]
                next_header_pos = sys.maxsize  # larger value than any column
                if header_index < len(self._headers) - 1:
                    next_header_pos = self._header_pos[header_index] + len(self._headers[header_index])
                if value_position > prev_header_pos and value_position < next_header_pos:
                    ret = True
        return ret


COMMAND_OUTPUT_number_only = """lsof | wc -l
lsof: WARNING: can't stat() vboxsf file system /media/sf_SharedFolder
      Output information may be incomplete.
lsof: WARNING: can't stat() fuse.gvfsd-fuse file system /run/user/121/gvfs
      Output information may be incomplete.
15695
bash-4.2:~ #"""

COMMAND_KWARGS_number_only = {
    "options": "| wc -l"
}

COMMAND_RESULT_number_only = {
    "NUMBER": 15695,
    "VALUES": []
}

COMMAND_OUTPUT_no_parameters = """lsof
COMMAND     PID   TID        USER   FD      TYPE             DEVICE  SIZE/OFF       NODE NAME
systemd       1              root  cwd   unknown                                         /proc/1/cwd (readlink: Permission denied)
systemd       1              root  rtd   unknown                                         /proc/1/root (readlink: Permission denied)
lxpanel    1593               uls   12r     FIFO               0,10       0t0      20366 pipe
VBoxClien  1557               uls    5u     unix 0xffff9a1adcb22800       0t0      19578 type=STREAM
exim4      1129       Debian-exim  cwd   unknown                                         /proc/1129/cwd (readlink: Permission denied)
gmain      1491  1570         uls  rtd       DIR              254,0      4096          2 /
                 1570         uls  rtd       DIR              254,0      4096          2 /
bash-4.2:~ #"""

COMMAND_KWARGS_no_parameters = {
}

COMMAND_RESULT_no_parameters = {
    "NUMBER": 7,
    "VALUES": [
        {
            'COMMAND': 'systemd',
            'PID': '1',
            'TID': None,
            'USER': 'root',
            'FD': 'cwd',
            'TYPE': 'unknown',
            'DEVICE': None,
            'SIZE/OFF': None,
            'NODE': None,
            'NAME': '/proc/1/cwd',
        },
        {
            'COMMAND': 'systemd',
            'PID': '1',
            'TID': None,
            'USER': 'root',
            'FD': 'rtd',
            'TYPE': 'unknown',
            'DEVICE': None,
            'SIZE/OFF': None,
            'NODE': None,
            'NAME': '/proc/1/root',
        },
        {
            'COMMAND': 'lxpanel',
            'PID': '1593',
            'TID': None,
            'USER': 'uls',
            'FD': '12r',
            'TYPE': 'FIFO',
            'DEVICE': '0,10',
            'SIZE/OFF': '0t0',
            'NODE': '20366',
            'NAME': 'pipe',
        },
        {
            'COMMAND': 'VBoxClien',
            'PID': '1557',
            'TID': None,
            'USER': 'uls',
            'FD': '5u',
            'TYPE': 'unix',
            'DEVICE': '0xffff9a1adcb22800',
            'SIZE/OFF': '0t0',
            'NODE': '19578',
            'NAME': 'type=STREAM',
        },
        {
            'COMMAND': 'exim4',
            'PID': '1129',
            'TID': None,
            'USER': 'Debian-exim',
            'FD': 'cwd',
            'TYPE': 'unknown',
            'DEVICE': None,
            'SIZE/OFF': None,
            'NODE': None,
            'NAME': '/proc/1129/cwd',
        },
        {
            'COMMAND': 'gmain',
            'PID': '1491',
            'TID': '1570',
            'USER': 'uls',
            'FD': 'rtd',
            'TYPE': 'DIR',
            'DEVICE': '254,0',
            'SIZE/OFF': '4096',
            'NODE': '2',
            'NAME': '/',
        },
        {
            'COMMAND': None,
            'PID': None,
            'TID': '1570',
            'USER': 'uls',
            'FD': 'rtd',
            'TYPE': 'DIR',
            'DEVICE': '254,0',
            'SIZE/OFF': '4096',
            'NODE': '2',
            'NAME': '/',
        }
    ]
}
