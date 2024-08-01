# -*- coding: utf-8 -*-
"""
Gunzip command module.
"""

__author__ = "Adrianna Pienkowska, Marcin Usielski"
__copyright__ = "Copyright (C) 2018-2024, Nokia"
__email__ = "adrianna.pienkowska@nokia.com, marcin.usielski@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Gunzip(GenericUnixCommand):
    def __init__(
        self,
        connection,
        archive_name,
        output_file_name=None,
        options=None,
        overwrite=False,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        super(Gunzip, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.archive_name = archive_name
        self.output_file_name = output_file_name
        self.options = options
        self.overwrite = overwrite
        self.keys = []
        self.current_ret["RESULT"] = []
        self.values = []

        # private variables
        self._answered_file = None
        self._asks_to_overwrite_send = False

    def build_command_string(self):
        cmd = "gunzip"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.archive_name:
            for file in self.archive_name:
                cmd = f"{cmd} {file}"
        if self.output_file_name:
            cmd = f"{cmd} > {self.output_file_name}"
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._parse_info_output(line)
            self._asks_to_overwrite(line)
            self._create_dictionary_at_l_option(line)
            self._command_failure(line)
            self._parse_verbose(line)
        except ParsingDone:
            pass
        return super(Gunzip, self).on_new_line(line, is_full_line)

    _re_info_output = re.compile(r" -- replaced with")

    def _parse_info_output(self, line):
        if self._regex_helper.search_compiled(Gunzip._re_info_output, line):
            self.current_ret["RESULT"].append(line)
            raise ParsingDone

    _re_overwrite = re.compile(
        r"gzip:\s+(?P<FILE_NAME>.*)\s+already exists", re.IGNORECASE
    )

    def _asks_to_overwrite(self, line):
        if self._regex_helper.search_compiled(Gunzip._re_overwrite, line):
            current_file = self._regex_helper.group("FILE_NAME")
            if current_file != self._answered_file:
                if self.overwrite:
                    self.connection.sendline("y")
                else:
                    self.connection.sendline("n")
                    self.set_exception(
                        CommandFailure(
                            self, f"ERROR: {current_file} already exists"
                        )
                    )
                self._answered_file = current_file
            raise ParsingDone

    _re_l_option = re.compile(
        r"(?P<L_OPTION> compressed\s*uncompressed\s*ratio\s*uncompressed_name.*)",
        re.IGNORECASE,
    )

    def _create_dictionary_at_l_option(self, line):
        if self.keys and not self.current_ret["RESULT"]:
            self.values = line.strip().split()
            if "date" in self.keys:
                self.values = self.values[:2] + [f"{self.values[2]} {self.values[3]}"] + self.values[4:]
            self.current_ret["RESULT"].append(dict(zip(self.keys, self.values)))
            raise ParsingDone
        if self._regex_helper.search_compiled(Gunzip._re_l_option, line):
            self.keys = line.strip().split()
            raise ParsingDone

    _re_error = re.compile(r"gzip:\s(?P<ERROR_MSG>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Gunzip._re_error, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('ERROR_MSG')}"
                )
            )
            raise ParsingDone

    # a.gz:	  0.0% -- created a
    _re_verbose = re.compile(r"(?P<COMPRESSED_FILE>\S+):.*\s+(?P<RATIO>[\d\.]+%)\s+\S+\s+\S+\s+(?P<DECOMPRESSED_FILE>\S+)")

    def _parse_verbose(self, line):
        if self._regex_helper.search_compiled(Gunzip._re_verbose, line):
            if 'files' not in self.current_ret:
                self.current_ret['files'] = []
                self.current_ret['details'] = []
            file_desc = {
                'compressed_file': self._regex_helper.group("COMPRESSED_FILE"),
                'ratio': self._regex_helper.group("RATIO"),
                'decompressed_file': self._regex_helper.group("DECOMPRESSED_FILE")
            }
            self.current_ret['files'].append(self._regex_helper.group("DECOMPRESSED_FILE"))
            self.current_ret['details'].append(file_desc)

            raise ParsingDone()


COMMAND_OUTPUT_without_options = """
xyz@debian:~$ gunzip new.gz
xyz@debian:~$"""

COMMAND_KWARGS_without_options = {"archive_name": ["new.gz"]}

COMMAND_RESULT_without_options = {"RESULT": []}


COMMAND_OUTPUT_loud_options = """
xyz@debian:~$ gunzip -v new.gz
new.gz:	 -7.7% -- replaced with new
xyz@debian:~$"""

COMMAND_KWARGS_loud_options = {"archive_name": ["new.gz"], "options": "-v"}

COMMAND_RESULT_loud_options = {"RESULT": ["new.gz:\t -7.7% -- replaced with new"]}


COMMAND_OUTPUT_overwrite = """
xyz@debian:~$ gunzip new.gz
gzip: new already exists; do you wish to overwrite (y or n)? xyz@debian:~$"""

COMMAND_KWARGS_overwrite = {"archive_name": ["new.gz"], "overwrite": "True"}

COMMAND_RESULT_overwrite = {"RESULT": []}


COMMAND_OUTPUT_send_to_another_directory = """
xyz@debian:~$ gunzip afile.gz > sed/afile
xyz@debian:~$"""

COMMAND_KWARGS_send_to_another_directory = {
    "archive_name": ["afile.gz"],
    "output_file_name": "sed/afile",
}

COMMAND_RESULT_send_to_another_directory = {"RESULT": []}


COMMAND_OUTPUT_on_l_option = """
xyz@debian:~$ gunzip -l afile.gz
         compressed        uncompressed  ratio uncompressed_name
                 26                   0   0.0% afile
xyz@debian:~$"""

COMMAND_KWARGS_on_l_option = {"archive_name": ["afile.gz"], "options": "-l"}

COMMAND_RESULT_on_l_option = {
    "RESULT": [
        {
            "compressed": "26",
            "uncompressed": "0",
            "ratio": "0.0%",
            "uncompressed_name": "afile",
        }
    ]
}


COMMAND_OUTPUT_on_vl_option = """
xyz@debian:~$ gunzip -vl afile.gz
method  crc     date  time           compressed        uncompressed  ratio uncompressed_name
defla 00000000 Aug 9 12:27                  26                   0   0.0% afile
xyz@debian:~$"""

COMMAND_KWARGS_on_vl_option = {"archive_name": ["afile.gz"], "options": "-vl"}

COMMAND_RESULT_on_vl_option = {
    "RESULT": [
        {
            "method": "defla",
            "crc": "00000000",
            "date": "Aug 9",
            "time": "12:27",
            "compressed": "26",
            "uncompressed": "0",
            "ratio": "0.0%",
            "uncompressed_name": "afile",
        }
    ]
}


COMMAND_OUTPUT_verbose = """gunzip -fkv a.gz b.gz
a.gz:	  0.0% -- created a
b.gz:	  0.0% -- created b
moler_bash# """

COMMAND_KWARGS_verbose = {"archive_name": ["a.gz", "b.gz"], "options": "-fkv"}

COMMAND_RESULT_verbose = {
    "files": ["a", "b"],
    "details": [
        {
            'compressed_file': 'a.gz',
            'ratio': '0.0%',
            'decompressed_file': 'a',
        },
        {
            'compressed_file': 'b.gz',
            'ratio': '0.0%',
            'decompressed_file': 'b',
        }
    ],
    'RESULT': []
}
