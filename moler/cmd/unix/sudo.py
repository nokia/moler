# -*- coding: utf-8 -*-
"""
Sudo command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
import importlib
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Sudo(GenericUnixCommand):

    def __init__(self, connection, sudo_password, cmd_object=None, cmd_class_name=None, cmd_params=None, prompt=None,
                 newline_chars=None, runner=None):
        super(Sudo, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.sudo_password = sudo_password
        self.cmd_object = cmd_object
        self._sent_sudo_password = False
        self._sent_command_string = False
        self.newline_seq = "\r\n"
        if cmd_class_name:
            params = dict()
            if cmd_params is not None:
                params = cmd_params.copy()
            params["connection"] = connection
            params['prompt'] = prompt
            params["newline_chars"] = newline_chars
            self.cmd_object = self._create_object_from_name(cmd_class_name, params)
        if not self.cmd_object:
            self.set_exception(CommandFailure(
                "Neither 'cmd_class_name' nor 'cmd_object' was provided to Sudo constructor. Please specific parameter."))

    def build_command_string(self):
        cmd = "sudo {}".format(self.cmd_object.command_string)
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            self._parse_sudo_password(line)
            self._parse_command_not_found(line)
            self._process_embedded_command(line, is_full_line)
        except ParsingDone:
            pass
        super(Sudo, self).on_new_line(line, is_full_line)

    def _process_embedded_command(self, line, is_full_line):
        if not self._sent_command_string:
            self._sent_command_string = True
            cs = "{}{}".format(self.cmd_object.command_string, self.newline_seq)
            self.cmd_object.data_received(cs)
        if is_full_line:
            line = "{}{}".format(line, self.newline_seq)
        self.cmd_object.data_received(line)
        self.current_ret["cmd_ret"] = self.cmd_object.current_ret

    _re_sudo_command_not_found = re.compile(r"sudo:.*command not found", re.I)

    def _create_object_from_name(self, full_class_name, constructor_params):
        name_splitted = full_class_name.split('.')
        module_name = ".".join(name_splitted[:-1])
        class_name = name_splitted[-1]

        imported_module = importlib.import_module(module_name)
        class_imported = getattr(imported_module, class_name)
        obj = class_imported(constructor_params)
        return obj

    def _parse_command_not_found(self, line):
        if re.search(Sudo._re_sudo_command_not_found, line):
            self.set_exception(CommandFailure(self, "Command not found in line '{}'".format(line)))
            raise ParsingDone()

    _re_sudo_password = re.compile(r"\[sudo\] password for.*:", re.I)

    def _parse_sudo_password(self, line):
        if re.search(Sudo._re_sudo_password, line):
            if not self._sent_sudo_password:
                self.connection.sendline(self.sudo_password)
                self._sent_sudo_password = True
            raise ParsingDone()


COMMAND_OUTPUT_whoami = """
user@client:~/moler$ sudo whoami
[sudo] password for user:
root
user@client:~/moler$ """

COMMAND_RESULT_whoami = {
    "cmd_ret": {"USER": "root"}
}

COMMAND_KWARGS_whoami = {
    "cmd_class_name": "moler.cmd.unix.whoami.Whoami",
    "sudo_password": "pass",
}

COMMAND_OUTPUT_ls = """
user@client:~/moler$ sudo ls -l
[sudo] password for user:
total 8
drwxr-xr-x  2 root root    4096 Sep 25  2014 bin
drwxr-xr-x  5 root root    4096 Mar 20  2015 btslog2
-rw-r--r--  1 root root      51 Dec 15 10:48 getfzmip.txt
-rw-r--r--  1 root root      24 Dec 15 10:48 getfzmip.txt-old.20171215-104858.txt
lrwxrwxrwx  1 root root       4 Mar 20  2015 bcn -> /bcn
lrwxrwxrwx  1 root root      10 Mar 20  2015 logsremote -> /mnt/logs/
user@client:~/moler$ """

COMMAND_RESULT_ls = {
    "cmd_ret": {
        "total": {
            "raw": "8",
            "bytes": 8,
        },

        "files": {
            "bin": {"permissions": "drwxr-xr-x", "hard_links_count": 2, "owner": "root", "group": "root",
                    "size_bytes": 4096, "size_raw": "4096", "date": "Sep 25  2014", "name": "bin", },
            "btslog2": {"permissions": "drwxr-xr-x", "hard_links_count": 5, "owner": "root", "group": "root",
                        "size_bytes": 4096, "size_raw": "4096", "date": "Mar 20  2015", "name": "btslog2", },
            "getfzmip.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1, "owner": "root", "group": "root",
                             "size_bytes": 51, "size_raw": "51", "date": "Dec 15 10:48", "name": "getfzmip.txt", },
            "getfzmip.txt-old.20171215-104858.txt": {"permissions": "-rw-r--r--", "hard_links_count": 1,
                                                     "owner": "root",
                                                     "group": "root", "size_bytes": 24, "size_raw": "24",
                                                     "date": "Dec 15 10:48",
                                                     "name": "getfzmip.txt-old.20171215-104858.txt", },
            "bcn": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root",
                    "size_bytes": 4,
                    "size_raw": "4", "date": "Mar 20  2015", "name": "bcn", "link": "/bcn"},
            "logsremote": {"permissions": "lrwxrwxrwx", "hard_links_count": 1, "owner": "root", "group": "root",
                           "size_bytes": 10, "size_raw": "10", "date": "Mar 20  2015", "name": "logsremote",
                           "link": "/mnt/logs/"},
        },
    },
}

COMMAND_KWARGS_ls = {
    "cmd_class_name": "moler.cmd.unix.ls.Ls",
    "cmd_params": {"options": "-l"},
    "sudo_password": "pass",
}
