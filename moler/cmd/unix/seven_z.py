# -*- coding: utf-8 -*-
"""
7zip command module.
To get command instance from device use cmd_name 7z like:
dev.get_cmd(cmd_name='7z'...)
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone
from moler.helpers import ClassProperty, convert_to_int


class SevenZ(GenericUnixCommand):

    def __init__(self, connection, options, archive_file, files=None, prompt=None, newline_chars=None,
                 runner=None):
        """
        Command to work with 7z command.

        :param connection: moler connection to device, terminal when command is executed.
        :param options: options of 7z command.
        :param archive_file: archive file to work on.
        :param files: files to work on. String with file(s) or list of files.
        :param prompt: prompt on which command has to stop working.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        """
        super(SevenZ, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        # Parameters defined by calling the command
        self.options = options
        self.archive_file = archive_file
        self.files = files
        self.ret_required = False
        self._all_sent = False

    def build_command_string(self):
        cmd = "7z"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.archive_file:
            cmd = f"{cmd} {self.archive_file}"
        if self.files is not None:
            if isinstance(self.files, str):
                cmd = f"{cmd} {self.files}"
            else:
                cmd = f"{cmd} {' '.join(self.files)}"
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._parse_all(line=line)
            if is_full_line:
                self._parse_error_via_output_line(line)
                self._parse_file(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        if is_full_line:
            self._all_sent = False
        return super(SevenZ, self).on_new_line(line, is_full_line)

    _re_error_line = re.compile(r'(?P<error>.*(: No more files|ERROR:).*)')

    def _parse_error_via_output_line(self, line):
        if self._cmd_output_started and self._regex_helper.search_compiled(SevenZ._re_error_line, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('error')}"))
            raise ParsingDone()

    # ? (Y)es / (N)o / (A)lways / (S)kip all / A(u)to rename all / (Q)uit? A
    _re_all = re.compile(r"\(Y\)es / \(N\)o / \(A\)lways / \(S\)kip all / A\(u\)to rename all / \(Q\)uit\?")

    def _parse_all(self, line: str) -> None:
        if self._all_sent is False and self._regex_helper.search_compiled(SevenZ._re_all, line):
            self.connection.send("a\n")
            self._all_sent = True
            raise ParsingDone()

    # 2024-07-26 12:04:29 ....A            0            0  b
    _re_parse_file = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<attr>\S+)\s+(?P<size>\d+)\s+(?P<compressed>\d+)\s+(?P<name>.*)$")

    def _parse_file(self, line: str) -> None:
        if self._regex_helper.search_compiled(SevenZ._re_parse_file, line):
            if 'files' not in self.current_ret:
                self.current_ret['files'] = []
                self.current_ret['details'] = []
            self.current_ret['files'].append(self._regex_helper.group('name'))
            detail = {
                'date': self._regex_helper.group('date'),
                'time': self._regex_helper.group('time'),
                'attr': self._regex_helper.group('attr'),
                'size': convert_to_int(self._regex_helper.group('size'), True),
                'compressed': convert_to_int(self._regex_helper.group('compressed'), True),
                'name': self._regex_helper.group('name')
            }
            self.current_ret['details'].append(detail)
            raise ParsingDone()

    @ClassProperty
    def observer_name(self) -> str:
        """
        Return the name of the observer.
        """
        return "7z"


COMMAND_OUTPUT_archive = """7z a arch.7z a b

7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,3 CPUs Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz (806EC),ASM,AES-NI)

Open archive: arch.7z
--
Path = arch.7z
Type = 7z
Physical Size = 124
Headers Size = 124
Solid = -
Blocks = 0

Scanning the drive:
2 files, 0 bytes

Updating archive: arch.7z

Items to compress: 2


Files read from disk: 0
Archive size: 124 bytes (1 KiB)
Everything is Ok
moler_bash# """


COMMAND_RESULT_archive = {
}


COMMAND_KWARGS_archive = {
    "options": "a",
    "archive_file": "arch.7z",
    "files": ["a", "b"],
}


COMMAND_OUTPUT_unarchive = """7z e arch.7z

7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,3 CPUs Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz (806EC),ASM,AES-NI)

Scanning the drive for archives:
1 file, 124 bytes (1 KiB)

Extracting archive: arch.7z
--
Path = arch.7z
Type = 7z
Physical Size = 124
Headers Size = 124
Solid = -
Blocks = 0


Would you like to replace the existing file:
  Path:     ./a
  Size:     0 bytes
  Modified: 2024-07-24 13:17:27
with the file from archive:
  Path:     a
  Size:     0 bytes
  Modified: 2024-07-24 13:17:27
? (Y)es / (N)o / (A)lways / (S)kip all / A(u)to rename all / (Q)uit? A

Everything is Ok

Files: 2
Size:       0
Compressed: 124
moler_bash# """


COMMAND_RESULT_unarchive = {
}


COMMAND_KWARGS_unarchive = {
    "options": "e",
    "archive_file": "arch.7z",
}


COMMAND_OUTPUT_list = """7z l arch.7z

7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,3 CPUs Intel(R) Core(TM) i7-8665U CPU @ 1.90GHz (806EC),ASM,AES-NI)

Scanning the drive for archives:
1 file, 124 bytes (1 KiB)

Listing archive: arch.7z

--
Path = arch.7z
Type = 7z
Physical Size = 124
Headers Size = 124
Solid = -
Blocks = 0

   Date      Time    Attr         Size   Compressed  Name
------------------- ----- ------------ ------------  ------------------------
2024-07-24 13:17:27 ....A            0            0  a
2024-07-26 12:04:29 ....A            0            0  b
------------------- ----- ------------ ------------  ------------------------
2024-07-26 12:04:29

moler_bash# """


COMMAND_KWARGS_list = {
    "options": "l",
    "archive_file": "arch.7z",
}


COMMAND_RESULT_list = {
    "files": ["a", "b"],
    "details": [
        {
            'date': '2024-07-24',
            'time': '13:17:27',
            'attr': '....A',
            'size': 0,
            'compressed': 0,
            'name': 'a'
        },
        {
            'date': '2024-07-26',
            'time': '12:04:29',
            'attr': '....A',
            'size': 0,
            'compressed': 0,
            'name': 'b'
        }
    ]
}
