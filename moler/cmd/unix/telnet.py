# -*- coding: utf-8 -*-
"""
Telnet command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from moler.helpers import copy_list


class Telnet(GenericUnixCommand):
    # Compiled regexp
    _re_login = re.compile(r"login:", re.IGNORECASE)
    _re_password = re.compile(r"password:", re.IGNORECASE)
    _re_failed_strings = re.compile(
        r"Permission denied|closed by foreign host|telnet:.*Name or service not known|"
        "is not a typo you can use command-not-found to lookup the package|command not found",
        re.IGNORECASE)
    _re_has_just_connected = re.compile(r"has just connected|\{bash_history,ssh\}|Escape character is", re.IGNORECASE)

    def __init__(self, connection, host, login=None, password=None, port=0, prompt=None, expected_prompt=r'^>\s*',
                 set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None, term_mono="TERM=xterm-mono", prefix=None,
                 newline_chars=None, cmds_before_establish_connection=None, cmds_after_establish_connection=None,
                 telnet_prompt=r"^\s*telnet>\s*", encrypt_password=True, runner=None, target_newline="\n"):
        """
        :param connection: moler connection to device, terminal when command is executed
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
        :param encrypt_password: If True then * will be in logs when password is sent, otherwise plain text
        :param runner: Runner to run command
        :param target_newline: newline chars on remote system where ssh connects
        """
        super(Telnet, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device
        self._re_telnet_prompt = CommandTextualGeneric._calculate_prompt(telnet_prompt)  # Prompt for telnet commands
        self.login = login
        self.password = password
        self.host = host
        self.port = port
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt
        self.term_mono = term_mono
        self.prefix = prefix
        self.encrypt_password = encrypt_password
        self.cmds_before_establish_connection = copy_list(cmds_before_establish_connection)
        self.cmds_after_establish_connection = copy_list(cmds_after_establish_connection)
        self.target_newline = target_newline

        # Internal variables
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_login = False
        self._sent_password = False
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
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        try:
            self._parse_failure_indication(line)
            self._send_commands_before_establish_connection_if_requested(line, is_full_line)
            self._send_login_if_requested(line)
            self._send_password_if_requested(line)
            self._just_connected(line)
            self._send_commands_after_establish_connection_if_requested(line, is_full_line)
            self._settings_after_login(line, is_full_line)
        except ParsingDone:
            pass

    def _parse_failure_indication(self, line):
        """
        Detects fail from command output.
        :param line: Line from device
        :return: Match object if matches, None otherwise
        """
        if self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            raise ParsingDone()

    def _settings_after_login(self, line, is_full_line):
        """
        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        sent = self._send_after_login_settings(line)
        if sent:
            raise ParsingDone()
        if (not sent) and self._is_target_prompt(line) and (not is_full_line):
            if self._all_after_login_settings_sent() or self._no_after_login_settings_needed():
                if not self.done():
                    self.set_result({})
                    raise ParsingDone()

    def _just_connected(self, line):
        """
        Checks if line contains has just connected
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Telnet._re_has_just_connected, line):
            self.connection.send(self.target_newline)
            raise ParsingDone()

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
        :return: Nothing but raises ParsingDone if any command was sent by this method.
        """
        if self._send_telnet_commands(line, is_full_line, self.cmds_before_establish_connection):
            raise ParsingDone()

    def _send_commands_after_establish_connection_if_requested(self, line, is_full_line):
        """
        Sends commands after connection (after login and password) to telnet server.
        :param line: Line from device.
        :param is_full_line: True if line had new line chars, False otherwise.
        :return: Nothing but raises ParsingDone if any command was sent by this method.
        """
        if self._telnet_command_mode:
            if self._send_telnet_commands(line, is_full_line, self.cmds_after_establish_connection):
                self.connection.send(self.target_newline)
                self._telnet_command_mode = False
                raise ParsingDone()

    def _change_telnet_to_setting_commands(self):
        """
        Changes telnet mode to enter telnet commands not information from server.
        :return: Nothing
        """
        if not self._telnet_command_mode:
            self.connection.send(chr(0x1D))  # ctrl + ]
            self._telnet_command_mode = True

    def _send_login_if_requested(self, line):
        """
        Sends login if requested by server.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if login was sent.
        """
        if (not self._sent_login) and self._is_login_requested(line) and self.login:
            self.connection.send("{}{}".format(self.login, self.target_newline))
            self._sent_login = True
            self._sent_password = False
            raise ParsingDone()

    def _send_password_if_requested(self, line):
        """
        Sends server if requested by server.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if password was sent.
        """
        if (not self._sent_password) and self._is_password_requested(line) and self.password:
            self.connection.send("{}{}".format(self.password, self.target_newline), encrypt=self.encrypt_password)
            self._sent_login = False
            self._sent_password = True
            raise ParsingDone()

    def _send_after_login_settings(self, line):
        """
        Sends commands to set timeout and to change prompt.
        :param line: Line from device.
        :return: True if any command was sent, False if no command was sent.
        """
        if self._is_target_prompt(line):
            if self._cmds_after_establish_connection_needed():
                self._change_telnet_to_setting_commands()
                return True
            if self._timeout_set_needed():
                self._send_timeout_set()
                return True  # just sent
            elif self._prompt_set_needed():
                self._send_prompt_set()
                return True  # just sent
        return False  # nothing sent

    def _cmds_after_establish_connection_needed(self):
        """
        Checks if any command is requested to be sent to telnet command after establishing connection.
        :return: True if there is at least one command to execute. False is there is no command to execute.
        """
        ret = False
        if len(self.cmds_after_establish_connection) > 0:
            ret = True
        return ret

    def _all_after_login_settings_sent(self):
        """
        Checks if all commands were sent by telnet command.
        :return: True if all requested commands were sent, False if at least one left.
        """
        telnet_cmds_sent = (0 == len(self.cmds_after_establish_connection))
        both_requested = self.set_prompt and self.set_timeout
        both_sent = self._sent_prompt and self._sent_timeout
        single_req_and_sent1 = self.set_prompt and self._sent_prompt
        single_req_and_sent2 = self.set_timeout and self._sent_timeout
        terminal_cmds_sent = ((both_requested and both_sent) or single_req_and_sent1 or single_req_and_sent2)
        return terminal_cmds_sent and telnet_cmds_sent

    def _no_after_login_settings_needed(self):
        """
        Checks if prompt and timeout commands are sent.
        :return: True if commands for login nor timeout are no needed.
        """
        return (not self.set_prompt) and (not self.set_timeout)

    def _timeout_set_needed(self):
        """
        Checks if command to set timeout is still needed.
        :return: True if command to set timeout is needed, otherwise (sent or not requested) False
        """
        return self.set_timeout and not self._sent_timeout

    def _send_timeout_set(self):
        """
        Sends command to set timeout
        :return: Nothing
        """
        self.connection.sendline("{}{}".format(self.target_newline, self.set_timeout))
        self._sent_timeout = True

    def _prompt_set_needed(self):
        """
        Checks if command to set prompt is still needed.
        :return: True if command to set prompt is needed, otherwise (sent or not requested) False
        """
        return self.set_prompt and not self._sent_prompt

    def _send_prompt_set(self):
        """
        Sends command to set prompt
        :return: Nothing
        """
        self.connection.sendline("{}{}".format(self.target_newline, self.set_prompt))
        self._sent_prompt = True

    def is_failure_indication(self, line):
        """
        Checks if line contains information that command fails
        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(Telnet._re_failed_strings, line)

    def _is_login_requested(self, line):
        """
        Checks if line contains information that commands waits for login
        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(Telnet._re_login, line)

    def _is_password_requested(self, line):
        """
        Checks if line contains information that commands waits for password
        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(Telnet._re_password, line)

    def _is_target_prompt(self, line):
        """
        Checks if line contains prompt on target system
        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(self._re_expected_prompt, line)


COMMAND_OUTPUT = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
CLIENT5 [] has just connected!
host:~ #
export TMOUT="2678400",
host:~ #"""

COMMAND_KWARGS = {
    "login": "user", "password": "english", "port": "1500",
    "host": "host.domain.net", "expected_prompt": "host:.*#"
}

COMMAND_RESULT = {}

COMMAND_OUTPUT_prompt = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1500
CLIENT5 [] has just connected!
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
export TMOUT="2678400",
host:~ #
export PS1="host_new#",
host_new#"""

COMMAND_KWARGS_prompt = {
    "login": "user", "password": "english", "port": "1500",
    "host": "host.domain.net", "expected_prompt": "host.*#",
    "set_prompt": "export PS1=\"host_new#\""

}

COMMAND_RESULT_prompt = {}


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

COMMAND_RESULT_no_settings = {}


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

COMMAND_RESULT_prefix = {}
