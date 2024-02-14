# -*- coding: utf-8 -*-
"""
Mount command module.
"""

__author__ = "Agnieszka Bylica, Marcin Usielski"
__copyright__ = "Copyright (C) 2018-2019, Nokia"
__email__ = "agnieszka.bylica@nokia.com, marcin.usielski@nokia.com"


import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure, ParsingDone


class Mount(GenericUnixCommand):
    def __init__(
        self,
        connection,
        options=None,
        device=None,
        directory=None,
        prompt=None,
        newline_chars=None,
        runner=None,
    ):
        """
        Moler class of Unix command mount.

        :param connection: moler connection to device, terminal when command is executed
        :param options: options passed to mount command
        :param device: device on mount command
        :param directory: directory on mount command
        :param prompt: Prompt of the shell
        :param newline_chars: newline chars to split the lines.
        :param runner: runner to run command.
        """
        super(Mount, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )

        # Parameters defined by calling the command
        self.options = options
        self.device = device
        self.directory = directory

        # Internal variables
        self.current_ret["RESULT"] = []
        self.current_ret["ON"] = {}

    def build_command_string(self):
        cmd = "mount"
        if self.options:
            cmd = f"{cmd} {self.options}"
        if self.device:
            cmd = f"{cmd} {self.device}"
        if self.directory:
            cmd = f"{cmd} {self.directory}"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            self._add_line_to_result(line)
            try:
                self._parse_on(line)
                self._command_failure(line)
            except ParsingDone:
                pass
        return super(Mount, self).on_new_line(line, is_full_line)

    def _add_line_to_result(self, line):
        self.current_ret["RESULT"].append(line)

    # sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
    _re_on = re.compile(
        r"(?P<FS_SPEC>\S+)\s+on\s+(?P<FS_FILE>\S+)\s+type\s+(?P<FS_VFSTYPE>\S+)\s+\((?P<FS_MNTOPTS>.*)\)",
        re.I,
    )

    def _parse_on(self, line):
        if self._regex_helper.search_compiled(Mount._re_on, line):
            self.current_ret["ON"][
                self._regex_helper.group("FS_FILE")
            ] = self._regex_helper.groupdict()
            raise ParsingDone()

    _re_error = re.compile(r"mount:\s(?P<ERROR>.*)", re.I)

    def _command_failure(self, line):
        if self._regex_helper.search_compiled(Mount._re_error, line):
            self.set_exception(
                CommandFailure(
                    self, f"ERROR: {self._regex_helper.group('ERROR')}"
                )
            )
            raise ParsingDone


COMMAND_OUTPUT_no_args = """
root@debian:~$ mount
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=1015000k,nr_inodes=253750,mode=755)
root@debian:~$"""

COMMAND_KWARGS_no_args = {}

COMMAND_RESULT_no_args = {
    "RESULT": [
        "sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)",
        "proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)",
        "udev on /dev type devtmpfs (rw,nosuid,relatime,size=1015000k,nr_inodes=253750,mode=755)",
    ],
    "ON": {
        "/sys": {
            "FS_SPEC": "sysfs",
            "FS_FILE": "/sys",
            "FS_VFSTYPE": "sysfs",
            "FS_MNTOPTS": "rw,nosuid,nodev,noexec,relatime",
        },
        "/proc": {
            "FS_SPEC": "proc",
            "FS_FILE": "/proc",
            "FS_VFSTYPE": "proc",
            "FS_MNTOPTS": "rw,nosuid,nodev,noexec,relatime",
        },
        "/dev": {
            "FS_SPEC": "udev",
            "FS_FILE": "/dev",
            "FS_VFSTYPE": "devtmpfs",
            "FS_MNTOPTS": "rw,nosuid,relatime,size=1015000k,nr_inodes=253750,mode=755",
        },
    },
}


COMMAND_OUTPUT_with_options = """
root@debian:~$ mount -l -t ext4
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro,data=ordered)
root@debian:~$"""

COMMAND_KWARGS_with_options = {"options": "-l -t ext4"}

COMMAND_RESULT_with_options = {
    "RESULT": ["/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro,data=ordered)"],
    "ON": {
        "/": {
            "FS_SPEC": "/dev/sda1",
            "FS_FILE": "/",
            "FS_VFSTYPE": "ext4",
            "FS_MNTOPTS": "rw,relatime,errors=remount-ro,data=ordered",
        }
    },
}


COMMAND_OUTPUT_with_device_and_directory = """
root@debian:~$ mount -B /mydata /mnt
root@debian:~$"""

COMMAND_KWARGS_with_device_and_directory = {
    "options": "-B",
    "device": "/mydata",
    "directory": "/mnt",
}

COMMAND_RESULT_with_device_and_directory = {"RESULT": [], "ON": {}}
