# -*- coding: utf-8 -*-
"""
id command module.
"""
from re import compile, escape, IGNORECASE

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'


class Id(GenericUnix):

    def __init__(self, connection, user=None, prompt=None, new_line_chars=None):
        super(Id, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.user = user

    def build_command_string(self):
        cmd = "id"
        if self.user:
            cmd = "{} {}".format(cmd, self.user)
        return cmd

    def on_new_line(self, line, is_full_line):
        if not is_full_line:
            return super(Id, self).on_new_line(line, is_full_line)

        return super(Id, self).on_new_line(line, is_full_line)


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# Parameters:
# user is Optional.Path for Unix id command
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_execute = """
host:~ # id user
uid=1000(user) gid=1000(user) groups=1000(user),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),108(netdev),110(lpadmin),113(scanner),118(bluetooth)
host:~ #
"""

COMMAND_KWARGS_ver_execute = {'user': 'user'}

COMMAND_RESULT_ver_execute = {
}
