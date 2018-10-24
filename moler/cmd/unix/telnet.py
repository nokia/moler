# -*- coding: utf-8 -*-
"""
Telnet command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
import copy

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Telnet(GenericUnixCommand):
    # Compiled regexp
    _re_login = re.compile(r"login:", re.IGNORECASE)
    _re_password = re.compile(r"password:", re.IGNORECASE)
    _re_failed_strings = re.compile(
        r"Permission denied|closed by foreign host|telnet:.*Name or service not known|"
        "is not a typo you can use command-not-found to lookup the package|command not found",
        re.IGNORECASE)
    _re_has_just_connected = re.compile(r"/has just connected|\{bash_history,ssh\}|Escape character is", re.IGNORECASE)

    def __init__(self, connection, host, login=None, password=None, port=0, prompt=None, expected_prompt=r'^>\s*',
                 set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None, term_mono="TERM=xterm-mono", prefix=None,
                 newline_chars=None, cmds_before_establish_connection=[], cmds_after_establish_connection=[],
                 telnet_prompt=r"^\s*telnet>\s*", encrypt_password=True, runner=None, target_newline="\n"):
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
        self.cmds_before_establish_connection = copy.deepcopy(cmds_before_establish_connection)
        self.cmds_after_establish_connection = copy.deepcopy(cmds_after_establish_connection)
        self.target_newline = target_newline

        # Internal variables
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_login = False
        self._sent_password = False
        self._telnet_command_mode = False

    def build_command_string(self):
        cmd = ""
        if self.term_mono:
            cmd = self.term_mono + " "
        cmd = cmd + "telnet"
        if self.prefix:
            cmd = cmd + " " + self.prefix
        host_port_cmd = self.host
        if self.port:
            host_port_cmd = host_port_cmd + " " + str(self.port)
        if 0 == len(self.cmds_before_establish_connection):
            cmd = cmd + " " + host_port_cmd
        else:
            self.cmds_before_establish_connection.append("open " + host_port_cmd)
        return cmd

    def on_new_line(self, line, is_full_line):
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
        if self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            raise ParsingDone()

    def _settings_after_login(self, line, is_full_line):
        sent = self._send_after_login_settings(line)
        if sent:
            raise ParsingDone()
        if (not sent) and self._is_target_prompt(line) and (not is_full_line):
            if self._all_after_login_settings_sent() or self._no_after_login_settings_needed():
                if not self.done():
                    self.set_result({})
                    raise ParsingDone()

    def _just_connected(self, line):
        if self._regex_helper.search_compiled(Telnet._re_has_just_connected, line):
            self.connection.send(self.target_newline)
            raise ParsingDone()

    def _send_telnet_commands(self, line, is_full_line, commands):
        len_cmds = len(commands)
        match_telnet_prompt = re.search(self._re_telnet_prompt, line)
        if not is_full_line and (len_cmds > 0) and match_telnet_prompt:
            cmd = commands.pop(0)
            self.connection.sendline(cmd)
            return True
        return False

    def _send_commands_before_establish_connection_if_requested(self, line, is_full_line):
        if self._send_telnet_commands(line, is_full_line, self.cmds_before_establish_connection):
            raise ParsingDone()

    def _send_commands_after_establish_connection_if_requested(self, line, is_full_line):
        if self._telnet_command_mode:
            if self._send_telnet_commands(line, is_full_line, self.cmds_after_establish_connection):
                self.connection.send(self.target_newline)
                self._telnet_command_mode = False
                raise ParsingDone()

    def _change_telnet_to_setting_commands(self):
        if not self._telnet_command_mode:
            self.connection.send(chr(0x1D))  # ctrl + ]
            self._telnet_command_mode = True

    def _send_login_if_requested(self, line):
        if (not self._sent_login) and self._is_login_requested(line) and self.login:
            self.connection.send("{}{}".format(self.login, self.target_newline))
            self._sent_login = True
            self._sent_password = False
            raise ParsingDone()

    def _send_password_if_requested(self, line):
        if (not self._sent_password) and self._is_password_requested(line) and self.password:
            self.connection.send("{}{}".format(self.password, self.target_newline), encrypt=self.encrypt_password)
            self._sent_login = False
            self._sent_password = True
            raise ParsingDone()

    def _send_after_login_settings(self, line):
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
        ret = False
        if len(self.cmds_after_establish_connection) > 0:
            ret = True
        return ret

    def _all_after_login_settings_sent(self):
        telnet_cmds_sent = (0 == len(self.cmds_after_establish_connection))
        both_requested = self.set_prompt and self.set_timeout
        both_sent = self._sent_prompt and self._sent_timeout
        single_req_and_sent1 = self.set_prompt and self._sent_prompt
        single_req_and_sent2 = self.set_timeout and self._sent_timeout
        terminal_cmds_sent = ((both_requested and both_sent) or single_req_and_sent1 or single_req_and_sent2)
        return terminal_cmds_sent and telnet_cmds_sent

    def _no_after_login_settings_needed(self):
        return (not self.set_prompt) and (not self.set_timeout)

    def _timeout_set_needed(self):
        return self.set_timeout and not self._sent_timeout

    def _send_timeout_set(self):
        self.connection.sendline("\n" + self.set_timeout)
        self._sent_timeout = True

    def _prompt_set_needed(self):
        return self.set_prompt and not self._sent_prompt

    def _send_prompt_set(self):
        self.connection.sendline("\n" + self.set_prompt)
        self._sent_prompt = True

    def is_failure_indication(self, line):
        return self._regex_helper.search_compiled(Telnet._re_failed_strings, line)

    def _is_login_requested(self, line):
        return self._regex_helper.search_compiled(Telnet._re_login, line)

    def _is_password_requested(self, line):
        return self._regex_helper.search_compiled(Telnet._re_password, line)

    def _is_target_prompt(self, line):
        return self._regex_helper.search_compiled(self._re_expected_prompt, line)


COMMAND_OUTPUT = """
user@host01:~> TERM=xterm-mono telnet host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
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
