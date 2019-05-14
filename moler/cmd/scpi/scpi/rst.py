# -*- coding: utf-8 -*-
"""
SCPI command RST module.
"""


from moler.cmd.scpi.scpi.genricscpinooutput import GenericScpiNoOutput

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Rst(GenericScpiNoOutput):

    def build_command_string(self):
        return "*RST"


COMMAND_OUTPUT = """*RST
SCPI>"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {}
