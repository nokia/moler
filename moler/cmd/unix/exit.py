# -*- coding: utf-8 -*-
"""
Exit command module.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

from moler.cmd.unix.genericunix import GenericUnix
from moler.textualgeneric import TextualGeneric
from moler.exceptions import ParsingDone


class Exit(GenericUnix):
    def __init__(self, connection, prompt=None, new_line_chars=None):
        super(Exit, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)
        self.ret_required = False

    def build_command_string(self):
        cmd = "exit"
        return cmd


COMMAND_OUTPUT = """
amu012@belvedere07:~$ exit
bash-4.2:~ #"""

COMMAND_KWARGS = {
}

COMMAND_RESULT = {}
