# -*- coding: utf-8 -*-
"""
id command module.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone


class Id(GenericUnixCommand):

    def __init__(self, connection, user=None, prompt=None, newline_chars=None, runner=None):
        super(Id, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self.user = user

    def build_command_string(self):
        cmd = "id"
        if self.user:
            cmd = "{} {}".format(cmd, self.user)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._parse_uid_gid_groups(line)
            except ParsingDone:
                pass  # line has been fully parsed by one of above parse-methods
        return super(Id, self).on_new_line(line, is_full_line)

    # uid=1000(user) gid=1000(user) groups=1000(user),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),
    # 108(netdev),110(lpadmin),113(scanner),118(bluetooth)
    _re_uid_gid_groups = re.compile(r"uid=(?P<UID>\S+)\s+gid=(?P<GID>\S+)\s+groups=(?P<GROUPS>\S+)")
    _ret_dict_key = ['UID', 'GID', 'GROUPS']

    def _parse_uid_gid_groups(self, line):
        return self._process_line_uid_gid_groups(line, Id._re_uid_gid_groups)

    def _process_line_uid_gid_groups(self, line, regexp):
        if self._regex_helper.search_compiled(regexp, line):
            self._parse_single_group()

            raise ParsingDone

    def _parse_single_group(self, ):
        _re_id_name = re.compile(r"((\d+?)\((\S+?)\)\,?)")

        for key in Id._ret_dict_key:
            self.current_ret[key] = []

            _id_name_values = self._regex_helper.group(key)
            _id_name_list = re.findall(_re_id_name, _id_name_values)

            self._add_single_entry_to_ret_dict(_id_name_list, key)

    def _add_single_entry_to_ret_dict(self, _id_name_list, key):
        for _id_name_entry in _id_name_list:
            self.current_ret[key].append(
                {
                    "ID": int(_id_name_entry[1]),
                    "NAME": _id_name_entry[2]
                }
            )


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
# Parameters:
# user is Optional.User for Unix id command
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_ver_execute = """
host:~ # id user
uid=1000(user) gid=1000(user) groups=1000(user),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),108(netdev),110(lpadmin),113(scanner),118(bluetooth)
host:~ #
"""

COMMAND_KWARGS_ver_execute = {'user': 'user'}

COMMAND_RESULT_ver_execute = {
    'UID': [
        {
            'ID': 1000,
            'NAME': 'user'
        },
    ],
    'GID': [
        {
            'ID': 1000,
            'NAME': 'user'
        }
    ],
    'GROUPS': [
        {
            'ID': 1000,
            'NAME': 'user'
        },
        {
            'ID': 24,
            'NAME': 'cdrom'
        },
        {
            'ID': 25,
            'NAME': 'floppy'
        },
        {
            'ID': 29,
            'NAME': 'audio'
        },
        {
            'ID': 30,
            'NAME': 'dip'
        },
        {
            'ID': 44,
            'NAME': 'video'
        },
        {
            'ID': 46,
            'NAME': 'plugdev'
        },
        {
            'ID': 108,
            'NAME': 'netdev'
        },
        {
            'ID': 110,
            'NAME': 'lpadmin'
        },
        {
            'ID': 113,
            'NAME': 'scanner'
        },
        {
            'ID': 118,
            'NAME': 'bluetooth'
        }
    ]
}
