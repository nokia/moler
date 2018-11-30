# -*- coding: utf-8 -*-
"""
Find command module.
"""

__author__ = 'Adrianna Pienkowska, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com, marcin.usielski@nokia.com'

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.helpers import copy_list
import re


class Find(GenericUnixCommand):
    def __init__(self, connection, paths=None, prompt=None, newline_chars=None, options=None, operators=None,
                 runner=None):
        """
        :param connection: moler connection to device, terminal when command is executed
        :param paths: list of paths to find
        :param prompt: prompt on start system (where command find starts).
        :param newline_chars: characters to split lines.
        :param options: unix find command options
        :param operators: operators of unix command find
        :param runner: Runner to run command
        """
        super(Find, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self.operators = operators
        self.paths = copy_list(paths)
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "find"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.paths:
            for afile in self.paths:
                cmd = "{} {}".format(cmd, afile)
        if self.operators:
            cmd = "{} {}".format(cmd, self.operators)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                self._ignore_permission_denied(line)
                self._command_failure(line)
                self._parse_file(line)
            except ParsingDone:
                pass
        return super(Find, self).on_new_line(line, is_full_line)

    _re_permission_denied = re.compile(r"find:\s(?P<PERMISSION_DENIED>.*Permission denied)", re.IGNORECASE)

    def _ignore_permission_denied(self, line):
        """
        Checks if line contains information about permission denied
        :param line: Line from device
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(Find._re_permission_denied, line):
            raise ParsingDone()

    _re_error = re.compile(r"(find|bash):\s(?P<ERROR_MSG_FIND>.*)", re.IGNORECASE)

    def _command_failure(self, line):
        """
        Checks if line contains information about failure of command
        :param line: Line from device
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(Find._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR_MSG_FIND"))))
            raise ParsingDone()

    def _parse_file(self, line):
        """
        Add line to value returning by the command
        :param line: Line from device
        :return: Nothing but raises ParsingDone
        """
        self.current_ret['RESULT'].append(line)
        raise ParsingDone()


COMMAND_OUTPUT_without_arguments = """
xyz@debian:~$ find
.
./key
./sed
./sed/new
./sed/new2
./sed/is_true.py
./sed/new5
./sed/new3
./sed/test
./sed/old
./sed/file2.sed
./sed/file1.sed
./uname
./uname/uname_trash.py
./uname/uname.py
xyz@debian:~$"""

COMMAND_KWARGS_without_arguments = {}

COMMAND_RESULT_without_arguments = {
    'RESULT': ['.', './key', './sed', './sed/new', './sed/new2', './sed/is_true.py', './sed/new5', './sed/new3',
               './sed/test', './sed/old', './sed/file2.sed', './sed/file1.sed', './uname', './uname/uname_trash.py',
               './uname/uname.py']
}

COMMAND_OUTPUT_with_files = """
xyz@debian:~$ find sed uname
sed
sed/new
sed/new2
sed/is_true.py
sed/new5
sed/new3
sed/test
sed/old
sed/file2.sed
sed/file1.sed
uname
uname/uname_trash.py
uname/uname.py
xyz@debian:~$"""

COMMAND_KWARGS_with_files = {
    'paths': ['sed', 'uname']
}

COMMAND_RESULT_with_files = {
    'RESULT': ['sed', 'sed/new', 'sed/new2', 'sed/is_true.py', 'sed/new5', 'sed/new3',
               'sed/test', 'sed/old', 'sed/file2.sed', 'sed/file1.sed', 'uname', 'uname/uname_trash.py',
               'uname/uname.py']
}

COMMAND_OUTPUT_with_options = """
xyz@debian:~$ find -L
.
./key
./to_new5
./sed
./sed/new
./sed/new2
./sed/is_true.py
./sed/new5
./sed/new3
./sed/test
./sed/old
./sed/file2.sed
./sed/file1.sed
./uname
./uname/uname_trash.py
./uname/uname.py
xyz@debian:~$"""

COMMAND_KWARGS_with_options = {
    'options': '-L'
}

COMMAND_RESULT_with_options = {
    'RESULT': ['.', './key', './to_new5', './sed', './sed/new', './sed/new2', './sed/is_true.py', './sed/new5',
               './sed/new3', './sed/test', './sed/old', './sed/file2.sed', './sed/file1.sed', './uname',
               './uname/uname_trash.py', './uname/uname.py']
}

COMMAND_OUTPUT_with_operators = """
xyz@debian:~$ find -name 'my*' -type f
./Pobrane/pycharm-community-2018.1.4/helpers/typeshed/third_party/2and3/mypy_extensions.pyi
./Pobrane/pycharm-community-2018.1.4/helpers/typeshed/tests/mypy_blacklist.txt
./Pobrane/pycharm-community-2018.1.4/helpers/typeshed/tests/mypy_selftest.py
./Pobrane/pycharm-community-2018.1.4/helpers/typeshed/tests/mypy_test.py
./.config/libreoffice/4/user/autotext/mytexts.bau
xyz@debian:~$"""

COMMAND_KWARGS_with_operators = {
    'operators': "-name 'my*' -type f"
}

COMMAND_RESULT_with_operators = {
    'RESULT': ['./Pobrane/pycharm-community-2018.1.4/helpers/typeshed/third_party/2and3/mypy_extensions.pyi',
               './Pobrane/pycharm-community-2018.1.4/helpers/typeshed/tests/mypy_blacklist.txt',
               './Pobrane/pycharm-community-2018.1.4/helpers/typeshed/tests/mypy_selftest.py',
               './Pobrane/pycharm-community-2018.1.4/helpers/typeshed/tests/mypy_test.py',
               './.config/libreoffice/4/user/autotext/mytexts.bau']
}

COMMAND_OUTPUT_no_files_found = """
xyz@debian:~$ find Doc -name 'my*' -type f -print.
xyz@debian:~$"""

COMMAND_KWARGS_no_files_found = {
    'paths': ['Doc'],
    'operators': "-name 'my*' -type f"
}

COMMAND_RESULT_no_files_found = {
    'RESULT': []
}

COMMAND_OUTPUT_permission_denied = """
xyz@debian:~$ find
./devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/autosuspend_delay_ms
./devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/runtime_enabled
./devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/runtime_active_time
./devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/control
./devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/async
find: './fs/fuse/connections/38': Permission denied
./module/kernel
./module/kernel/parameters
./module/kernel/parameters/crash_kexec_post_notifiers
./module/kernel/parameters/consoleblank
./module/kernel/parameters/initcall_debug
find: './kernel/debug': Permission denied
xyz@debian:~$"""

COMMAND_KWARGS_permission_denied = {}

COMMAND_RESULT_permission_denied = {
    'RESULT': ['./devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/autosuspend_delay_ms',
               './devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/runtime_enabled',
               './devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/runtime_active_time',
               './devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/control',
               './devices/LNXSYSTM:00/LNXPWRBN:00/input/input3/power/async',
               './module/kernel', './module/kernel/parameters', './module/kernel/parameters/crash_kexec_post_notifiers',
               './module/kernel/parameters/consoleblank', './module/kernel/parameters/initcall_debug']
}
