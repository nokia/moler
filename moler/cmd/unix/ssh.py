# -*- coding: utf-8 -*-
"""
Ssh command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re
import six

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Ssh(GenericUnixCommand):
    # Compiled regexp
    _re_host_key = re.compile(r"Add correct host key in (?P<HOSTS_FILE>\S+) to get rid of this message", re.IGNORECASE)
    _re_yes_no = re.compile(r"\(yes/no\)\?|'yes' or 'no':", re.IGNORECASE)
    _re_id_dsa = re.compile(r"id_dsa:", re.IGNORECASE)
    _re_password = re.compile(r"(password.*:)", re.IGNORECASE)
    _re_failed_strings = re.compile(r"Permission denied|No route to host|ssh: Could not", re.IGNORECASE)
    _re_host_key_verification_failed = re.compile(r"Host key verification failed", re.IGNORECASE)
    _re_resize = re.compile(r"999H")

    def __init__(self, connection, login, password, host, prompt=None, expected_prompt='>', port=0,
                 known_hosts_on_failure='keygen', set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None,
                 term_mono="TERM=xterm-mono", newline_chars=None, encrypt_password=True, runner=None,
                 target_newline="\n", allowed_newline_after_prompt=False):
        """
        :param connection: moler connection to device, terminal when command is executed
        :param login: ssh login
        :param password: ssh password or list of passwords for multi passwords connection
        :param host: host to ssh
        :param prompt: start prompt (on system where command ssh starts)
        :param expected_prompt: final prompt (on system where command ssh connects)
        :param port: port to ssh connect
        :param known_hosts_on_failure: "rm" or "keygen" how to deal with error. If empty then ssh fails.
        :param set_timeout: Command to set timeout after ssh connects
        :param set_prompt: Command to set prompt after ssh connects
        :param term_mono: Params to set ssh mono connection (useful in script)
        :param newline_chars: Characters to split lines
        :param encrypt_password: If True then * will be in logs when password is sent, otherwise plain text
        :param runner: Runner to run command
        :param target_newline: newline chars on remote system where ssh connects
        ;param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt
        """
        super(Ssh, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        # Parameters defined by calling the command
        self._re_expected_prompt = CommandTextualGeneric._calculate_prompt(expected_prompt)  # Expected prompt on device
        self.login = login
        if isinstance(password, six.string_types):
            self._passwords = [password]
        else:
            self._passwords = list(password)  # copy of list of passwords to modify
        self.host = host
        self.port = port
        self.known_hosts_on_failure = known_hosts_on_failure
        self.set_timeout = set_timeout
        self.set_prompt = set_prompt
        self.term_mono = term_mono
        self.encrypt_password = encrypt_password
        self.target_newline = target_newline
        self.allowed_newline_after_prompt = allowed_newline_after_prompt

        self.ret_required = False

        # Internal variables
        self._hosts_file = ""
        self._sent_timeout = False
        self._sent_prompt = False
        self._sent_password = False
        self._sent_continue_connecting = False
        self._resize_sent = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = ""
        if self.term_mono:
            cmd = "{} ".format(self.term_mono)
        cmd += "ssh"
        if self.port:
            cmd = "{} -p {}".format(cmd, self.port)
        if self.login:
            cmd = "{} -l {}".format(cmd, self.login)
        cmd = "{} {}".format(cmd, self.host)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        try:
            self._check_if_resize(line)
            self._check_if_failure(line)
            self._get_hosts_file_if_displayed(line)
            self._push_yes_if_needed(line)
            self._send_password_if_requested(line)
            self._id_dsa(line)
            self._host_key_verification(line)
            self._commands_after_established(line, is_full_line)
        except ParsingDone:
            pass
        if is_full_line:
            self._sent_password = False  # Clear flag for multi passwords connections

    def is_failure_indication(self, line):
        """
        Detects fail from command output.
        :param line: Line from device
        :return: Match object if matches, None otherwise
        """
        return self._regex_helper.search_compiled(Ssh._re_failed_strings, line)

    def _commands_after_established(self, line, is_full_line):
        """
        Performs commands after ssh connection is established and user is logged in.
        :param line: Line from device.
        :param is_full_line: True is line contained new line chars, False otherwise.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        sent = self._send_after_login_settings(line)
        if sent:
            raise ParsingDone()
        if (not sent) and self._is_target_prompt(line):
            if not is_full_line or self.allowed_newline_after_prompt:
                if self._all_after_login_settings_sent() or self._no_after_login_settings_needed():
                    if not self.done():
                        self.set_result({})
                    raise ParsingDone()

    def _host_key_verification(self, line):
        """
        Checks regex host key verification.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(Ssh._re_host_key_verification_failed, line):
            if self._hosts_file:
                self._handle_failed_host_key_verification()
            else:
                self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            raise ParsingDone()

    def _id_dsa(self, line):
        """
        Checks id dsa.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if Ssh._re_id_dsa.search(line):
            self.connection.sendline("")
            raise ParsingDone()

    def _check_if_failure(self, line):
        """
        Checks if line from device has information about failed ssh.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if self.is_failure_indication(line):
            self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            raise ParsingDone()

    def _get_hosts_file_if_displayed(self, line):
        """
        Checks if line from device has info about hosts file.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if (self.known_hosts_on_failure is not None) and self._regex_helper.search_compiled(Ssh._re_host_key, line):
            self._hosts_file = self._regex_helper.group("HOSTS_FILE")
            raise ParsingDone()

    def _push_yes_if_needed(self, line):
        """
        Checks if line from device has information about waiting for sent yes/no.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if (not self._sent_continue_connecting) and self._regex_helper.search_compiled(Ssh._re_yes_no, line):
            self.connection.sendline('yes')
            self._sent_continue_connecting = True
            raise ParsingDone()

    def _send_password_if_requested(self, line):
        """
        Checks if line from device has information about waiting for password.
        :param line: Line from device.
        :return: Nothing but raises ParsingDone if regex matches.
        """
        if (not self._sent_password) and self._is_password_requested(line):
            try:
                pwd = self._passwords.pop(0)
                self.connection.sendline(pwd, encrypt=self.encrypt_password)
            except IndexError:
                self.set_exception(CommandFailure(self, "Password was requested but no more passwords provided."))
            self._sent_password = True
            raise ParsingDone()

    def _handle_failed_host_key_verification(self):
        """
        Handles situation when failed host key verification.
        :return: Nothing.
        """
        if "rm" == self.known_hosts_on_failure:
            self.connection.sendline("\nrm -f {}".format(self._hosts_file))
        elif "keygen" == self.known_hosts_on_failure:
            self.connection.sendline("\nssh-keygen -R {}".format(self.host))
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

    def _send_after_login_settings(self, line):
        """
        Sends information about timeout and prompt.
        :param line: Line from device.
        :return: True if anything was sent, False otherwise.
        """
        if self._is_target_prompt(line):
            if self._timeout_set_needed():
                self._send_timeout_set()
                return True  # just sent
            elif self._prompt_set_needed():
                self._send_prompt_set()
                return True  # just sent
        return False  # nothing sent

    def _all_after_login_settings_sent(self):
        """
        Checks if all requested commands are sent.
        :return: True if all commands after ssh connection establishing are sent, False otherwise
        """
        both_requested = self.set_prompt and self.set_timeout
        both_sent = self._sent_prompt and self._sent_timeout
        single_req_and_sent1 = self.set_prompt and self._sent_prompt
        single_req_and_sent2 = self.set_timeout and self._sent_timeout
        return (both_requested and both_sent) or single_req_and_sent1 or single_req_and_sent2

    def _no_after_login_settings_needed(self):
        """
        Checks if any commands after logged in are requested.
        :return: True if no commands are awaited, False if any.
        """
        return (not self.set_prompt) and (not self.set_timeout)

    def _timeout_set_needed(self):
        """
        Checks if command for timeout is awaited.
        :return: True if command is set and not sent. False otherwise.
        """
        return self.set_timeout and not self._sent_timeout

    def _send_timeout_set(self):
        """
        Sends command to set timeout.
        :return: Nothing.
        """
        cmd = "{}{}{}".format(self.target_newline, self.set_timeout, self.target_newline)
        self.connection.send(cmd)
        self._sent_timeout = True

    def _prompt_set_needed(self):
        """
        Checks if command for prompt is awaited.
        :return: True if command is set and not sent. False otherwise.
        """
        return self.set_prompt and not self._sent_prompt

    def _send_prompt_set(self):
        """
        Sends command to set prompt.
        :return: Nothing.
        """
        cmd = "{}{}{}".format(self.target_newline, self.set_prompt, self.target_newline)
        self.connection.send(cmd)
        self._sent_prompt = True

    def _is_password_requested(self, line):
        """
        Checks if password is requested by device.
        :param line: Line from device.
        :return: Match object if regex matches, None otherwise.
        """
        return self._regex_helper.search_compiled(Ssh._re_password, line)

    def _is_target_prompt(self, line):
        """
        Checks if device sends prompt from target system.
        :param line: Line from device.
        :return: Match object if regex matches, None otherwise.
        """
        return self._regex_helper.search_compiled(self._re_expected_prompt, line)

    def _check_if_resize(self, line):
        """
        Checks if line from device has information about size of windows.
        :param line: Line from device.
        :return: Match object if regex matches, None otherwise.
        """
        if self._regex_helper.search_compiled(Ssh._re_resize, line) and not self._resize_sent:
            self._resize_sent = True
            self.connection.sendline("")
            raise ParsingDone()


COMMAND_OUTPUT = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
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

COMMAND_OUTPUT_prompt = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
Do you want to continue (yes/no)? yes
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export PS1="\\u$"
user$"""

COMMAND_KWARGS_prompt = {
    "login": "user", "password": "english", "set_prompt": r'export PS1="\\u$"',
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": r"host.*#|user\$"
}

COMMAND_RESULT_prompt = {}

COMMAND_OUTPUT_rm = """
client:~/>TERM=xterm-mono ssh -p 25 -l user host.domain.net
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the RSA key sent by the remote host is
[...].
Please contact your system administrator.
Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.
Offending RSA key in /home/you/.ssh/known_hosts:86
id_dsa:
RSA host key for host.domain.net has changed and you have requested strict checking.
Host key verification failed.
client:~/>rm /home/you/.ssh/known_hosts
client:~/>TERM=xterm-mono ssh -p 25 -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #"""

COMMAND_KWARGS_rm = {
    "login": "user", "password": "english", "known_hosts_on_failure": "rm", "port": 25,
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#", "set_timeout": None,
}

COMMAND_RESULT_rm = {}

COMMAND_OUTPUT_keygen = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the RSA key sent by the remote host is
[...].
Please contact your system administrator.
Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.
Offending RSA key in /home/you/.ssh/known_hosts:86
RSA host key for host.domain.net has changed and you have requested strict checking.
Host key verification failed.
client:~/>sh-keygen -R host.domain.net
client:~/>TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_keygen = {
    "login": "user", "password": "english", "known_hosts_on_failure": "keygen",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT_keygen = {}

COMMAND_OUTPUT_2_passwords = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
You are about to access a private system. This system is for the use of
authorized users only. All connections are logged to the extent and by means
acceptable by the local legislation. Any unauthorized access or access attempts
may be punished to the fullest extent possible under the applicable local
legislation.
Password:
This account is used as a fallback account. The only thing it provides is
the ability to switch to the root account.

Please enter the root password
Password:

USAGE OF THE ROOT ACCOUNT AND THE FULL BASH IS RECOMMENDED ONLY FOR LIMITED USE. PLEASE USE A NON-ROOT ACCOUNT AND THE SCLI SHELL (fsclish) AND/OR LIMITED BASH SHELL.

host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_2_passwords = {
    "login": "user", "password": ["english", "englishroot"],
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT_2_passwords = {}

COMMAND_OUTPUT_resize_window = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the RSA key sent by the remote host is
[...].
Please contact your system administrator.
Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.
Offending RSA key in /home/you/.ssh/known_hosts:86
RSA host key for host.domain.net has changed and you have requested strict checking.
Host key verification failed.
client:~/>sh-keygen -R host.domain.net
client:~/>TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Sun Jan  6 13:42:05 UTC+2 2019 on ttyAMA2
7[r[999;999H[6n
resize: unknown character, exiting.
Have a lot of fun...
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_resize_window = {
    "login": "user", "password": "english", "known_hosts_on_failure": "keygen",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT_resize_window = {}
