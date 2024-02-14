# -*- coding: utf-8 -*-
"""
Tail command module.
"""
from moler.cmd.unix.cat import Cat

__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2023, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'


class Tail(Cat):
    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None,
                 failure_only_in_first_line=True):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param path: path to file to tail.
        :param options: options passed to command tail.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param failure_only_in_first_line: Set False to find errors in all lines, True otherwise.
        """
        super(Tail, self).__init__(connection=connection, path=path, options=options, prompt=prompt,
                                   newline_chars=newline_chars, runner=runner,
                                   failure_only_in_first_line=failure_only_in_first_line)

    def build_command_string(self):
        """
        Builds string with command.

        :return: String with command.
        """
        cmd = "tail"
        if self.options:
            cmd = f"{cmd} {self.path} {self.options}"
        else:
            cmd = f"{cmd} {self.path}"
        return cmd


COMMAND_OUTPUT = """
user@host:~$ tail /proc/meminfo
VmallocChunk:   34359608824 kB
HardwareCorrupted:     0 kB
AnonHugePages:         0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
DirectMap4k:       53184 kB
DirectMap2M:     4141056 kB
user@host:~$
"""

COMMAND_RESULT = {'LINES': ['VmallocChunk:   34359608824 kB',
                            'HardwareCorrupted:     0 kB',
                            'AnonHugePages:         0 kB',
                            'HugePages_Total:       0',
                            'HugePages_Free:        0',
                            'HugePages_Rsvd:        0',
                            'HugePages_Surp:        0',
                            'Hugepagesize:       2048 kB',
                            'DirectMap4k:       53184 kB',
                            'DirectMap2M:     4141056 kB',
                            'user@host:~$']}

COMMAND_KWARGS = {
    "path": "/proc/meminfo"
}
