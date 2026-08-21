# -*- coding: utf-8 -*-
"""
Df command module.
"""

__author__ = "Yeshu Yang, Marcin Usielski"
__copyright__ = "Copyright (C) 2018-2026, Nokia"
__email__ = "yeshu.yang@nokia.com, marcin.usielski@nokia.com"

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.util.converterhelper import ConverterHelper


class Df(GenericUnixCommand):
    def __init__(self, connection, prompt=None, newline_chars=None, runner=None, options="-BM -T -P"):
        super(Df, self).__init__(
            connection=connection,
            prompt=prompt,
            newline_chars=newline_chars,
            runner=runner,
        )
        self._options = options
        self._converter_helper = ConverterHelper()

    def build_command_string(self):
        cmd = f"df {self._options}" if self._options else "df"
        print(f"cmd: '{cmd}'")
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_filesystem_line(line)
            except ParsingDone:
                pass
        return super(Df, self).on_new_line(line, is_full_line)

    _re_filesystem_line = re.compile(
        r"^(?P<Filesystem>\S+)\s+(?P<Type>\S+)\s+(?P<Size>[\d\.]+)M?\s+(?P<Used>[\d\.]+)M?\s+"
        r"(?P<Avail>[\d\.]+)M?\s+(?P<Use_percentage>\d+)%\s+(?P<Mounted_on>\S+)$"
    )

    _re_filesystem_line_h = re.compile(
        r"^(?P<Filesystem>\S+)\s+(?P<Size>[\d\.]+[TGMK]?)\s+(?P<Used>[\d\.]+[TGMK]?)\s+"
        r"(?P<Avail>[\d\.]+[TGMK]?)\s+(?P<Use_percentage>\d+)%\s+(?P<Mounted_on>\S+)$"
    )

    def _parse_filesystem_line(self, line):
        if self._regex_helper.search_compiled(Df._re_filesystem_line, line) or \
          self._regex_helper.search_compiled(Df._re_filesystem_line_h, line):
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


COMMAND_OUTPUT = """df -BM -T -P
Filesystem    Type 1048576-blocks      Used Available Capacity Mounted on
/dev/sda2     ext3          4039M     1760M     2073M      46% /
udev         tmpfs           999M        1M      999M       1% /dev
/dev/sda3     ext3        144169M   109553M    27293M      81% /home
//175.28.247.174/emssim cifs      433150M     7865M   403282M       2% /home/emssim
//175.28.247.165/vobs cifs      918588M     1299M   916356M       1% /vobs
//175.28.247.165/vob cifs      918588M     1299M   916356M       1% /vob
//175.28.247.165/cc cifs      918588M     1299M   916356M       1% /cc
moler_bash#"""


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


COMMAND_KWARGS_TPM = {
    "options": "-T -P -m",
}


COMMAND_OUTPUT_TPM = """df -T -P -m
Filesystem     Type     1048576-blocks   Used Available Capacity Mounted on
none           overlay            7856      0      7856       0% /usr/lib/modules/6.6.114.1-microsoft-standard-WSL2
none           tmpfs              7856      1      7856       1% /mnt/wsl
drivers        9p               975581 657470    318112      68% /usr/lib/wsl/drivers
/dev/sdd       ext4            1031019  84523    894051       9% /
none           tmpfs              7856      1      7856       1% /mnt/wslg
none           overlay            7856      0      7856       0% /usr/lib/wsl/lib
rootfs         rootfs             7851      3      7848       1% /init
moler_bash#"""


COMMAND_RESULT_TPM = {
    "by_FS": {
        "drivers": {
            "Avail": "318112",
            "Used": "657470",
            "Type": "9p",
            "Size": "975581",
            "Filesystem": "drivers",
            "Mounted_on": "/usr/lib/wsl/drivers",
            "Use_percentage": "68",
        },
        "/dev/sdd": {
            "Avail": "894051",
            "Used": "84523",
            "Type": "ext4",
            "Size": "1031019",
            "Filesystem": "/dev/sdd",
            "Mounted_on": "/",
            "Use_percentage": "9",
        },
        "none": {
            "Avail": "7856",
            "Used": "0",
            "Type": "overlay",
            "Size": "7856",
            "Filesystem": "none",
            "Mounted_on": "/usr/lib/wsl/lib",
            "Use_percentage": "0",
        },
        "rootfs": {
            "Avail": "7848",
            "Used": "3",
            "Type": "rootfs",
            "Size": "7851",
            "Filesystem": "rootfs",
            "Mounted_on": "/init",
            "Use_percentage": "1",
        },
    },
    "by_MOUNTPOINT": {
        "/usr/lib/modules/6.6.114.1-microsoft-standard-WSL2": {
            "Avail": "7856",
            "Used": "0",
            "Type": "overlay",
            "Size": "7856",
            "Filesystem": "none",
            "Mounted_on": "/usr/lib/modules/6.6.114.1-microsoft-standard-WSL2",
            "Use_percentage": "0",
        },
        "/mnt/wsl": {
            "Avail": "7856",
            "Used": "1",
            "Type": "tmpfs",
            "Size": "7856",
            "Filesystem": "none",
            "Mounted_on": "/mnt/wsl",
            "Use_percentage": "1",
        },
        "/usr/lib/wsl/drivers": {
            "Avail": "318112",
            "Used": "657470",
            "Type": "9p",
            "Size": "975581",
            "Filesystem": "drivers",
            "Mounted_on": "/usr/lib/wsl/drivers",
            "Use_percentage": "68",
        },
        "/": {
            "Avail": "894051",
            "Used": "84523",
            "Type": "ext4",
            "Size": "1031019",
            "Filesystem": "/dev/sdd",
            "Mounted_on": "/",
            "Use_percentage": "9",
        },
        "/mnt/wslg": {
            "Avail": "7856",
            "Used": "1",
            "Type": "tmpfs",
            "Size": "7856",
            "Filesystem": "none",
            "Mounted_on": "/mnt/wslg",
            "Use_percentage": "1",
        },
        "/usr/lib/wsl/lib": {
            "Avail": "7856",
            "Used": "0",
            "Type": "overlay",
            "Size": "7856",
            "Filesystem": "none",
            "Mounted_on": "/usr/lib/wsl/lib",
            "Use_percentage": "0",
        },
        "/init": {
            "Avail": "7848",
            "Used": "3",
            "Type": "rootfs",
            "Size": "7851",
            "Filesystem": "rootfs",
            "Mounted_on": "/init",
            "Use_percentage": "1",
        },
    },
}


COMMAND_KWARGS_H = {
    "options": "-h",
}


COMMAND_OUTPUT_H = """df -h
Filesystem      Size  Used Avail Use% Mounted on
none            7.7G     0  7.7G   0% /usr/lib/modules/6.6.114.1-microsoft-standard-WSL2
none            7.7G  4.0K  7.7G   1% /mnt/wsl
drivers         953G  643G  311G  68% /usr/lib/wsl/drivers
/dev/sdd       1007G   83G  874G   9% /
none            7.7G   48K  7.7G   1% /mnt/wslg
none            7.7G     0  7.7G   0% /usr/lib/wsl/lib
rootfs          7.7G  2.8M  7.7G   1% /init
moler_bash#"""


COMMAND_RESULT_H = {
    "by_FS": {
        "drivers": {
            "Avail": "311G",
            "Used": "643G",
            "Size": "953G",
            "Filesystem": "drivers",
            "Mounted_on": "/usr/lib/wsl/drivers",
            "Use_percentage": "68",
        },
        "/dev/sdd": {
            "Avail": "874G",
            "Used": "83G",
            "Size": "1007G",
            "Filesystem": "/dev/sdd",
            "Mounted_on": "/",
            "Use_percentage": "9",
        },
        "none": {
            "Avail": "7.7G",
            "Used": "0",
            "Size": "7.7G",
            "Filesystem": "none",
            "Mounted_on": "/usr/lib/wsl/lib",
            "Use_percentage": "0",
        },
        "rootfs": {
            "Avail": "7.7G",
            "Used": "2.8M",
            "Size": "7.7G",
            "Filesystem": "rootfs",
            "Mounted_on": "/init",
            "Use_percentage": "1",
        },
    },
    "by_MOUNTPOINT": {
        "/usr/lib/modules/6.6.114.1-microsoft-standard-WSL2": {
            "Avail": "7.7G",
            "Used": "0",
            "Size": "7.7G",
            "Filesystem": "none",
            "Mounted_on": "/usr/lib/modules/6.6.114.1-microsoft-standard-WSL2",
            "Use_percentage": "0",
        },
        "/mnt/wsl": {
            "Avail": "7.7G",
            "Used": "4.0K",
            "Size": "7.7G",
            "Filesystem": "none",
            "Mounted_on": "/mnt/wsl",
            "Use_percentage": "1",
        },
        "/usr/lib/wsl/drivers": {
            "Avail": "311G",
            "Used": "643G",
            "Size": "953G",
            "Filesystem": "drivers",
            "Mounted_on": "/usr/lib/wsl/drivers",
            "Use_percentage": "68",
        },
        "/usr/lib/wsl/lib": {
            "Avail": "7.7G",
            "Used": "0",
            "Size": "7.7G",
            "Filesystem": "none",
            "Mounted_on": "/usr/lib/wsl/lib",
            "Use_percentage": "0",
        },
        "/": {
            "Avail": "874G",
            "Used": "83G",
            "Size": "1007G",
            "Filesystem": "/dev/sdd",
            "Mounted_on": "/",
            "Use_percentage": "9",
        },
        "/mnt/wslg": {
            "Avail": "7.7G",
            "Used": "48K",
            "Size": "7.7G",
            "Filesystem": "none",
            "Mounted_on": "/mnt/wslg",
            "Use_percentage": "1",
        },
        "/init": {
            "Avail": "7.7G",
            "Used": "2.8M",
            "Size": "7.7G",
            "Filesystem": "rootfs",
            "Mounted_on": "/init",
            "Use_percentage": "1",
        },
    },
}
