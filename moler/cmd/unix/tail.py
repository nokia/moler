# -*- coding: utf-8 -*-
"""
Tail command module.
"""
from moler.cmd.unix.cat import Cat

__author__ = 'Sylwester Golonka, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'sylwester.golonka@nokia.com, marcin.usielski@nokia.com'


class Tail(Cat):
    def __init__(self, connection, path, options=None, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: Moler connection to device, terminal when command is executed.
        :param path: path to file to tail.
        :param options: options passed to command tail.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Tail, self).__init__(connection=connection, path=path, options=options, prompt=prompt,
                                   newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        """
        Builds string with command.

        :return: String with command.
        """
        cmd = "tail"
        if self.options:
            cmd = "{} {} {}".format(cmd, self.path, self.options)
        else:
            cmd = "{} {}".format(cmd, self.path)
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

COMMAND_RESULT = {'LINES': [u'VmallocChunk:   34359608824 kB',
                            u'HardwareCorrupted:     0 kB',
                            u'AnonHugePages:         0 kB',
                            u'HugePages_Total:       0',
                            u'HugePages_Free:        0',
                            u'HugePages_Rsvd:        0',
                            u'HugePages_Surp:        0',
                            u'Hugepagesize:       2048 kB',
                            u'DirectMap4k:       53184 kB',
                            u'DirectMap2M:     4141056 kB',
                            u'user@host:~$']}

COMMAND_KWARGS = {
    "path": "/proc/meminfo"
}
