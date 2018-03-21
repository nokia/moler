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
    _re_new_line = re.compile(r"\n$")

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
        if (not self._cmd_output_started) and (self._regex_helper.search(self._cmd_escaped, line)):
            self._cmd_output_started = True
        elif self._cmd_output_started:
            if not self._sent_login and (self._regex_helper.search_compiled(Telnet._re_login, line)):
                self.connection.send(self.login)
                self._sent_login = True
                self._sent_password = False
            elif (not self._sent_password) and (self._regex_helper.search_compiled(Telnet._re_password, line)):
                self.connection.send(self.password)
                self._sent_login = False
                self._sent_password = True
            elif self._regex_helper.search_compiled(Telnet._re_failed_strings, line):
                self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            elif self._regex_helper.search_compiled(Telnet._re_has_just_connected, line):
                self.connection.send("")
            elif self._cmd_output_started and self._regex_helper.search_compiled(self._re_prompt, line):
                if self.set_timeout and not self._sent_timeout:
                    self.connection.send("\n" + self.set_timeout)
                    self._sent_timeout = True
                elif self.set_prompt and not self._sent_prompt:
                    self.connection.send("\n" + self.set_prompt)
                    self._sent_prompt = True
                else:
                    if not self._regex_helper.search(Telnet._re_new_line, line):
                        if self.set_prompt and self.set_timeout:
                            if self._sent_prompt and self._sent_timeout:
                                if not self.done():
                                    self.set_result(self.current_ret)
                        elif self.set_prompt:
                            if self._sent_prompt:
                                if not self.done():
                                    self.set_result(self.current_ret)
                        elif self.set_timeout:
                            if self._sent_timeout:
                                if not self.done():
                                    self.set_result(self.current_ret)
                        else:
                            if not self.done():
                                self.set_result(self.current_ret)


COMMAND_OUTPUT_ver_execute = """
amu012@belvedere07:~/automation/Flexi/config> TERM=xterm-mono telnet host.domain.net 1500
Login:
Login:user
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
export TMOUT="2678400",
host:~ #"""

COMMAND_KWARGS_ver_execute = {
    "login": "user", "password": "english", "port": "1500",
    "host": "host.domain.net", "prompt": "host:.*#"
}

COMMAND_RESULT_ver_execute = {

}
