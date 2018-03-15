# -*- coding: utf-8 -*-
"""
Ls command module.
"""
from re import compile

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Ls(GenericUnix):

    _reg_new_line = compile(r"\n$")
    _reg_files_list = compile(r"\S{2,}")
    _reg_total = compile(r"total\s\d+")
    _reg_permissions = compile(r"^[\w-]{10}\s+")
    _reg_links = compile(r"(\S+)\s+\-\>\s+(\S+)")
    _reg_long = compile(r"[\w-]{10}\s+\S+\s+\S+\s+\S+\s+(\S+).*\s+(\S+)\s*$")

    def __init__(self, connection, opt=None):
        super(Ls, self).__init__(connection)

        # Parameters defined by calling the command
        self.opt = opt
        self.matched = 0

    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = "ls"
            if self.opt:
                cmd = cmd + " " + self.opt
        return cmd

    def on_new_line(self, line):
        if not self._cmd_matched or not self._regex_helper.search_compiled(Ls._reg_new_line, line):
            return super(Ls, self).on_new_line(line)
        if self._regex_helper.search_compiled(Ls._reg_links, line):
            if "-LINKS" not in self.ret:
                self.ret["-LINKS"] = dict()
            self.ret["-LINKS"][self._regex_helper.group(1)] = self._regex_helper.group(2)
        elif self._regex_helper.search_compiled(Ls._reg_long, line):
            filename = self._regex_helper.group(2)
            if "files" not in self.ret:
                self.ret["files"] = list()
            self.ret["files"].append(filename)
            if "-SIZE" not in self.ret:
                self.ret["-SIZE"] = dict()
            self.ret["-SIZE"][filename] = self._regex_helper.group(1)
        elif self._regex_helper.search_compiled(Ls._reg_files_list, line) and not self._regex_helper.search_compiled(Ls._reg_total, line) and not self._regex_helper.search_compiled(Ls._reg_permissions, line):
            files = line.split()
            if "files" in self.ret:
                self.ret["files"].extend(files)
            else:
                self.ret["files"] = list(files)

        return super(Ls, self).on_new_line(line)


COMMAND_OUTPUT_ver_long = """
FZM-TDD-249:~ # ls -l
drwxr-xr-x  2 root root    4096 Sep 25  2014 bin
drwxr-xr-x  5 root root    4096 Mar 20  2015 btslog2
-rw-r--r--  1 root root      51 Dec 15 10:48 getfzmip.txt
-rw-r--r--  1 root root      24 Dec 15 10:48 getfzmip.txt-old.20171215-104858.txt 
lrwxrwxrwx  1 root root       4 Mar 20  2015 bcn -> /bcn
lrwxrwxrwx  1 root root      10 Mar 20  2015 logsremote -> /mnt/logs/
FZM-TDD-249:~ #"""

COMMAND_KWARGS_ver_long = {"opt": "-l"}

COMMAND_RESULT_ver_long = {
            "-LINKS": {
                "bcn": "/bcn",
                "logsremote": "/mnt/logs/"
            },
            "-SIZE": {
                "bin": "4096",
                "btslog2": "4096",
                "getfzmip.txt": "51",
                "getfzmip.txt-old.20171215-104858.txt": "24"
            },
            "files": ["bin", "btslog2", "getfzmip.txt", "getfzmip.txt-old.20171215-104858.txt"]
}


COMMAND_OUTPUT_ver_plain = """
FZM-TDD-249:~ # ls
.ansible               dot1ag-13.2.tgz                       .kde4             .skel
.bash_history          Downloads
FZM-TDD-249:~ #"""

COMMAND_KWARGS_ver_plain = {}

COMMAND_RESULT_ver_plain = {
            "files": [".ansible", "dot1ag-13.2.tgz", ".kde4", ".skel", ".bash_history", "Downloads"]
}
