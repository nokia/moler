# -*- coding: utf-8 -*-
"""
Telnet command module.
"""

import re
from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import CommandFailure

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Telnet(GenericUnix):
    # Compiled regexp
    _re_login = re.compile("login:", re.IGNORECASE)
    _re_password = re.compile("password:", re.IGNORECASE)
    _re_failed_strings = re.compile("Permission denied|closed by foreign host|telnet:.*Name or service not known", re.IGNORECASE)
    _re_has_just_connected = re.compile(r"/has just connected|\{bash_history,ssh\}|Escape character is", re.IGNORECASE)

    def __init__(self, connection, login, password, host, port=0, prompt=None,
                 set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None, term_mono=True,
                 new_line_chars=None):
        super(Telnet, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        # Parameters defined by calling the command
        self.login = login
        self.password = password
        self.host = host
        self.port = port
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt
        self.term_mono = term_mono

        # Internal variables
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_login = False
        self._sent_password = False

    def build_command_string(self):
        cmd = ""
        if self.term_mono:
            cmd = "TERM=xterm-mono "
        cmd = cmd + "telnet " + self.host
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
            self.connection.send("")
            return
        sent = self.send_after_login_settings(line)
        if (not sent) and self.is_target_prompt(line) and (not is_full_line):
            if self.set_prompt and self.set_timeout:
                if self._sent_prompt and self._sent_timeout:
                    if not self.done():
                        self.set_result({})
            elif self.set_prompt:
                if self._sent_prompt:
                    if not self.done():
                        self.set_result({})
            elif self.set_timeout:
                if self._sent_timeout:
                    if not self.done():
                        self.set_result({})
            else:
                if not self.done():
                    self.set_result({})

    def send_login_if_requested(self, line):
        if (not self._sent_login) and self.is_login_requested(line):
            self.connection.send(self.login)
            self._sent_login = True
            self._sent_password = False

    def send_password_if_requested(self, line):
        if (not self._sent_password) and self.is_password_requested(line):
            self.connection.send(self.password)
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

    def timeout_set_needed(self):
        return self.set_timeout and not self._sent_timeout

    def send_timeout_set(self):
        self.connection.send("\n" + self.set_timeout)
        self._sent_timeout = True

    def prompt_set_needed(self):
        return self.set_prompt and not self._sent_prompt

    def send_prompt_set(self):
        self.connection.send("\n" + self.set_prompt)
        self._sent_prompt = True

    def is_failure_indication(self, line):
        return self._regex_helper.search_compiled(Telnet._re_failed_strings, line)

    def is_login_requested(self, line):
        return self._regex_helper.search_compiled(Telnet._re_login, line)

    def is_password_requested(self, line):
        return self._regex_helper.search_compiled(Telnet._re_password, line)

    def is_target_prompt(self, line):
        return self._regex_helper.search_compiled(self._re_prompt, line)


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
    "host": "host.domain.net", "prompt": "host:.*#"
}

COMMAND_RESULT = {}
