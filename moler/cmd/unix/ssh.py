# -*- coding: utf-8 -*-
"""
Ssh command module.
"""
from re import compile, escape, IGNORECASE

from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'


class Ssh(GenericUnix):
    # Compiled regexp
    _reg_host_key = compile("Add correct host key in (\\S+) to get rid of this message.*\\n$",
                            IGNORECASE)
    _reg_yes_no = compile("\(yes/no\)\?|'yes' or 'no':", IGNORECASE)
    _reg_id_dsa = compile("id_dsa:", IGNORECASE)
    _reg_password = compile("password:", IGNORECASE)
    _reg_permission_denied = compile("Permission denied, please try again", IGNORECASE)
    _reg_failed_strings = compile("Permission denied|No route to host|ssh: Could not", IGNORECASE)
    _reg_host_key_verification_failed = compile("Host key verification failed", IGNORECASE)
    _reg_new_line = compile(r"\n$")

    def __init__(self, connection, login, password, host, expected_prompt='>', port=0, known_hosts_on_failure='keygen',
                 set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None, term_mono=True):
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
        self.term_mono = term_mono

        self.get_cmd()
        self.ret_required = False

        # Internal variables
        self._hosts_file = ""
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_password = False
        self._sent_continue_connecting = False

    def get_cmd(self, cmd=None):
        if cmd is None:
            cmd = ""
            if self.term_mono:
                cmd = "TERM=xterm-mono "
            cmd = cmd + "ssh"
            if self.port:
                cmd = cmd + " -p " + str(self.port)
            cmd = cmd + " -l " + self.login + " " + self.host
        #self._cmd_escaped = escape(cmd)
        #self.command_string = cmd
        return cmd

    def on_new_line(self, line):
        if not self._cmd_matched and self._regex_helper.search(self._cmd_escaped, line):
            self._cmd_matched = True
        elif self._cmd_matched:
            if self.known_hosts_on_failure is not None and self._regex_helper.search_compiled(Ssh._reg_host_key, line):
                self._hosts_file = self._regex_helper.group(1)
            if not self._sent_continue_connecting and self._regex_helper.search_compiled(Ssh._reg_yes_no, line):
                self.connection.send('yes')
                self._sent_continue_connecting = True
            elif not self._sent_password and self._regex_helper.search_compiled(Ssh._reg_password, line):
                self.connection.send(self.password)
                self._sent_password = True
            elif self._sent_password and self._regex_helper.search_compiled(Ssh._reg_permission_denied, line):
                self._sent_password = False
            elif Ssh._reg_id_dsa.search(line):
                self.connection.send("")
            elif self._regex_helper.search_compiled(Ssh._reg_failed_strings, line):
                self.set_exception(Exception("command failed in line '{}'".format(line)))
            elif self._regex_helper.search_compiled(Ssh._reg_host_key_verification_failed, line):
                if self._hosts_file:
                    if "rm" == self.known_hosts_on_failure:
                        self.connection.send("\nrm -f " + self._hosts_file)
                    elif "keygen" == self.known_hosts_on_failure:
                        self.connection.send("\nssh-keygen -R " + self.host)
                    else:
                        self.set_exception(Exception("Bad value of parameter known_hosts_on_failure '{}'. "
                                                     "Supported values: rm or keygen.".format(self.known_hosts_on_failure)))
                    self._cmd_matched = False
                    self._sent_continue_connecting = False
                    self._sent_prompt = False
                    self._sent_timeout = False
                    self._sent_password = False
                    self.connection.send(self.command_string)
                else:
                    self.set_exception(Exception("command failed in line '{}'".format(line)))
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


COMMAND_OUTPUT_ver_execute = """
amu012@belvedere07:~/automation/Flexi/config>
amu012@belvedere07:~/automation/Flexi/config>TERM=xterm-mono ssh -l fzm-tdd-1 FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Password:
Last login: Thu Nov 23 10:38:16 2017 from 10.83.200.37
Have a lot of fun...
fzm-tdd-1:~ #
fzm-tdd-1:~ # export TMOUT="2678400"
fzm-tdd-1:~ #"""

COMMAND_KWARGS_ver_execute = {
    "login": "fzm-tdd-1", "password": "Nokia",
    "host": "FZM-TDD-1.lab0.krk-lab.nsn-rdnet.net", "expected_prompt": "fzm-tdd-1:.*#"
}

COMMAND_RESULT_ver_execute = {

}
