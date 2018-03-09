"""
:copyright: Nokia Networks
:author: Marcin Usielski
:contact: marcin.usielski@nokia.com
:maintainer:
:contact:
"""

import re
from command.unix.genericunix import GenericUnix


class Telnet(GenericUnix):
    # Compiled regexp
    _reg_login = re.compile("login:", re.IGNORECASE)
    _reg_password = re.compile("password:", re.IGNORECASE)
    _reg_failed_strings = re.compile(
        "Permission denied|closed by foreign host|telnet:.*Name or service not known", re.IGNORECASE)
    _reg_has_just_connected = re.compile(r"/has just connected|\{bash_history,ssh\}|Escape character is",
        re.IGNORECASE)
    _reg_new_line = re.compile(r"\n$")

    def __init__(self, connection, login, password, host, expected_prompt='>', port=0, set_timeout=r'export TMOUT=\"2678400\"',
                       set_prompt=None):
        super(Telnet, self).__init__(connection)

        # Parameters defined by calling the command
        self.expected_prompt = expected_prompt
        self.login = login
        self.password = password
        self.host = host
        self.port = port
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt

        self.command_string = self.get_cmd()

        # Internal variables
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_login = False
        self._sent_password = False

    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = "TERM=xterm-mono telnet " + self.host
            if self.port:
                cmd = cmd + " " + str(self.port)
            self.command_string = cmd
        self._cmd_escaped = re.escape(cmd)
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
                self.set_exception(Exception("command failed in line '%s'" % line))
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


