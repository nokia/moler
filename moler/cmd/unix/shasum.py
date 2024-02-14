# -*- coding: utf-8 -*-
"""
Shasum command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone

__author__ = "Marcin Usielski"
__copyright__ = "Copyright (C) 2020, Nokia"
__email__ = "marcin.usielski@nokia.com"


class Shasum(GenericUnixCommand):
    def __init__(
        self,
        connection,
        path,
        options=None,
        cmd_kind="shasum",
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        """
        Moler base class for commands that change prompt.

        :param connection: moler connection to device, terminal when command is executed.
        :param path: path to file(s) to calculate sum.
        :param cmd_kind: command to calculate sum, eg. sha256sum, sha224sum or shasum.
        :param prompt: prompt on start system (where command starts).
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        """
        super(Shasum, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self.path = path
        self.options = options
        self.cmd_kind = cmd_kind

    def build_command_string(self):
        """
        Builds command string form parameters.

        :return: Command string
        """
        cmd = self.cmd_kind
        if self.options:
            cmd = f"{cmd} {self.options} {self.path}"
        else:
            cmd = f"{cmd} {self.path}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses every line from connection.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._parse_sum(line)
            except ParsingDone:
                pass
        return super(Shasum, self).on_new_line(line, is_full_line)

    _re_parse_sum = re.compile(r"(?P<SUM>[\da-f]+)\s+(?P<FILE>\S+)")

    def _parse_sum(self, line):
        """
        Parses sum from command output.

        :param line: Line from device/connection.
        :return: None
        :raises ParsingDone if line was processed by the method.
        """
        if self._regex_helper.search_compiled(Shasum._re_parse_sum, line):
            file = self._regex_helper.group("FILE")
            shasum = self._regex_helper.group("SUM")
            self.current_ret["SUM"] = shasum
            self.current_ret["FILE"] = file
            if "FILES" not in self.current_ret:
                self.current_ret["FILES"] = {}
            self.current_ret["FILES"][file] = shasum
        raise ParsingDone()


COMMAND_OUTPUT_parms = """shasum test.txt
138114f10aa62da8ccd762b93f0f1f2b83a4c47c  test.txt
user@server:~$"""

COMMAND_RESULT_parms = {
    "FILE": "test.txt",
    "SUM": "138114f10aa62da8ccd762b93f0f1f2b83a4c47c",
    "FILES": {
        "test.txt": "138114f10aa62da8ccd762b93f0f1f2b83a4c47c",
    },
}

COMMAND_KWARGS_parms = {
    "path": "test.txt",
}

COMMAND_OUTPUT_many_files = """sha256sum *.py
30dadab8f7e0dfdd1e5f9a5e3c73fdb4d5ce958c71fff7b5fc782d18ed729f79  abstract_moler_connection.py
9d47eaea79621966becfbaa8e97c3700ff498958d33447c37c05e22164d399b4  asyncio_runner.py
aafaa899c8863770395b8feb3460b88c2b66ba77a0e6fd82e9ce18fc06c8c2c2  command.py
user@server:~$"""

COMMAND_RESULT_many_files = {
    "FILE": "command.py",
    "SUM": "aafaa899c8863770395b8feb3460b88c2b66ba77a0e6fd82e9ce18fc06c8c2c2",
    "FILES": {
        "abstract_moler_connection.py": "30dadab8f7e0dfdd1e5f9a5e3c73fdb4d5ce958c71fff7b5fc782d18ed729f79",
        "asyncio_runner.py": "9d47eaea79621966becfbaa8e97c3700ff498958d33447c37c05e22164d399b4",
        "command.py": "aafaa899c8863770395b8feb3460b88c2b66ba77a0e6fd82e9ce18fc06c8c2c2",
    },
}

COMMAND_KWARGS_many_files = {
    "path": "*.py",
    "cmd_kind": "sha256sum",
}

COMMAND_OUTPUT_many_files_224 = """shasum -a 224 *.py
6545a64ce6952ba6871bafb5f0591bdf012fee7c06c8b6f919e8df07  abstract_moler_connection.py
8af16b9740b39ef77bdbbbfeafbbd790be1c72e553b1a21190d510f6  asyncio_runner.py
de1291c73280e5f108d5c6c43c3ad7c7983344f2eca8add011f59ecd  command.py

user@server:~$"""

COMMAND_RESULT_many_files_224 = {
    "FILE": "command.py",
    "SUM": "de1291c73280e5f108d5c6c43c3ad7c7983344f2eca8add011f59ecd",
    "FILES": {
        "abstract_moler_connection.py": "6545a64ce6952ba6871bafb5f0591bdf012fee7c06c8b6f919e8df07",
        "asyncio_runner.py": "8af16b9740b39ef77bdbbbfeafbbd790be1c72e553b1a21190d510f6",
        "command.py": "de1291c73280e5f108d5c6c43c3ad7c7983344f2eca8add011f59ecd",
    },
}

COMMAND_KWARGS_many_files_224 = {
    "path": "*.py",
    "options": "-a 224",
}
