# -*- coding: utf-8 -*-
"""
AT+GTCELLLOCK=<mode>[,<rat>,<type>,<earfcn>[,<PCI>][,<scs>][,<nrband>]]

AT commands specification:
https://drive.google.com/file/d/1hnt_gnJT55Fr-aR4IhOX4HKuuLxWwhd_/view?pli=1
(always check against the latest vendor release notes)
"""

__author__ = 'Piotr Wojdan, Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'piotr.wojdan@nokia.com, marcin.usielski@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand
from moler.helpers import convert_to_int


class GtCellLock(GenericAtCommand):
    """
    Command to lock/unlock cell PCI/frequency for Qualcomm X55 chips. Example outputs:

    AT+GTCELLLOCK=1,1,0,649920,312,1,5078
    OK
    AT+GTCELLLOCK=1,0,0,649920,312,0,7
    OK
    """

    def __init__(self, enable, net_mode, earfcn=0, pci=0, scs=0, band=0, lock_pci=0,
                 connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Command to lock/unlock cell PCI/frequency for Qualcomm X55 chips.

        :param enable: 1 - lock, 0 - unlock
        :param net_mode: NR5G/LTE
        :param earfcn: earfcn number
        :param pci: pci number
        :param scs: 15/30kHz
        :param band: nr band number
        :param lock_pci: 0 - lock PCI, 1 - lock frequency
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(GtCellLock, self).__init__(connection, operation="execute", prompt=prompt,
                                         newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.enable = enable
        self.net_mode = convert_to_int(net_mode, none_if_cannot_convert=True)
        if self.net_mode is None:
            self.net_mode = 1 if net_mode.lower() in ['nr', '5g'] else 0
        self.earfcn = earfcn
        self.pci = pci
        self.scs = 0 if scs == 15 else 1
        self.band = band
        self.lock_pci = lock_pci

    def build_command_string(self):
        command_prefix = 'AT+GTCELLLOCK='
        command = (f'{command_prefix}{self.enable},{self.net_mode},{self.lock_pci},{self.earfcn},'
                   f'{self.pci},{self.scs},{self.band}') if self.enable else f'{command_prefix}{self.enable}'
        return command


# -----------------------------------------------------------------------------
# Following documentation is required for library CI.
# It is used to perform command self-test.
#
# Moreover, it documents what will be COMMAND_RESULT when command
# is run with COMMAND_KWARGS on COMMAND_OUTPUT data coming from connection.
#
# When you need to show parsing of multiple outputs just add suffixes:
# COMMAND_OUTPUT_suffix
# COMMAND_KWARGS_suffix
# COMMAND_RESULT_suffix
# -----------------------------------------------------------------------------

COMMAND_OUTPUT_option = """
AT+GTCELLLOCK=1,1,0,649920,312,1,5078
OK
"""

COMMAND_KWARGS_option = {"enable": 1,
                         "net_mode": 'nr',
                         "lock_pci": 0,
                         "earfcn": 649920,
                         "pci": 312,
                         "scs": 1,
                         "band": 5078}

COMMAND_RESULT_option = {}


COMMAND_OUTPUT_option_net_mode_nr = """
AT+GTCELLLOCK=1,1,0,649920,312,1,5078
OK
"""

COMMAND_KWARGS_option_net_mode_nr = {"enable": 1,
                                     "net_mode": 1,
                                     "lock_pci": 0,
                                     "earfcn": 649920,
                                     "pci": 312,
                                     "scs": 1,
                                     "band": 5078}

COMMAND_RESULT_option_net_mode_nr = {}
