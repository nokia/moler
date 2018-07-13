# -*- coding: utf-8 -*-
"""
Ls command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.cmd.converterhelper import ConverterHelper
from moler.exceptions import WrongUsage

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Ls(GenericUnix):

    _re_files_list = re.compile(r"\S{2,}")
    _re_total = re.compile(r"total\s+(\d+\S*)")
    _re_long = re.compile(r"([\w-]{10})\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S.*\S)\s+(\S+)\s*$")
    _re_long_links = re.compile(r"([\w-]{10})\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S.*\S)\s+(\S+)\s+->\s+(\S+)\s*$")

    def __init__(self, connection, prompt=None, new_line_chars=None, options=None):
        super(Ls, self).__init__(connection, prompt, new_line_chars)
        self._converter_helper = ConverterHelper()
        # Parameters defined by calling the command
        self.options = options
        self.matched = 0

    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = "ls"
            if self.options:
                cmd = cmd + " " + self.options
        return cmd

    def on_new_line(self, line, is_full_line):
        if not is_full_line:
            return super(Ls, self).on_new_line(line, is_full_line)
        if self._regex_helper.search_compiled(Ls._re_total, line):
            if "total" not in self.current_ret:
                self.current_ret["total"] = dict()
            self.current_ret["total"]["raw"] = self._regex_helper.group(1)
            self.current_ret["total"]["bytes"] = self._converter_helper.to_bytes(self._regex_helper.group(1))[0]
        elif self._regex_helper.search_compiled(Ls._re_long_links, line):
            self._add_new_file_long(True)
        elif self._regex_helper.search_compiled(Ls._re_long, line):
            self._add_new_file_long(False)
        elif self._regex_helper.search_compiled(Ls._re_files_list, line):
            files = line.split()
            if "files" not in self.current_ret:
                self.current_ret["files"] = dict()
            for filename in files:
                self.current_ret["files"][filename] = dict()
                self.current_ret["files"][filename]["name"] = filename
        return super(Ls, self).on_new_line(line, is_full_line)

    def _add_new_file_long(self, islink):
        filename = self._regex_helper.group(7)
        if "files" not in self.current_ret:
            self.current_ret["files"] = dict()
        self.current_ret["files"][filename] = dict()
        self.current_ret["files"][filename]["permissions"] = self._regex_helper.group(1)
        self.current_ret["files"][filename]["hard_links_count"] = int(self._regex_helper.group(2))
        self.current_ret["files"][filename]["owner"] = self._regex_helper.group(3)
        self.current_ret["files"][filename]["group"] = self._regex_helper.group(4)
        self.current_ret["files"][filename]["size_raw"] = self._regex_helper.group(5)
        self.current_ret["files"][filename]["size_bytes"] = self._converter_helper.to_bytes(self._regex_helper.group(5))[0]
        self.current_ret["files"][filename]["date"] = self._regex_helper.group(6)
        self.current_ret["files"][filename]["name"] = self._regex_helper.group(7)
        if islink:
            self.current_ret["files"][filename]["link"] = self._regex_helper.group(8)

    def _get_types(self, requested_type):
        if not self.done():
            raise WrongUsage("Command not executed already")
        requested_type = requested_type.lower()
        ret = dict()
        result = self.result()
        if 'files' in result:
            for file_name in result["files"]:
                file_dict = result["files"][file_name]
                permissions = file_dict["permissions"]
                current_type = permissions[0]
                if requested_type == current_type:
                    ret[file_name] = file_dict
        return ret

    def get_dirs(self):
        return self._get_types('d')

    def get_links(self):
        return self._get_types('l')

    def get_files(self):
        return self._get_types('-')


COMMAND_OUTPUT_ver_human = """
FZM-TDD-249:~ # ls -lh
total 1T
-rwxr-xr-x 2 root  root  4.0K Nov 10  2016 file1
-rwxr-xr-x 2 root  root  4.5M Nov 10  2016 file2
-rwxr-xr-x 2 root  root  3.0G Nov 10  2016 file3
-rwxr-xr-x 2 root  root  1.0T Nov 10  2016 file4
-rwxr-xr-x 2 root  root    92 Nov 10  2016 file5
FZM-TDD-249:~ #"""


COMMAND_KWARGS_ver_human = {"options": "-lh"}

COMMAND_RESULT_ver_human = {
"total": {
    "raw": "1T",
    "bytes": 1099511627776
},
"files": {
                "file1": {"permissions": "-rwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root", "size_bytes": 4096, "size_raw": "4.0K", "date": "Nov 10  2016", "name": "file1", },
                "file2": {"permissions": "-rwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root", "size_bytes": 4718592, "size_raw": "4.5M", "date": "Nov 10  2016", "name": "file2", },
                "file3": {"permissions": "-rwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root", "size_bytes": 3221225472, "size_raw": "3.0G", "date": "Nov 10  2016", "name": "file3", },
                "file4": {"permissions": "-rwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root", "size_bytes": 1099511627776, "size_raw": "1.0T", "date": "Nov 10  2016", "name": "file4", },
                "file5": {"permissions": "-rwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root", "size_bytes": 92, "size_raw": "92", "date": "Nov 10  2016", "name": "file5", },
            },
}

COMMAND_OUTPUT_ver_long = """
FZM-TDD-249:~ # ls -l
total 8
drwxr-xr-x  2 root root    4096 Sep 25  2014 bin
drwxr-xr-x  5 root root    4096 Mar 20  2015 btslog2
-rw-r--r--  1 root root      51 Dec 15 10:48 getfzmip.txt
-rw-r--r--  1 root root      24 Dec 15 10:48 getfzmip.txt-old.20171215-104858.txt
lrwxrwxrwx  1 root root       4 Mar 20  2015 bcn -> /bcn
lrwxrwxrwx  1 root root      10 Mar 20  2015 logsremote -> /mnt/logs/
FZM-TDD-249:~ #
"""

COMMAND_KWARGS_ver_long = {"options": "-l"}

COMMAND_RESULT_ver_long = {

"total": {
            "raw": "8",
            "bytes": 8,
},

"files": {
            "bin": {"permissions": "drwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root", "size_bytes": 4096, "size_raw": "4096", "date": "Sep 25  2014", "name": "bin", },
            "btslog2": {"permissions": "drwxr-xr-x", "hard_links_count": 5, "owner": "root", "group": "root", "size_bytes": 4096, "size_raw": "4096", "date": "Mar 20  2015", "name": "btslog2", },
            "getfzmip.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1, "owner": "root", "group": "root", "size_bytes":51, "size_raw": "51", "date": "Dec 15 10:48", "name": "getfzmip.txt", },
            "getfzmip.txt-old.20171215-104858.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1, "owner": "root", "group": "root", "size_bytes": 24, "size_raw": "24", "date": "Dec 15 10:48", "name": "getfzmip.txt-old.20171215-104858.txt", },
            "bcn": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root", "size_bytes": 4, "size_raw": "4", "date": "Mar 20  2015", "name": "bcn", "link": "/bcn"},
            "logsremote": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root", "size_bytes":10, "size_raw": "10", "date": "Mar 20  2015", "name": "logsremote", "link": "/mnt/logs/"},
    },
}


COMMAND_OUTPUT_ver_plain = """
FZM-TDD-249:~ # ls
.ansible               dot1ag-13.2.tgz                       .kde4
.bash_history          Downloads
FZM-TDD-249:~ #
"""

COMMAND_KWARGS_ver_plain = {}

COMMAND_RESULT_ver_plain = {
            "files": {
                ".ansible": {"name": ".ansible"},
                "dot1ag-13.2.tgz": {"name": "dot1ag-13.2.tgz"},
                ".kde4": {"name": ".kde4"},
                ".bash_history": {"name": ".bash_history"},
                "Downloads": {"name": "Downloads"},
            },
}
