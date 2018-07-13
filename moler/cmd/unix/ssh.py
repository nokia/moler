# -*- coding: utf-8 -*-
"""
Ssh command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnix
from moler.exceptions import CommandFailure
from moler.textualgeneric import TextualGeneric


class Ssh(GenericUnix):
    # Compiled regexp
    _re_host_key = re.compile(r"Add correct host key in (\\S+) to get rid of this message.*\\n$", re.IGNORECASE)
    _re_yes_no = re.compile(r"\(yes/no\)\?|'yes' or 'no':", re.IGNORECASE)
    _re_id_dsa = re.compile(r"id_dsa:", re.IGNORECASE)
    _re_password = re.compile(r"password:", re.IGNORECASE)
    _re_permission_denied = re.compile(r"Permission denied, please try again", re.IGNORECASE)
    _re_failed_strings = re.compile(r"Permission denied|No route to host|ssh: Could not", re.IGNORECASE)
    _re_host_key_verification_failed = re.compile(r"Host key verification failed", re.IGNORECASE)

    def __init__(self, connection, login, password, host, prompt=None, expected_prompt='>', port=0,
                 known_hosts_on_failure='keygen', set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None,
                 term_mono="TERM=xterm-mono", new_line_chars=None):

        super(Ssh, self).__init__(connection, prompt, new_line_chars)

        # Parameters defined by calling the command
        self._re_expected_prompt = TextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device
        self.login = login
        self.password = password
        self.host = host
        self.port = port
        self.known_hosts_on_failure = known_hosts_on_failure
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt
        self.term_mono = term_mono

        self.ret_required = False

        # Internal variables
        self._hosts_file = ""
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_password = False
        self._sent_continue_connecting = False

    def build_command_string(self):
        cmd = ""
        if self.term_mono:
            cmd = self.term_mono + " "
        cmd += "ssh"
        if self.port:
            cmd += " -p " + str(self.port)
        cmd += " -l " + self.login + " " + self.host
        return cmd

    def on_new_line(self, line, is_full_line):
        if self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            return
        self.get_hosts_file_if_displayed(line)
        self.push_yes_if_needed(line)
        self.send_password_if_requested(line)

        if Ssh._re_id_dsa.search(line):
            self.connection.sendlineline("")
        elif self._regex_helper.search_compiled(Ssh._re_host_key_verification_failed, line):
            if self._hosts_file:
                self.handle_failed_host_key_verification()
            else:
                self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
        else:
            sent = self.send_after_login_settings(line)
            if (not sent) and self.is_target_prompt(line) and (not is_full_line):
                if self.all_after_login_settings_sent() or self.no_after_login_settings_needed():
                    if not self.done():
                        self.set_result({})

    def get_hosts_file_if_displayed(self, line):
        if (self.known_hosts_on_failure is not None) and self._regex_helper.search_compiled(Ssh._re_host_key, line):
            self._hosts_file = self._regex_helper.group(1)

    def push_yes_if_needed(self, line):
        if (not self._sent_continue_connecting) and self._regex_helper.search_compiled(Ssh._re_yes_no, line):
            self.connection.sendline('yes')
            self._sent_continue_connecting = True

    def send_password_if_requested(self, line):
        if (not self._sent_password) and self.is_password_requested(line):
            self.connection.sendline(self.password)
            self._sent_password = True
        elif self._sent_password and self._regex_helper.search_compiled(Ssh._re_permission_denied, line):
            self._sent_password = False

    def handle_failed_host_key_verification(self):
        if "rm" == self.known_hosts_on_failure:
            self.connection.sendline("\nrm -f " + self._hosts_file)
        elif "keygen" == self.known_hosts_on_failure:
            self.connection.sendline("\nssh-keygen -R " + self.host)
        else:
            self.set_exception(
                CommandFailure(self,
                               "Bad value of parameter known_hosts_on_failure '{}'. "
                               "Supported values: rm or keygen.".format(
                                   self.known_hosts_on_failure)))
        self._cmd_output_started = False
        self._sent_continue_connecting = False
        self._sent_prompt = False
        self._sent_timeout = False
        self._sent_password = False
        self.connection.sendline(self.command_string)

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
        return (((self.set_prompt and self.set_timeout) and  # both requested
                 (self._sent_prompt and self._sent_timeout)) or  # & both sent
                (self.set_prompt and self._sent_prompt) or  # single req & sent
                (self.set_timeout and self._sent_timeout))  # single req & sent

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
        return self._regex_helper.search_compiled(Ssh._re_failed_strings, line)

    def is_password_requested(self, line):
        return self._regex_helper.search_compiled(Ssh._re_password, line)

    def is_target_prompt(self, line):
        return self._regex_helper.search_compiled(self._re_expected_prompt, line)


COMMAND_OUTPUT = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS = {
    "login": "user", "password": "english",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT = {}
