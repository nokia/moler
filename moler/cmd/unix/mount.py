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

    def __init__(self, connection, options=None, device=None, directory=None, prompt=None, newline_chars=None,
                 runner=None):
        super(Mount, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self.options = options
        self.device = device
        self.directory = directory

        # Internal variables
        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "mount"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.device:
            cmd = "{} {}".format(cmd, self.device)
        if self.directory:
            cmd = "{} {}".format(cmd, self.directory)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse_line(line)
            except ParsingDone:
                pass
        return super(Mount, self).on_new_line(line, is_full_line)

    def _parse_line(self, line):
        self.current_ret['RESULT'].append(line)
        raise ParsingDone

    _re_error = re.compile(r"mount:\s(?P<ERROR>.*)", re.I)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Mount._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone


COMMAND_OUTPUT_no_args = """
root@debian:~$ mount
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=1015000k,nr_inodes=253750,mode=755)
root@debian:~$"""

COMMAND_KWARGS_no_args = {
}

COMMAND_RESULT_no_args = {
    'RESULT': ['sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)',
               'proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)',
               'udev on /dev type devtmpfs (rw,nosuid,relatime,size=1015000k,nr_inodes=253750,mode=755)']
}


COMMAND_OUTPUT_with_options = """
root@debian:~$ mount -l -t ext4
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro,data=ordered)
root@debian:~$"""

COMMAND_KWARGS_with_options = {
    'options': '-l -t ext4'
}

COMMAND_RESULT_with_options = {
    'RESULT': ['/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro,data=ordered)']
}


COMMAND_OUTPUT_with_device_and_directory = """
root@debian:~$ mount -B /mydata /mnt
root@debian:~$"""

COMMAND_KWARGS_with_device_and_directory = {
    'options': '-B', 'device': '/mydata', 'directory': '/mnt'
}

COMMAND_RESULT_with_device_and_directory = {
    'RESULT': []
}
