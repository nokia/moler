# -*- coding: utf-8 -*-
"""
Telnet command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
from moler.cmd.unix.genericunix import GenericUnix
from moler.textualgeneric import TextualGeneric
from moler.exceptions import CommandFailure


class Telnet(GenericUnix):
    # Compiled regexp
    _re_login = re.compile(r"login:", re.IGNORECASE)
    _re_password = re.compile(r"password:", re.IGNORECASE)
    _re_failed_strings = re.compile(r"Permission denied|closed by foreign host|telnet:.*Name or service not known", re.IGNORECASE)
    _re_has_just_connected = re.compile(r"/has just connected|\{bash_history,ssh\}|Escape character is", re.IGNORECASE)

    def __init__(self, connection, host, login=None, password=None, port=0, prompt=None, expected_prompt='>',
                 set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None, term_mono="TERM=xterm-mono", prefix=None,
                 new_line_chars=None):
        super(Telnet, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self._re_expected_prompt = TextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device
        self.login = login
        self.password = password
        self.host = host
        self.port = port
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt
        self.term_mono = term_mono
        self.prefix = prefix

        # Internal variables
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_login = False
        self._sent_password = False

    def build_command_string(self):
        cmd = ""
        if self.term_mono:
            cmd = self.term_mono + " "
        cmd = cmd + "telnet "
        if self.prefix:
            cmd = cmd + self.prefix + " "
        cmd = cmd + self.host
        if self.port:
            cmd = cmd + " " + str(self.port)
        return cmd

    def on_new_line(self, line, is_full_line):
        if self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            return
        self.send_login_if_requested(line)
        self.send_password_if_requested(line)

        if self._regex_helper.search_compiled(Telnet._re_has_just_connected, line):
            self.connection.sendline("")
            return
        sent = self.send_after_login_settings(line)
        if (not sent) and self.is_target_prompt(line) and (not is_full_line):
            if self.all_after_login_settings_sent() or self.no_after_login_settings_needed():
                if not self.done():
                    self.set_result({})

    def send_login_if_requested(self, line):
        if (not self._sent_login) and self.is_login_requested(line) and self.login:
            self.connection.sendline(self.login)
            self._sent_login = True
            self._sent_password = False

    def send_password_if_requested(self, line):
        if (not self._sent_password) and self.is_password_requested(line) and self.password:
            self.connection.sendline(self.password)
            self._sent_login = False
            self._sent_password = True

    def send_after_login_settings(self, line):
        if self.is_target_prompt(line):
            if self.timeout_set_needed():
                self.send_timeout_set()
                return True  # just sent
            elif self.prompt_set_needed():
                self.send_prompt_set()
                return True  # just sent
        return False  # nothing sent

    def all_after_login_settings_sent(self):
        return (((self.set_prompt and self.set_timeout) and     # both requested
                (self._sent_prompt and self._sent_timeout)) or  # & both sent

                (self.set_prompt and self._sent_prompt) or      # single req & sent

                (self.set_timeout and self._sent_timeout))      # single req & sent

    def no_after_login_settings_needed(self):
        return (not self.set_prompt) and (not self.set_timeout)

    def timeout_set_needed(self):
        return self.set_timeout and not self._sent_timeout

    def send_timeout_set(self):
        self.connection.sendline("\n" + self.set_timeout)
        self._sent_timeout = True

    def prompt_set_needed(self):
        return self.set_prompt and not self._sent_prompt

    def send_prompt_set(self):
        self.connection.sendline("\n" + self.set_prompt)
        self._sent_prompt = True

    def is_failure_indication(self, line):
        return self._regex_helper.search_compiled(Telnet._re_failed_strings, line)

    def is_login_requested(self, line):
        return self._regex_helper.search_compiled(Telnet._re_login, line)

    def is_password_requested(self, line):
        return self._regex_helper.search_compiled(Telnet._re_password, line)

    def is_target_prompt(self, line):
        return self._regex_helper.search_compiled(self._re_expected_prompt, line)


COMMAND_OUTPUT = """
amu012@belvedere07:~/automation/Flexi/config> TERM=xterm-mono telnet host.domain.net 1500
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
