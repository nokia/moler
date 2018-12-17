# -*- coding: utf-8 -*-
"""
Sudo command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.helpers import create_object_from_name
from moler.helpers import copy_dict


class Sudo(GenericUnixCommand):

    def __init__(self, connection, sudo_password, cmd_object=None, cmd_class_name=None, cmd_params=None, prompt=None,
                 newline_chars=None, runner=None):
        """
        :param connection: moler connection to device, terminal when command is executed
        :param sudo_password: password
        :param cmd_object: object of command. Pass this object or cmd_class_name.
        :param cmd_class_name: full (with package) class name. Pass this name or cmd_object.
        :param cmd_params: params for cmd_class_name. If cmd_object is passed this parameter is ignored.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        """
        super(Sudo, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.sudo_password = sudo_password
        self.cmd_object = cmd_object
        self._sent_sudo_password = False
        self._sent_command_string = False
        self.newline_seq = "\n"
        if cmd_object and cmd_class_name:
            self.set_exception(CommandFailure(self, "both 'cmd_object' and 'cmd_class_name' parameters provided. Please specify only one. "))
            return

        if cmd_class_name:
            params = copy_dict(cmd_params)
            params["connection"] = connection
            params['prompt'] = prompt
            params["newline_chars"] = newline_chars
            try:
                self.cmd_object = create_object_from_name(cmd_class_name, params)
            except Exception as ex:
                self.set_exception(ex)
        else:
            if not self.cmd_object:
                self.set_exception(CommandFailure(self,
                                                  "Neither 'cmd_class_name' nor 'cmd_object' was provided to Sudo constructor. Please specific parameter."))

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "sudo"
        if self.cmd_object:
            cmd = "sudo {}".format(self.cmd_object.command_string)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: Nothing.
        """
        try:
            self._parse_sudo_password(line)
            self._parse_command_not_found(line)
            self._process_embedded_command(line, is_full_line)
        except ParsingDone:
            pass
        super(Sudo, self).on_new_line(line, is_full_line)

    def _process_embedded_command(self, line, is_full_line):
        """
        Processes embedded command, passes output from device to embedded command.
        :param line: Line from device
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: Nothing but raises ParsingDone if sudo has embedded command object.
        """
        if self.cmd_object:
            if not self._sent_command_string:
                self._sent_command_string = True
                cs = "{}{}".format(self.cmd_object.command_string, self.newline_seq)
                self.cmd_object.data_received(cs)
            if is_full_line:
                line = "{}{}".format(line, self.newline_seq)
            self.cmd_object.data_received(line)
            self.current_ret["cmd_ret"] = self.cmd_object.current_ret
            if self.cmd_object.done():
                try:
                    self.cmd_object.result()
                except Exception as ex:
                    self.set_exception(ex)
            raise ParsingDone()

    _re_sudo_command_not_found = re.compile(r"sudo:.*command not found", re.I)

    def _parse_command_not_found(self, line):
        """
        Parses if command not found is found in line.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if re.search(Sudo._re_sudo_command_not_found, line):
            self.set_exception(CommandFailure(self, "Command not found in line '{}'".format(line)))
            raise ParsingDone()

    _re_sudo_password = re.compile(r"\[sudo\] password for.*:", re.I)

    def _parse_sudo_password(self, line):
        """
        Parses if sudo waits for password.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
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
