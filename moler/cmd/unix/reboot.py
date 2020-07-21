# -*- coding: utf-8 -*-
"""
Reboot command module.
"""
__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
import re


class Reboot(GenericUnixCommand):

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None):
        """
        :param connection: moler connection to device, terminal when command is executed
        :param prompt: Prompt of the starting shell
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(Reboot, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

    def build_command_string(self):
        """
        Builds command string.
        :return: String representation of command to send over connection to device.
        """
        return "reboot"

    def on_new_line(self, line, is_full_line):
        """
        Method to parse command output. Will be called after line with command echo.
        :param line: Line to parse, new lines are trimmed
        :param is_full_line:  False for chunk of line; True on full line (NOTE: new line character removed)
        :return: None
        """
        if is_full_line:
            self._catch_connection_closed(line)
        else:
            self._catch_login_prompt(line)

    _re_connection_closed = re.compile(r"(?P<CLOSED>(Connection\s+to\s+\S+\s+closed.*)|"
                                       r"(Connection closed by .* host.*))", re.I)

    def _catch_connection_closed(self, line):
        if self._regex_helper.search_compiled(Reboot._re_connection_closed, line):
            self.set_result({'RESULT': self._regex_helper.group('CLOSED')})

    _re_login_prompt = re.compile(r"(?P<LOGIN_PROMPT>.*?login:\s+)", re.I)

    def _catch_login_prompt(self, line):
        if self._regex_helper.search_compiled(Reboot._re_login_prompt, line):
            self.set_result({'RESULT': self._regex_helper.group('LOGIN_PROMPT')})


COMMAND_OUTPUT_SSH = """
toor4nsn@fzhub:~# reboot
Connection to 192.168.255.129 closed by remote host.

Connection to 192.168.255.129 closed.
"""

COMMAND_KWARGS_SSH = {}

COMMAND_RESULT_SSH = {
    'RESULT': 'Connection to 192.168.255.129 closed by remote host.'
}

COMMAND_OUTPUT_TELNET = """
root@HUB_WS:~# reboot
Connection closed by foreign host.

ute@SC5G-HUB-079"""

COMMAND_KWARGS_TELNET = {}

COMMAND_RESULT_TELNET = {
    'RESULT': 'Connection closed by foreign host.'
}

COMMAND_OUTPUT_CONSOLE = """
toor4nsn@fzhub:~# reboot
Poky (Yocto Project Reference Distro) 2.2.2 fzhub ttyPS0

fzhub login: """

COMMAND_KWARGS_CONSOLE = {}

COMMAND_RESULT_CONSOLE = {
    'RESULT': 'fzhub login: '
}

COMMAND_OUTPUT_reboot = """reboot
Connection to 192.168.255.179 closed by remote host.
"""

COMMAND_KWARGS_reboot = {}

COMMAND_RESULT_reboot = {
    'RESULT': 'Connection to 192.168.255.179 closed by remote host.'
}
