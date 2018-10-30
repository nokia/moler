# -*- coding: utf-8 -*-
"""
Grep command module.
"""

__author__ = 'Julia Patacz'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'julia.patacz@nokia.com'

import re

from moler.util.converterhelper import ConverterHelper
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Grep(GenericUnixCommand):

    def __init__(self, connection, options, prompt=None, newline_chars=None, runner=None):
        super(Grep, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self._convert_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.options = options
        self.ret_required = False
        self.current_ret["LINES"] = []
        self.line_no = 0

    def build_command_string(self):
        cmd = "grep {}".format(self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            self.line_no += 1
            try:
                self._parse_path_number_bytes_lines(line)
                self._parse_path_number_lines(line)
                self._parse_path_lines(line)
                self._parse_number_bytes_lines(line)
                self._parse_number_lines(line)
                self._parse_lines(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Grep, self).on_new_line(line, is_full_line)

    def _process_line(self, line, regexp, key_list):
        if self._regex_helper.search_compiled(regexp, line):
            _ret = dict()
            for key in key_list:
                _ret[key] = self._regex_helper.group(key)
            self.current_ret["LINES"].append(_ret)
            raise ParsingDone

    # /etc/iptables/rules.v4:16:196:#PREROUTING-RULES
    _re_path_number_bytes_line = re.compile(r"^(?P<PATH>\/\S+):(?P<NUMBER>\d+):(?P<BYTES>\d+):(?P<LINE>.*)$")
    _key_list_path_number_bytes_line = ["PATH", "NUMBER", "BYTES", "LINE"]

    def _parse_path_number_bytes_lines(self, line):
        return self._process_line(line, Grep._re_path_number_bytes_line, Grep._key_list_path_number_bytes_line)

    # /etc/iptables/rules.v4:16:#PREROUTING-RULES
    _re_path_number_line = re.compile(r"^(?P<PATH>\/\S+):(?P<NUMBER>\d+):(?P<LINE>.*)$")
    _key_list_path_number_line = ["PATH", "NUMBER", "LINE"]

    def _parse_path_number_lines(self, line):
        return self._process_line(line, Grep._re_path_number_line, Grep._key_list_path_number_line)

    # /etc/iptables/rules.v4:#PREROUTING-RULES
    _re_path_line = re.compile(r"^(?P<PATH>\/\S+):(?P<LINE>.*)$")
    _key_list_path_line = ["PATH", "LINE"]

    def _parse_path_lines(self, line):
        return self._process_line(line, Grep._re_path_line, Grep._key_list_path_line)

    # 16:196:#PREROUTING-RULES
    _re_number_bytes_line = re.compile(r"^(?P<NUMBER>\d+):(?P<BYTES>\d+):(?P<LINE>.*)$")
    _key_list_number_bytes_line = ["NUMBER", "BYTES", "LINE"]

    def _parse_number_bytes_lines(self, line):
        return self._process_line(line, Grep._re_number_bytes_line, Grep._key_list_number_bytes_line)

    # 16:#PREROUTING-RULES
    _re_number_line = re.compile(r"^(?P<NUMBER>\d+):(?P<LINE>.*)$")
    _key_list_number_line = ["NUMBER", "LINE"]

    def _parse_number_lines(self, line):
        return self._process_line(line, Grep._re_number_line, Grep._key_list_number_line)

    # Mode: 644
    def _parse_lines(self, line):
        self.current_ret["LINES"].append(line)
        raise ParsingDone


COMMAND_OUTPUT_with_file_path_and_lines_number_and_bytes = """
ute@debdev:~$ grep -bnH PREROUTING /etc/iptables/rules.v4
/etc/iptables/rules.v4:16:196:#PREROUTING-RULES
/etc/iptables/rules.v4:17:214:-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319
/etc/iptables/rules.v4:18:297:-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320
ute@debdev:~$ """
COMMAND_KWARGS_with_file_path_and_lines_number_and_bytes = {
    "options": "-bnH PREROUTING /etc/iptables/rules.v4"
}
COMMAND_RESULT_with_file_path_and_lines_number_and_bytes = {
    "LINES": [
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "#PREROUTING-RULES",
            "NUMBER": "16",
            "BYTES": "196",
        },
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319",
            "NUMBER": "17",
            "BYTES": "214",
        },
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320",
            "NUMBER": "18",
            "BYTES": "297",
        },
    ]
}

COMMAND_OUTPUT_with_file_path_and_lines_number_or_bytes = """
ute@debdev:~$ grep -nH PREROUTING /etc/iptables/rules.v4
/etc/iptables/rules.v4:16:#PREROUTING-RULES
/etc/iptables/rules.v4:17:-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319
/etc/iptables/rules.v4:18:-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320
ute@debdev:~$ """
COMMAND_KWARGS_with_file_path_and_lines_number_or_bytes = {
    "options": "-nH PREROUTING /etc/iptables/rules.v4"
}
COMMAND_RESULT_with_file_path_and_lines_number_or_bytes = {
    "LINES": [
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "#PREROUTING-RULES",
            "NUMBER": "16",
        },
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319",
            "NUMBER": "17",
        },
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320",
            "NUMBER": "18",
        },
    ]
}

COMMAND_OUTPUT_with_file_path = """
ute@debdev:~$ grep -H PREROUTING /etc/iptables/rules.v4
/etc/iptables/rules.v4:#PREROUTING-RULES
/etc/iptables/rules.v4:-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319
/etc/iptables/rules.v4:-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320
ute@debdev:~$ """
COMMAND_KWARGS_with_file_path = {
    "options": "-H PREROUTING /etc/iptables/rules.v4"
}
COMMAND_RESULT_with_file_path = {
    "LINES": [
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "#PREROUTING-RULES",
        },
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319",
        },
        {
            "PATH": "/etc/iptables/rules.v4",
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320",
        },
    ]
}

COMMAND_OUTPUT_with_lines_number_and_bytes = """
ute@debdev:~$ grep -bn PREROUTING /etc/iptables/rules.v4
16:196:#PREROUTING-RULES
17:214:-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319
18:297:-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320
ute@debdev:~$ """
COMMAND_KWARGS_with_lines_number_and_bytes = {
    "options": "-bn PREROUTING /etc/iptables/rules.v4"
}
COMMAND_RESULT_with_lines_number_and_bytes = {
    "LINES": [
        {
            "LINE": "#PREROUTING-RULES",
            "NUMBER": "16",
            "BYTES": "196",
        },
        {
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319",
            "NUMBER": "17",
            "BYTES": "214",
        },
        {
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320",
            "NUMBER": "18",
            "BYTES": "297",
        },
    ]
}

COMMAND_KWARGS_with_lines_number_or_bytes = {
    "options": "-n PREROUTING /etc/iptables/rules.v4"
}

COMMAND_OUTPUT_with_lines_number_or_bytes = """
ute@debdev:~$ grep -n PREROUTING /etc/iptables/rules.v4
16:#PREROUTING-RULES
17:-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319
18:-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320
ute@debdev:~$ """
COMMAND_RESULT_with_lines_number_or_bytes = {
    "LINES": [
        {
            "LINE": "#PREROUTING-RULES",
            "NUMBER": "16",
        },
        {
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 319 -j DNAT --to-destination 10.0.1.2:319",
            "NUMBER": "17",
        },
        {
            "LINE": "-A PREROUTING -i eth0 -p udp -d  --dport 320 -j DNAT --to-destination 10.0.1.2:320",
            "NUMBER": "18",
        },
    ]
}

COMMAND_OUTPUT_ver_human = """
host:~ # grep Mode debconf.conf
Mode: 644
Mode: 600
Mode: 644
host:~ # """
COMMAND_KWARGS_ver_human = {
    "options": "Mode debconf.conf",
}
COMMAND_RESULT_ver_human = {
    "LINES": [
        "Mode: 644",
        "Mode: 600",
        "Mode: 644",
    ]
}
