# -*- coding: utf-8 -*-
"""
Mount command module.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Mount(GenericUnixCommand):

    def __init__(self, connection, options=None, device=None, pipe=None, directory=None, prompt=None,
                 new_line_chars=None):
        super(Mount, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.options = options
        self.device = device
        self.pipe = pipe
        self.directory = directory

        # Internal variables
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "mount"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.device and self.pipe and self.directory:
            cmd = "{} {}|{}".format(cmd, self.device, self.directory)
        elif self.device and self.directory:
            cmd = "{} {} {}".format(cmd, self.device, self.directory)
        elif self.device:
            cmd = "{} {}".format(cmd, self.device)
        elif self.directory:
            cmd = "{} {}".format(cmd, self.directory)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                # self._command_failure(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Mount, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        self.current_ret['RESULT'].append(line)
        raise ParsingDone


COMMAND_OUTPUT_ = """
xyz@debian:~$ mount
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=1015000k,nr_inodes=253750,mode=755)
root@debian:~$"""

COMMAND_KWARGS_ = {
}

COMMAND_RESULT_ = {
    'RESULT': ['sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)',
               'proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)',
               'udev on /dev type devtmpfs (rw,nosuid,relatime,size=1015000k,nr_inodes=253750,mode=755)']
}
