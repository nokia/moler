# -*- coding: utf-8 -*-
"""
AT+QNWPREFCFG="{config_option}",(option_value)[:(option_value)]

AT commands specification:
google for: Quectel RG50xQRM5xxQ (R11 release and later)
This is internal Quectel AT command
(always check against the latest vendor release notes)
"""

__author__ = 'Piotr Wojdan'
__copyright__ = 'Copyright (C) 2023, Nokia'
__email__ = 'piotr.wojdan@nokia.com'

from moler.cmd.at.genericat import GenericAtCommand


class QuectelNetworkPreferences(GenericAtCommand):
    """
    Command to set configuration for network searching preferences. Example outputs:

    AT+QNWPREFCFG= "mode_pref",LTE
    OK
    AT+QNWPREFCFG= "mode_pref",LTE:NR5G
    OK
    """
    def __init__(self, config_option, option_value, connection=None, prompt=None, newline_chars=None, runner=None):
        """
        Quectel UE set parameter in configuration for network searching preferences.

        :param config_option: parameter name to be set
        :param option_value: value to be set
        :param connection: Moler connection to device, terminal when command is executed.
        :param prompt: prompt where we start from.
        :param newline_chars: Characters to split local lines - list.
        :param runner: Runner to run command.
        """
        super(QuectelNetworkPreferences, self).__init__(connection, operation="execute", prompt=prompt,
                                                        newline_chars=newline_chars, runner=runner)
        self.ret_required = False
        self.config_option = config_option
        self.option_value = option_value

    def build_command_string(self):
        command_prefix = 'AT+QNWPREFCFG='
        return f'{command_prefix}"{self.config_option}",{self.option_value}'


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
AT+QNWPREFCFG="nr5g_band",66
OK
"""

COMMAND_KWARGS_option = {'config_option': 'nr5g_band', 'option_value': '66'}

COMMAND_RESULT_option = {}
