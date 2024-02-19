# -*- coding: utf-8 -*-
"""
Hexdump command module.
"""

__author__ = "Agnieszka Bylica", "Adrianna Pienkowska"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "agnieszka.bylica@nokia.com", "adrianna.pienkowska@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Hexdump(GenericUnixCommand):
    def __init__(
        self,
        connection,
        files,
        options=None,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        super(Hexdump, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.options = options
        self.files = files
        self.current_ret["RESULT"] = []

    def build_command_string(self):
        cmd = "hexdump"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.files:
            for afile in self.files:
                cmd = f"{cmd} {afile}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse_hex_line(line)
            except ParsingDone:
                pass
        return super(Hexdump, self).on_new_line(line, is_full_line)

    def _parse_hex_line(self, line):
        separate_hex = line.split()
        if not self.current_ret["RESULT"]:
            separate_hex = separate_hex[1:]
        self.current_ret["RESULT"].extend(separate_hex)
        raise ParsingDone

    _re_error = re.compile(r"hexdump:\s(?P<ERROR_MSG>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Hexdump._re_error, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('ERROR_MSG')}"
                )
            )
            raise ParsingDone


COMMAND_OUTPUT_proper_use = """
xyz@debian:~$ hexdump old
0000000 6741 0a61 6e41 6169 410a 646e 7a72 6a65
0000010 410a 746e 6e6f 0a69
0000018
xyz@debian:~$"""

COMMAND_KWARGS_proper_use = {"files": ["old"]}

COMMAND_RESULT_proper_use = {
    "RESULT": [
        "6741",
        "0a61",
        "6e41",
        "6169",
        "410a",
        "646e",
        "7a72",
        "6a65",
        "0000010",
        "410a",
        "746e",
        "6e6f",
        "0a69",
        "0000018",
    ]
}

COMMAND_OUTPUT_empty_file = """
xyz@debian:~$ hexdump new
xyz@debian:~$"""

COMMAND_KWARGS_empty_file = {"files": ["new"]}

COMMAND_RESULT_empty_file = {"RESULT": []}

COMMAND_OUTPUT_options = """
xyz@debian:~$ hexdump -b old
0000000 101 147 141 012 101 156 151 141 012 101 156 144 162 172 145 152
0000010 012 101 156 164 157 156 151 012
0000018
xyz@debian:~$"""

COMMAND_KWARGS_options = {"files": ["old"], "options": "-b"}

COMMAND_RESULT_options = {
    "RESULT": [
        "101",
        "147",
        "141",
        "012",
        "101",
        "156",
        "151",
        "141",
        "012",
        "101",
        "156",
        "144",
        "162",
        "172",
        "145",
        "152",
        "0000010",
        "012",
        "101",
        "156",
        "164",
        "157",
        "156",
        "151",
        "012",
        "0000018",
    ]
}

COMMAND_OUTPUT_two_files = """
xyz@debian:~$ hexdump old new5
0000000 616a 6c62 6f6b 670a 7572 7a73 616b 6b0a
0000010 6d6f 6f70 0a74 6741 0a61 6e41 6169 410a
0000020 646e 7a72 6a65 410a 746e 6e6f 0a69 416a
0000030 6c62 6f6b 670a 7572 7a73 416b 6b0a 6d6f
0000040 6f70 0074
0000043
xyz@debian:~$"""

COMMAND_KWARGS_two_files = {"files": ["old", "new5"]}

COMMAND_RESULT_two_files = {
    "RESULT": [
        "616a",
        "6c62",
        "6f6b",
        "670a",
        "7572",
        "7a73",
        "616b",
        "6b0a",
        "0000010",
        "6d6f",
        "6f70",
        "0a74",
        "6741",
        "0a61",
        "6e41",
        "6169",
        "410a",
        "0000020",
        "646e",
        "7a72",
        "6a65",
        "410a",
        "746e",
        "6e6f",
        "0a69",
        "416a",
        "0000030",
        "6c62",
        "6f6b",
        "670a",
        "7572",
        "7a73",
        "416b",
        "6b0a",
        "6d6f",
        "0000040",
        "6f70",
        "0074",
        "0000043",
    ]
}
