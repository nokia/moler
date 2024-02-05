# -*- coding: utf-8 -*-
"""
Df command module.
"""

__author__ = "Yeshu Yang"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "yeshu.yang@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper


class Df(GenericUnixCommand):
    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        super(Df, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self._converter_helper = ConverterHelper()

    def build_command_string(self):
        cmd = "df -BM -T -P"
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_filesystem_line(line)
            except ParsingDone:
                pass
        return super(Df, self).on_new_line(line, is_full_line)

    _re_filesystem_line = re.compile(
        r"^(?P<Filesystem>\S+)\s+(?P<Type>\S+)\s+(?P<Size>\S+)M\s+(?P<Used>\S+)M\s+"
        r"(?P<Avail>\S+)M\s+(?P<Use_percentage>\d+)%\s+(?P<Mounted_on>\S+)$"
    )

    def _parse_filesystem_line(self, line):
        if self._regex_helper.search_compiled(Df._re_filesystem_line, line):
            filesystem = self._regex_helper.group("Filesystem")
            Mounted_on = self._regex_helper.group("Mounted_on")
            if "by_FS" not in self.current_ret:
                self.current_ret["by_FS"] = {}
            if "by_MOUNTPOINT" not in self.current_ret:
                self.current_ret["by_MOUNTPOINT"] = {}
            self.current_ret["by_FS"][filesystem] = self._regex_helper.groupdict()
            self.current_ret["by_MOUNTPOINT"][
                Mounted_on
            ] = self._regex_helper.groupdict()
            raise ParsingDone


COMMAND_OUTPUT = """
[root@Pclinux90: /home/runner]# df -BM -T -P
Filesystem    Type 1048576-blocks      Used Available Capacity Mounted on
/dev/sda2     ext3          4039M     1760M     2073M      46% /
udev         tmpfs           999M        1M      999M       1% /dev
/dev/sda3     ext3        144169M   109553M    27293M      81% /home
//175.28.247.174/emssim cifs      433150M     7865M   403282M       2% /home/emssim
//175.28.247.165/vobs cifs      918588M     1299M   916356M       1% /vobs
//175.28.247.165/vob cifs      918588M     1299M   916356M       1% /vob
//175.28.247.165/cc cifs      918588M     1299M   916356M       1% /cc
[root@Pclinux90: /home/runner]#"""


COMMAND_RESULT = {
    "by_FS": {
        "//175.28.247.165/vobs": {
            "Avail": "916356",
            "Used": "1299",
            "Type": "cifs",
            "Size": "918588",
            "Filesystem": "//175.28.247.165/vobs",
            "Mounted_on": "/vobs",
            "Use_percentage": "1",
        },
        "//175.28.247.165/vob": {
            "Avail": "916356",
            "Used": "1299",
            "Type": "cifs",
            "Size": "918588",
            "Filesystem": "//175.28.247.165/vob",
            "Mounted_on": "/vob",
            "Use_percentage": "1",
        },
        "/dev/sda3": {
            "Avail": "27293",
            "Used": "109553",
            "Type": "ext3",
            "Size": "144169",
            "Filesystem": "/dev/sda3",
            "Mounted_on": "/home",
            "Use_percentage": "81",
        },
        "//175.28.247.165/cc": {
            "Avail": "916356",
            "Used": "1299",
            "Type": "cifs",
            "Size": "918588",
            "Filesystem": "//175.28.247.165/cc",
            "Mounted_on": "/cc",
            "Use_percentage": "1",
        },
        "/dev/sda2": {
            "Avail": "2073",
            "Used": "1760",
            "Type": "ext3",
            "Size": "4039",
            "Filesystem": "/dev/sda2",
            "Mounted_on": "/",
            "Use_percentage": "46",
        },
        "//175.28.247.174/emssim": {
            "Avail": "403282",
            "Used": "7865",
            "Type": "cifs",
            "Size": "433150",
            "Filesystem": "//175.28.247.174/emssim",
            "Mounted_on": "/home/emssim",
            "Use_percentage": "2",
        },
        "udev": {
            "Avail": "999",
            "Used": "1",
            "Type": "tmpfs",
            "Size": "999",
            "Filesystem": "udev",
            "Mounted_on": "/dev",
            "Use_percentage": "1",
        },
    },
    "by_MOUNTPOINT": {
        "/home/emssim": {
            "Avail": "403282",
            "Used": "7865",
            "Type": "cifs",
            "Size": "433150",
            "Filesystem": "//175.28.247.174/emssim",
            "Mounted_on": "/home/emssim",
            "Use_percentage": "2",
        },
        "/": {
            "Avail": "2073",
            "Used": "1760",
            "Type": "ext3",
            "Size": "4039",
            "Filesystem": "/dev/sda2",
            "Mounted_on": "/",
            "Use_percentage": "46",
        },
        "/dev": {
            "Avail": "999",
            "Used": "1",
            "Type": "tmpfs",
            "Size": "999",
            "Filesystem": "udev",
            "Mounted_on": "/dev",
            "Use_percentage": "1",
        },
        "/vobs": {
            "Avail": "916356",
            "Used": "1299",
            "Type": "cifs",
            "Size": "918588",
            "Filesystem": "//175.28.247.165/vobs",
            "Mounted_on": "/vobs",
            "Use_percentage": "1",
        },
        "/vob": {
            "Avail": "916356",
            "Used": "1299",
            "Type": "cifs",
            "Size": "918588",
            "Filesystem": "//175.28.247.165/vob",
            "Mounted_on": "/vob",
            "Use_percentage": "1",
        },
        "/cc": {
            "Avail": "916356",
            "Used": "1299",
            "Type": "cifs",
            "Size": "918588",
            "Filesystem": "//175.28.247.165/cc",
            "Mounted_on": "/cc",
            "Use_percentage": "1",
        },
        "/home": {
            "Avail": "27293",
            "Used": "109553",
            "Type": "ext3",
            "Size": "144169",
            "Filesystem": "/dev/sda3",
            "Mounted_on": "/home",
            "Use_percentage": "81",
        },
    },
}

COMMAND_KWARGS = {}
