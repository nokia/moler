# -*- coding: utf-8 -*-
"""
SCPI command idn module.
"""


from moler.cmd.scpi.scpi.genericscpi import GenericScpi

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Idn(GenericScpi):

    def build_command_string(self):
        return "*idn?"


COMMAND_OUTPUT = """*idn?
Agilent Technologies,N9020A,MY53420262,A.13.15
SCPI>"""

COMMAND_KWARGS = {}

COMMAND_RESULT = {
    'RAW_OUTPUT': ['Agilent Technologies,N9020A,MY53420262,A.13.15']
}
