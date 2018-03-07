"""
:copyright: Nokia Networks
:author: Marcin Usielski
:contact: marcin.usielski@nokia.com
:maintainer:
:contact:
"""


import re
from genericunix import GenericUnix


class Ssh(GenericUnix):
    # Compiled regexp
    _reg_host_key = re.compile("Add correct host key in (\\S+) to get rid of this message.*\\n$",
                                    re.IGNORECASE)
    _reg_yes_no = re.compile("\(yes/no\)\?|'yes' or 'no':", re.IGNORECASE)
    _reg_id_dsa = re.compile("id_dsa:", re.IGNORECASE)
    _reg_password = re.compile("password:", re.IGNORECASE)
    _reg_permission_denied = re.compile("Permission denied, please try again", re.IGNORECASE)
    _reg_failed_strings = re.compile("Permission denied|No route to host|ssh: Could not", re.IGNORECASE)
    _reg_host_key_verification_failed = re.compile("Host key verification failed", re.IGNORECASE)
    _reg_new_line = re.compile(r"\n$")

    def __init__(self, connection, login, password, host, expected_prompt='>', port=0, known_hosts_on_failure='keygen',
                set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None):
        super(Ssh, self).__init__(connection)

        # Parameters defined by calling the command
        self.expected_prompt = expected_prompt
        self.login = login
        self.password = password
        self.host = host
        self.port = port
        self.known_hosts_on_failure = known_hosts_on_failure
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt

        self.command_string = self.get_cmd()
        self.ret_required = False

        # Internal variables
        self._hosts_file = ""
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_password = False
        self._sent_continue_connecting = False

    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = "TERM=xterm-mono ssh"
            if self.port:
                cmd = cmd + " -p " + str(self.port)
            cmd = cmd + " -l " + self.login + " " + self.host
        self._cmd_escaped = re.escape(cmd)
        return cmd

    def on_new_line(self, line):
        if (not self._cmd_matched) and (self._regex_helper.search(self._cmd_escaped, line)):
            self._cmd_matched = True
        elif self._cmd_matched:
            if (self.known_hosts_on_failure is not None) and self._regex_helper.search_compiled(Ssh._reg_host_key, line):
                self._hosts_file = self._regex_helper.group(1)
            if (not self._sent_continue_connecting) and (
               self._regex_helper.search_compiled(Ssh._reg_yes_no, line)):
                self.connection.send('yes')
                self._sent_continue_connecting = True
            elif (not self._sent_password) and (self._regex_helper.search_compiled(Ssh._reg_password, line)):
                self.connection.send(self.password)
                self._sent_password = True
            elif self._sent_password and (
                 self._regex_helper.search_compiled(Ssh._reg_permission_denied, line)):
                self._sent_password = False
            elif Ssh._reg_id_dsa.search(line):
                self.connection.send("")
            elif self._regex_helper.search_compiled(Ssh._reg_failed_strings, line):
                self.set_exception(Exception("command failed in line '%s'" % line))
            elif self._regex_helper.search_compiled(Ssh._reg_host_key_verification_failed, line):
                if self._hosts_file:
                    if "rm" == self.known_hosts_on_failure:
                        self.connection.send("\nrm -f " + self._hosts_file)
                    elif "keygen" == self.known_hosts_on_failure:
                        self.connection.send("\nssh-keygen -R " + self.host)
                    else:
                        self.set_exception(Exception("Bad value of parameter known_hosts_on_failure '%s'. Supported values: rm or keygen." % self.known_hosts_on_failure))
                    self._cmd_matched = False
                    self._sent_continue_connecting = False
                    self._sent_prompt = False
                    self._sent_timeout = False
                    self._sent_password = False
                    self.connection.send(self.command_string)
                else:
                    self.set_exception(Exception("command failed in line '%s'" % line))
            elif self._cmd_matched and self._regex_helper.search(self.expected_prompt, line):
                if self.set_timeout and not self._sent_timeout:
                    self.connection.send("\n" + self.set_timeout)
                    self._sent_timeout = True
                elif self.set_prompt and not self._sent_prompt:
                    self.connection.send("\n" + self.set_prompt)
                    self._sent_prompt = True
                else:
                    if not self._regex_helper.search(Ssh._reg_new_line, line):
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
