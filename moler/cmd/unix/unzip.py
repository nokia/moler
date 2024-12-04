# -*- coding: utf-8 -*-
__author__ = "Mateusz Szczurek"
__copyright__ = "Copyright (C) 2019, Nokia"
__email__ = "mateusz.m.szczurek@nokia.com"

import datetime
import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Unzip(GenericUnixCommand):
    """Unzip command class."""

    def __init__(
        self,
        connection,
        zip_file,
        extract_dir=None,
        options="",
        overwrite=False,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        """
        Unzip command.

        :param connection: Moler connection to device, terminal when command is executed.
        :param zip_file: Name of a file which shall be unzipped.
        :param extract_dir: An optional extract_dir to which to extract files.
        :param options: Options of command unzip.
        :param overwrite: A parameter that determines whether an existing file shall be overwritten.
        :param prompt: Expected prompt that has been sent by device after command execution.
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Unzip, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        # Parameters defined by calling the command
        self.options = options
        self.zip_file = zip_file
        self.extract_dir = extract_dir
        self.overwrite = overwrite
        self.ret_required = False
        self._is_overwritten = False
        self.current_ret["FILE_LIST"] = []
        self.current_ret["FILE_DICT"] = {}

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of the command to send over a connection to the device.
        """
        if self.options and self.extract_dir:
            cmd = f"unzip {self.options} {self.zip_file} -d {self.extract_dir}"
        elif self.extract_dir:
            cmd = f"unzip {self.zip_file} -d {self.extract_dir}"
        elif self.options:
            cmd = f"unzip {self.options} {self.zip_file}"
        else:
            cmd = f"unzip {self.zip_file}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._asks_to_overwrite(line)
            if is_full_line:
                self._parse_error_no_file(line)
                self._parse_error_can_not_create_dir(line)
                self._parse_info_output(line)
                self._parse_v_option(line)
        except ParsingDone:
            pass  # line has been fully parsed by one of above parse-methods
        return super(Unzip, self).on_new_line(line, is_full_line)

    _re_info_output = re.compile(r"extracting:+\s*(?P<FILE_NAME>\S*)")

    def _parse_info_output(self, line):
        """
        Parse file name in line abd append it to FILE_LIST list.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._regex_helper.search_compiled(Unzip._re_info_output, line):
            self.current_ret["FILE_LIST"].append(self._regex_helper.group("FILE_NAME"))
            raise ParsingDone

    # unzip:  cannot find or open test.zip, test.zip.zip or test.zip.ZIP.
    _re_no_file = re.compile(r"(?P<error>unzip:+\s*cannot find or open.*)")

    def _parse_error_no_file(self, line):
        """
        Parse errors in line and set exception in case of any errors were parsed.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._cmd_output_started and self._regex_helper.search_compiled(
            Unzip._re_no_file, line
        ):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('error')}"
                )
            )
            raise ParsingDone

    # replace test.txt? [y]es, [n]o, [A]ll, [N]one, [r]ename:
    _re_overwrite = re.compile(
        r"replace\s*(?P<OVERWRITE>\S*)\?\s*\[y]es,\s*\[n\]o,\s*\[A\]ll,\s*\[N\]one,\s*\[r\]ename:",
        re.IGNORECASE,
    )

    def _asks_to_overwrite(self, line):
        """
        Parse line in order to find the overwrite query and send line in accordance to overwrite parameter.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._regex_helper.search_compiled(Unzip._re_overwrite, line) and not self._is_overwritten:
            self._is_overwritten = True
            if self.overwrite:
                self.connection.sendline("A")
            else:
                self.connection.sendline("N")
                self.set_exception(
                    CommandFailure(
                        self,
                        f"ERROR: {self._regex_helper.group('OVERWRITE')} already exists",
                    )
                )
            raise ParsingDone

    # 0  Stored        0   0% 2019-01-30 08:58 00000000  file1.txt
    _re_assign_values = re.compile(
        r"(?P<LENGTH>\d+)\s+(?P<METHOD>\S+)\s+(?P<SIZE>\d+)\s+(?P<CMPR>\S+)\s+(?P<DATE>\S+)\s+(?P<TIME>\S+)\s+"
        r"(?P<CRC>\S+)\s+(?P<NAME>\S+)"
    )

    def _parse_v_option(self, line):
        """
        Check if 'v' option is in use and parse file details in line. Append file name to FILE_LIST list and update
        FILE_DICT with file details.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if "v" in self.options and self._regex_helper.search_compiled(
            Unzip._re_assign_values, line
        ):
            _date_time_str = f"{self._regex_helper.group('DATE')} {self._regex_helper.group('TIME')}"
            self.current_ret["FILE_LIST"].append(self._regex_helper.group("NAME"))
            self.current_ret["FILE_DICT"].update(
                {
                    self._regex_helper.group("NAME"): {
                        "length": self._regex_helper.group("LENGTH"),
                        "method": self._regex_helper.group("METHOD"),
                        "size": self._regex_helper.group("SIZE"),
                        "cmpr": self._regex_helper.group("CMPR"),
                        "date": self._regex_helper.group("DATE"),
                        "time": self._regex_helper.group("TIME"),
                        "crc-32": self._regex_helper.group("CRC"),
                        "datetime": datetime.datetime.strptime(
                            _date_time_str, "%Y-%m-%d %H:%M"
                        ),
                    }
                }
            )
            raise ParsingDone

    # unzip:  caution: filename not matched:  -q
    _re_filename_not_matched = re.compile(
        r"(?P<caution>cannot create extraction directory:.*\S)"
    )

    def _parse_error_can_not_create_dir(self, line):
        """
        Parse errors in line and set exception in case of any errors were parsed.

        :param line: Line to process.
        :return: None but raises ParsingDone if line has the information to handle by this method.
        """
        if self._cmd_output_started and self._regex_helper.search_compiled(
            Unzip._re_filename_not_matched, line
        ):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('caution')}"
                )
            )
            raise ParsingDone


COMMAND_OUTPUT_parse_info_output = """
host:~ # unzip test.zip
Archive:  test.zip
 extracting: file1.txt
 extracting: file.txt
host:~ # """

COMMAND_RESULT_parse_info_output = {
    "FILE_LIST": ["file1.txt", "file.txt"],
    "FILE_DICT": {},
}

COMMAND_KWARGS_parse_info_output = {"zip_file": "test.zip"}

COMMAND_OUTPUT_overwrite = """
host:~ # unzip test.zip
Archive:  test.zip
replace test.txt? [y]es, [n]o, [A]ll, [N]one, [r]ename:
 extracting: test.txt
host:~ # """

COMMAND_RESULT_overwrite = {"FILE_LIST": ["test.txt"], "FILE_DICT": {}}

COMMAND_KWARGS_overwrite = {"zip_file": "test.zip", "overwrite": True}

COMMAND_OUTPUT_v_option = """
host:~ # unzip -v files.zip
Archive:  files.zip
 Length   Method    Size  Cmpr    Date    Time   CRC-32   Name
--------  ------  ------- ---- ---------- ----- --------  ----
       0  Stored        0   0% 2019-01-30 08:58 00000000  file1.txt
       0  Stored        0   0% 2019-01-30 08:58 00000000  file.txt
--------          -------  ---                            -------
       0                0   0%                            2 files
host:~ # """

COMMAND_RESULT_v_option = {
    "FILE_LIST": ["file1.txt", "file.txt"],
    "FILE_DICT": {
        "file.txt": {
            "cmpr": "0%",
            "crc-32": "00000000",
            "date": "2019-01-30",
            "datetime": datetime.datetime(2019, 1, 30, 8, 58),
            "length": "0",
            "method": "Stored",
            "size": "0",
            "time": "08:58",
        },
        "file1.txt": {
            "cmpr": "0%",
            "crc-32": "00000000",
            "date": "2019-01-30",
            "datetime": datetime.datetime(2019, 1, 30, 8, 58),
            "length": "0",
            "method": "Stored",
            "size": "0",
            "time": "08:58",
        },
    },
}

COMMAND_KWARGS_v_option = {
    "options": "-v",
    "zip_file": "files.zip",
}

COMMAND_OUTPUT_extract_dir = """
host:~ # unzip test.zip -d /home/ute/temp
Archive:  test.zip
 extracting: /home/ute/temp/test.txt
host:~ # """

COMMAND_RESULT_extract_dir = {"FILE_LIST": ["/home/ute/temp/test.txt"], "FILE_DICT": {}}

COMMAND_KWARGS_extract_dir = {"zip_file": "test.zip", "extract_dir": "/home/ute/temp"}

COMMAND_OUTPUT_options_extract_dir = """
host:~ # unzip -u test.zip -d /home/ute/temp
Archive:  test.zip
 extracting: /home/ute/temp/test.txt
host:~ # """

COMMAND_RESULT_options_extract_dir = {
    "FILE_LIST": ["/home/ute/temp/test.txt"],
    "FILE_DICT": {},
}

COMMAND_KWARGS_options_extract_dir = {
    "options": "-u",
    "zip_file": "test.zip",
    "extract_dir": "/home/ute/temp",
}
