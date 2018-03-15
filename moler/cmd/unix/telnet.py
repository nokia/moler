# -*- coding: utf-8 -*-
"""
Telnet command module.
"""
from re import compile, IGNORECASE

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Telnet(GenericUnix):
    # Compiled regexp
    _reg_login = compile("login:", IGNORECASE)
    _reg_password = compile("password:", IGNORECASE)
    _reg_failed_strings = compile("Permission denied|closed by foreign host|telnet:.*Name or service not known", IGNORECASE)
    _reg_has_just_connected = compile(r"/has just connected|\{bash_history,ssh\}|Escape character is", IGNORECASE)
    _reg_new_line = compile(r"\n$")

    def __init__(self, connection, login, password, host, expected_prompt='>', port=0,
                 set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None, term_mono=True):
        super(Telnet, self).__init__(connection)

        # Parameters defined by calling the command
        self.expected_prompt = expected_prompt
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

    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = ""
            if self.term_mono:
                cmd = "TERM=xterm-mono "
            cmd = cmd + "telnet " + self.host
            if self.port:
                cmd = cmd + " " + str(self.port)
        return cmd

    def on_new_line(self, line):
        if (not self._cmd_matched) and (self._regex_helper.search(self._cmd_escaped, line)):
            self._cmd_matched = True
        elif self._cmd_matched:
            if not self._sent_login and (self._regex_helper.search_compiled(Telnet._reg_login, line)):
                self.connection.send(self.login)
                self._sent_login = True
                self._sent_password = False
            elif (not self._sent_password) and (self._regex_helper.search_compiled(Telnet._reg_password, line)):
                self.connection.send(self.password)
                self._sent_login = False
                self._sent_password = True
            elif self._regex_helper.search_compiled(Telnet._reg_failed_strings, line):
                self.set_exception(Exception("command failed in line '{}'".format(line)))
            elif self._regex_helper.search_compiled(Telnet._reg_has_just_connected, line):
                self.connection.send("")
            elif self._cmd_matched and self._regex_helper.search(self.expected_prompt, line):
                if self.set_timeout and not self._sent_timeout:
                    self.connection.send("\n" + self.set_timeout)
                    self._sent_timeout = True
                elif self.set_prompt and not self._sent_prompt:
                    self.connection.send("\n" + self.set_prompt)
                    self._sent_prompt = True
                else:
                    if not self._regex_helper.search(Telnet._reg_new_line, line):
                        if self.set_prompt and self.set_timeout:
                            if self._sent_prompt and self._sent_timeout:
                                if not self.done():
                                    self.set_result(self.ret)
                        elif self.set_prompt:
                            if self._sent_prompt:
                                if not self.done():
                                    self.set_result(self.ret)
                        elif self.set_timeout:
                            if self._sent_timeout:
                                if not self.done():
                                    self.set_result(self.ret)
                        else:
                            if not self.done():
                                self.set_result(self.ret)


COMMAND_OUTPUT_ver_execute = """
amu012@belvedere07:~/automation/Flexi/config> TERM=xterm-mono telnet FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net 6000
Login:
Login:fzm-tdd-1
Password:
Last login: Thu Nov 23 10:38:16 2017 from 10.83.200.37
Have a lot of fun...
fzm-tdd-1:~ #
export TMOUT="2678400",
fzm-tdd-1:~ #"""

COMMAND_KWARGS_ver_execute = {
    "login": "fzm-tdd-1", "password": "Nokia", "port": "6000",
    "host": "FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", "expected_prompt": "fzm-tdd-1:.*#"
}

COMMAND_RESULT_ver_execute = {

}
