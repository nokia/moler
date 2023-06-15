# -*- coding: utf-8 -*-
"""
Telnet command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.generictelnetssh import GenericTelnetSsh
from moler.exceptions import ParsingDone
from moler.helpers import copy_list
from dateutil import parser


class Telnet(GenericTelnetSsh):

    def __init__(self, connection, host, login=None, password=None, port=0, prompt=None, expected_prompt=r'^>\s*',
                 set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None, term_mono="TERM=xterm-mono", prefix=None,
                 newline_chars=None, cmds_before_establish_connection=None, cmds_after_establish_connection=None,
                 telnet_prompt=r"^\s*telnet>\s*", encrypt_password=True, runner=None, target_newline="\n",
                 allowed_newline_after_prompt=False, repeat_password=True, failure_exceptions_indication=None,
                 prompt_after_login=None, send_enter_after_connection=True, username=None):
        """
        Moler class of Unix command telnet.

        :param connection: moler connection to device, terminal when command is executed.
        :param host: address of telnet server.
        :param login: login to telnet server.
        :param password: password to telnet server.
        :param port: port to listen on server.
        :param prompt: prompt on start system (where command telnet starts).
        :param expected_prompt: prompt on server (where command telnet connects).
        :param set_timeout: Command to set timeout after telnet connects.
        :param set_prompt: Command to set prompt after telnet connects.
        :param term_mono: Params to set ssh mono connection (useful in script).
        :param prefix: prefix telnet command.
        :param newline_chars: characters to split lines.
        :param cmds_before_establish_connection: list of commands to execute by telnet command before open.
        :param cmds_after_establish_connection: list of commands to execute by telnet commands after establishing.
        :param telnet_prompt: prompt for telnet commands.
        :param encrypt_password: If True then * will be in logs when password is sent, otherwise plain text.
        :param runner: Runner to run command.
        :param target_newline: newline chars on remote system where ssh connects.
        :param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt.
        :param repeat_password: If True then repeat last password if no more provided. If False then exception is set.
        :param failure_exceptions_indication: String with regex or regex object to omit failure even if failed string
         was found.
        :param prompt_after_login: prompt after login before send export PS1. If you do not change prompt exporting PS1
         then leave it None.
        :param send_enter_after_connection: set True to send new line char(s) after connection is established, False
         otherwise.
        :param username: login for ssh. Set this or login but not both.
        """
        super(Telnet, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner,
                                     port=port, host=host, login=login, password=password,
                                     expected_prompt=expected_prompt, set_timeout=set_timeout, set_prompt=set_prompt,
                                     term_mono=term_mono, encrypt_password=encrypt_password,
                                     target_newline=target_newline,
                                     allowed_newline_after_prompt=allowed_newline_after_prompt,
                                     repeat_password=repeat_password,
                                     failure_exceptions_indication=failure_exceptions_indication,
                                     prompt_after_login=prompt_after_login,
                                     send_enter_after_connection=send_enter_after_connection,
                                     username=username
                                     )

        self.prefix = prefix
        # Parameters defined by calling the command
        self._re_telnet_prompt = Telnet._calculate_prompt(telnet_prompt)  # Prompt for telnet commands

        self.cmds_before_establish_connection = copy_list(cmds_before_establish_connection)
        self.cmds_after_establish_connection = copy_list(cmds_after_establish_connection)

        # Internal variables
        self._telnet_command_mode = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = ""
        if self.term_mono:
            cmd = "{} ".format(self.term_mono)
        cmd = "{}telnet".format(cmd)
        if self.prefix:
            cmd = "{} {}".format(cmd, self.prefix)
        host_port_cmd = self.host
        if self.port:
            host_port_cmd = "{} {}".format(host_port_cmd, self.port)
        if 0 == len(self.cmds_before_establish_connection):
            cmd = "{} {}".format(cmd, host_port_cmd)
        else:
            self.cmds_before_establish_connection.append("open {}".format(host_port_cmd))
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._send_commands_before_establish_connection_if_requested(line, is_full_line)
            self._send_commands_after_establish_connection_if_requested(line, is_full_line)
        except ParsingDone:
            pass
        super(Telnet, self).on_new_line(line=line, is_full_line=is_full_line)

    def _send_telnet_commands(self, line, is_full_line, commands):
        """
        Sends telnet commands.

        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :param commands: list of commands to send.
        :return: if any command was sent then True, otherwise False.
        """
        len_cmds = len(commands)
        match_telnet_prompt = re.search(self._re_telnet_prompt, line)
        if not is_full_line and (len_cmds > 0) and match_telnet_prompt:
            cmd = commands.pop(0)
            self.connection.sendline(cmd)
            return True
        return False

    def _send_commands_before_establish_connection_if_requested(self, line, is_full_line):
        """
        Sends commands before open connection to telnet server.

        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None but raises ParsingDone if any command was sent by this method.
        """
        if self._send_telnet_commands(line, is_full_line, self.cmds_before_establish_connection):
            raise ParsingDone()

    def _send_commands_after_establish_connection_if_requested(self, line, is_full_line):
        """
        Sends commands after connection (after login and password) to telnet server.

        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: None but raises ParsingDone if any command was sent by this method.
        """
        if self._telnet_command_mode:
            if self._send_telnet_commands(line, is_full_line, self.cmds_after_establish_connection):
                self.connection.send(self.target_newline)
                self._telnet_command_mode = False
                raise ParsingDone()

    def _change_telnet_to_setting_commands(self):
        """
        Changes telnet mode to enter telnet commands not information from server.

        :return: None
        """
        if not self._telnet_command_mode:
            self.connection.send(chr(0x1D))  # ctrl + ]
            self._telnet_command_mode = True

    def _cmds_after_establish_connection_needed(self):
        """
        Checks if any command is requested to be sent to telnet command after establishing connection.

        :return: True if there is at least one command to execute. False is there is no command to execute.
        """
        ret = False
        if len(self.cmds_after_establish_connection) > 0:
            ret = True
        return ret

    def _commands_to_set_connection_after_login(self, line):
        """
        Sends command to telnet to change mode to enter telnet commands.

        :param line: Line from device.
        :return: True if command to change telnet mode was sent, False otherwise.
        """
        if self._cmds_after_establish_connection_needed():
            self._change_telnet_to_setting_commands()
            return True
        return False

    def _sent_additional_settings_commands(self):
        """
        Checks if additional commands for telnet mode are sent.

        :return: True if no any commands to change telnet left. False if any command left.
        """
        telnet_cmds_sent = (0 == len(self.cmds_after_establish_connection))
        return telnet_cmds_sent


COMMAND_OUTPUT = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #
export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS = {
    "login": "user", "password": "english", "port": "1500",
    "host": "host.domain.net", "expected_prompt": "host:.*#"
}

COMMAND_RESULT = {
    'LINES': [
        "Login:",
        "Login:user",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!",
        "host:~ #",
        "export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_username = """TERM=xterm-mono telnet host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #
export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_username = {
    "username": "user", "password": "english", "port": "1500",
    "host": "host.domain.net", "expected_prompt": "host:.*#"
}

COMMAND_RESULT_username = {
    'LINES': [
        "Login:",
        "Login:user",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!",
        "host:~ #",
        "export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}


COMMAND_OUTPUT_prompt = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1500
CLIENT5 [] has just connected!
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
export TMOUT="2678400"
host:~ #
export PS1="host_new#"
host_new#"""

COMMAND_KWARGS_prompt = {
    "login": "user", "password": "english", "port": "1500",
    "host": "host.domain.net", "expected_prompt": "host.*#",
    "set_prompt": "export PS1=\"host_new#\""
}

COMMAND_RESULT_prompt = {
    'LINES': [
        "CLIENT5 [] has just connected!",
        "Login:",
        "Login:user",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "export TMOUT=\"2678400\"",
        "host:~ #",
        "export PS1=\"host_new#\""
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_2prompts = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1500
CLIENT5 [] has just connected!
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
export TMOUT="2678400"
host:~ #
export PS1="host_new#"
host_new#"""

COMMAND_KWARGS_2prompts = {
    "login": "user", "password": "english", "port": "1500",
    "host": "host.domain.net", "expected_prompt": r"host_new#",
    "set_prompt": "export PS1=\"host_new#\"", "prompt_after_login": r"host:.*#"
}

COMMAND_RESULT_2prompts = {
    'LINES': [
        "CLIENT5 [] has just connected!",
        "Login:",
        "Login:user",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "export TMOUT=\"2678400\"",
        "host:~ #",
        "export PS1=\"host_new#\""
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_many_passwords = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1501
Login:
Login:user
Password:
Second password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ # """

COMMAND_KWARGS_many_passwords = {
    "login": "user", "password": ["english", "polish"], "port": 1501,
    "host": "host.domain.net", "expected_prompt": "host.*#", 'set_timeout': None,
}

COMMAND_RESULT_many_passwords = {
    'LINES': [
        "Login:",
        "Login:user",
        "Password:",
        "Second password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_many_passwords_repeat = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1501
Login:
Login:user
Password:
Second password:
Third password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ # """

COMMAND_KWARGS_many_passwords_repeat = {
    "login": "user", "password": ["english", "polish"], "port": 1501,
    "host": "host.domain.net", "expected_prompt": "host.*#", 'set_timeout': None,
}

COMMAND_RESULT_many_passwords_repeat = {
    'LINES': [
        "Login:",
        "Login:user",
        "Password:",
        "Second password:",
        "Third password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_no_settings = """
userl@host01:~> TERM=xterm-mono telnet host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

COMMAND_KWARGS_no_settings = {
    "login": "user", "password": "english", "port": "1500", 'set_timeout': None,
    "host": "host.domain.net", "expected_prompt": "host:.*#",
}

COMMAND_RESULT_no_settings = {
    'LINES': [
        "Login:",
        "Login:user",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!"
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_no_credentials = """
userl@host01:~> TERM=xterm-mono telnet host.domain.net 1425
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

COMMAND_KWARGS_no_credentials = {
    "login": None, "password": None, "port": 1425, 'set_timeout': None,
    "host": "host.domain.net", "expected_prompt": "host:.*#",
}

COMMAND_RESULT_no_credentials = {
    'LINES': [
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!"
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}


COMMAND_OUTPUT_prefix = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #"""

COMMAND_KWARGS_prefix = {
    "login": "user", "password": "english", "port": "1500", 'set_timeout': None,
    "host": "host.domain.net", "expected_prompt": "host:.*#", 'prefix': "-4",
}

COMMAND_RESULT_prefix = {
    "LINES": [
        "Login:",
        "Login:user",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!"
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}


COMMAND_OUTPUT_newline_after_prompt = """
user@host01:~> TERM=xterm-mono telnet -4 host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #
"""

COMMAND_KWARGS_newline_after_prompt = {
    "login": "user", "password": "english", "port": "1500", 'set_timeout': None,
    "host": "host.domain.net", "expected_prompt": "host:.*#", 'prefix': "-4",
    "allowed_newline_after_prompt": True
}

COMMAND_RESULT_newline_after_prompt = {
    'LINES': [
        "Login:",
        "Login:user",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "CLIENT5 [] has just connected!",
        "host:~ #",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}
