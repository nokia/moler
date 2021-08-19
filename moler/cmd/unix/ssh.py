# -*- coding: utf-8 -*-
"""
Ssh command module.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2021, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import re

from moler.cmd.unix.generictelnetssh import GenericTelnetSsh
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
from dateutil import parser


class Ssh(GenericTelnetSsh):
    # Compiled regexp

    # Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.
    _re_host_key = re.compile(r"Add correct host key in (?P<HOSTS_FILE>\S+) to get rid of this message", re.IGNORECASE)

    # Do you want to continue connecting? (y/n)
    # Do you want to continue (yes/no)?
    _re_yes_no = re.compile(r"\(y/n\)|\(yes/no.*\)\?|'yes' or 'no':", re.IGNORECASE)

    # id_dsa:
    _re_id_dsa = re.compile(r"id_dsa:", re.IGNORECASE)

    # Host key verification failed.
    _re_host_key_verification_failed = re.compile(r"Host key verification failed", re.IGNORECASE)

    # Permission denied (publickey,password,keyboard-interactive)
    _re_permission_denied_key_pass_keyboard = re.compile(r"Permission denied \(publickey,password,"
                                                         r"keyboard-interactive\)", re.IGNORECASE)

    # 7[r[999;999H[6n
    _re_resize = re.compile(r"999H")

    # Password:
    _re_password = re.compile(r"(password|Enter passphrase for key.*):", re.IGNORECASE)

    #  ssh-keygen -f "/home/user/.ssh/known_hosts" -R "2a00:8a02:60:1c::2:44"
    _re_keygen_from_output = re.compile(r"(?P<COMMAND>ssh-keygen.*)")

    def __init__(self, connection, login=None, password=None, host="0", prompt=None, expected_prompt='>', port=0,
                 known_hosts_on_failure='keygen', set_timeout=r'export TMOUT=\"2678400\"', set_prompt=None,
                 term_mono="TERM=xterm-mono", newline_chars=None, encrypt_password=True, runner=None,
                 target_newline="\n", allowed_newline_after_prompt=False, repeat_password=True,
                 options='-o ServerAliveInterval=7 -o ServerAliveCountMax=2',
                 failure_exceptions_indication=None, prompt_after_login=None, send_enter_after_connection=True,
                 username=None, permission_denied_key_pass_keyboard=r'ssh-keygen -f "~/.ssh/known_hosts" -R "{host}"',
                 allow_override_denied_key_pass_keyboard=True, suffix=None):
        """
        Moler class of Unix command ssh.

        :param connection: moler connection to device, terminal when command is executed.
        :param login: ssh login.
        :param password: ssh password or list of passwords for multi passwords connection.
        :param host: host to ssh.
        :param prompt: start prompt (on system where command ssh starts).
        :param expected_prompt: final prompt (on system where command ssh connects).
        :param port: port to ssh connect.
        :param known_hosts_on_failure: "rm" or "keygen" how to deal with error. If empty then ssh fails.
        :param set_timeout: Command to set timeout after ssh connects.
        :param set_prompt: Command to set prompt after ssh connects.
        :param term_mono: Params to set ssh mono connection (useful in script).
        :param newline_chars: Characters to split lines.
        :param encrypt_password: If True then * will be in logs when password is sent, otherwise plain text.
        :param runner: Runner to run command.
        :param target_newline: newline chars on remote system where ssh connects.
        :param allowed_newline_after_prompt: If True then newline chars may occur after expected (target) prompt.
        :param repeat_password: If True then repeat last password if no more provided. If False then exception is set.
        :param options: Options to add to command string just before host.
        :param failure_exceptions_indication: String with regex or regex object to omit failure even if failed string
         was found.
        :param prompt_after_login: prompt after login before send export PS1. If you do not change prompt exporting PS1
         then leave it None.
        :param send_enter_after_connection: set True to send new line char(s) after connection is established, False
         otherwise.
        :param username: login for ssh. Set this or login but not both.
        :param permission_denied_key_pass_keyboard: Set to not None value to execute command after match line:
         'Permission denied (publickey,password,keyboard-interactive)'.
        :param allow_override_denied_key_pass_keyboard: Set True to override the command ssh-keygen to command from ssh
         output. False to ignore ssh output.
        :param suffix: String to append after command ssh.
        """
        super(Ssh, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner,
                                  port=port, host=host, login=login, password=password,
                                  expected_prompt=expected_prompt, set_timeout=set_timeout, set_prompt=set_prompt,
                                  term_mono=term_mono, encrypt_password=encrypt_password,
                                  target_newline=target_newline,
                                  allowed_newline_after_prompt=allowed_newline_after_prompt,
                                  repeat_password=repeat_password,
                                  failure_exceptions_indication=failure_exceptions_indication,
                                  prompt_after_login=prompt_after_login,
                                  send_enter_after_connection=send_enter_after_connection,
                                  username=username
                                  )

        # Parameters defined by calling the command
        self.known_hosts_on_failure = known_hosts_on_failure
        self.options = options
        self.allow_override_denied_key_pass_keyboard = allow_override_denied_key_pass_keyboard
        self.suffix = suffix

        # Internal variables
        self._hosts_file = ""
        self._sent_continue_connecting = False
        self._resize_sent = False
        self._was_overridden_key_pass_keyboard = False
        self._permission_denied_key_pass_keyboard_cmd = None
        if permission_denied_key_pass_keyboard is not None:
            self._permission_denied_key_pass_keyboard_cmd = permission_denied_key_pass_keyboard.format(host=host)

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
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.host:
            cmd = "{} {}".format(cmd, self.host)
        if self.suffix:
            cmd = "{} {}".format(cmd, self.suffix)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._override_permission_denied_key_pass_keyboard(line)
            self._check_if_resize(line)
            self._get_hosts_file_if_displayed(line)
            self._push_yes_if_needed(line)
            self._id_dsa(line)
            self._host_key_verification(line)
            self._permission_denied_key_pass_keyboard(line)
        except ParsingDone:
            pass
        super(Ssh, self).on_new_line(line=line, is_full_line=is_full_line)

    def _override_permission_denied_key_pass_keyboard(self, line):
        """
        Checks if line contains new command.
        :param line: Line from device
        :return: None
        :raise ParsingDone
        """
        if self.allow_override_denied_key_pass_keyboard and not self._was_overridden_key_pass_keyboard and \
                self._regex_helper.search_compiled(Ssh._re_keygen_from_output, line):
            self._permission_denied_key_pass_keyboard_cmd = self._regex_helper.group("COMMAND")
            self._was_overridden_key_pass_keyboard = True
            raise ParsingDone()

    def _permission_denied_key_pass_keyboard(self, line):
        """
        Checks regex host key verification.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        if self._regex_helper.search_compiled(Ssh._re_permission_denied_key_pass_keyboard, line):
            if self._permission_denied_key_pass_keyboard_cmd:
                self._handle_permission_denied_key_pass_keyboard()
            else:
                self.set_exception(CommandFailure(self, "command failed in line '{}'".format(line)))
            raise ParsingDone()

    def _host_key_verification(self, line):
        """
        Checks regex host key verification.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
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
        :return: None but raises ParsingDone if regex matches.
        """
        if Ssh._re_id_dsa.search(line):
            self.connection.sendline("")
            raise ParsingDone()

    def _get_hosts_file_if_displayed(self, line):
        """
        Checks if line from device has info about hosts file.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        if (self.known_hosts_on_failure is not None) and self._regex_helper.search_compiled(Ssh._re_host_key, line):
            self._hosts_file = self._regex_helper.group("HOSTS_FILE")
            raise ParsingDone()

    def _push_yes_if_needed(self, line):
        """
        Checks if line from device has information about waiting for sent yes/no.

        :param line: Line from device.
        :return: None but raises ParsingDone if regex matches.
        """
        if (not self._sent_continue_connecting) and self._regex_helper.search_compiled(Ssh._re_yes_no, line):
            self.connection.sendline('yes')
            self._sent_continue_connecting = True
            raise ParsingDone()

    def _resend_command_string(self):
        self._cmd_output_started = False
        self._sent_continue_connecting = False
        self._sent_prompt = False
        self._sent_timeout = False
        self._sent = False
        self.connection.sendline(self.command_string)

    def _handle_permission_denied_key_pass_keyboard(self):
        """
        Handles situation when permission denied.

        :return: None
        """
        self.connection.sendline("\n{}".format(self._permission_denied_key_pass_keyboard_cmd))
        self._resend_command_string()

    def _handle_failed_host_key_verification(self):
        """
        Handles situation when failed host key verification.

        :return: None.
        """
        exception = None
        if "rm" == self.known_hosts_on_failure:
            self.connection.sendline("\nrm -f {}".format(self._hosts_file))
        elif "keygen" == self.known_hosts_on_failure:
            self.connection.sendline("\nssh-keygen -R {}".format(self.host))
        else:
            exception = CommandFailure(self,
                                       "Bad value of parameter known_hosts_on_failure '{}'. "
                                       "Supported values: rm or keygen.".format(
                                           self.known_hosts_on_failure))
        if exception:
            self.set_exception(exception=exception)
        else:
            self._resend_command_string()

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

    def _is_password_requested(self, line):
        """
        Checks if line contains information that commands waits for password.

        :param line: Line from device
        :return: Match object or None
        """
        return self._regex_helper.search_compiled(Ssh._re_password, line)


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

COMMAND_RESULT = {
    'LINES': [
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}


COMMAND_OUTPUT_permission_denied = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Permission denied (publickey,password,keyboard-interactive)
client:~/>ssh-keygen -f "~/.ssh/known_hosts" -R host.domain.net
client:~/>TERM=xterm-mono ssh -l user host.domain.net
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_permission_denied = {
    "login": "user", "password": "english",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT_permission_denied = {
    'LINES': [
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Permission denied (publickey,password,keyboard-interactive)",
        # "client:~/>ssh-keygen -f \"~/.ssh/known_hosts\" -R host.domain.net",
        # "client:~/>TERM=xterm-mono ssh -l user host.domain.net",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_passphrase = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Enter passphrase for key '/home/user/serviceuser_key_passphrase':
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_passphrase = {
    "login": "user", "password": "english",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT_passphrase = {
    'LINES': [
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Enter passphrase for key '/home/user/serviceuser_key_passphrase':",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_username = """TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_username = {
    "username": "user", "password": "english",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT_username = {
    'LINES': [
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

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
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": r"host.*#|user\$",
    "options": None,
}

COMMAND_RESULT_prompt = {
    "LINES": [
        "Do you want to continue (yes/no)? yes",
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export PS1=\"\\u$\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_2prompts = """
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

COMMAND_KWARGS_2prompts = {
    "login": "user", "password": "english", "set_prompt": r'export PS1="\\u$"',
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": r"user\$",
    "prompt_after_login": r"host.*#", "options": None,
}

COMMAND_RESULT_2prompts = {
    'LINES': [
        'Do you want to continue (yes/no)? yes',
        'To edit this message please edit /etc/ssh_banner',
        'You may put information to /etc/ssh_banner who is owner of '
        'this PC',
        'Password:',
        'Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1',
        'Have a lot of fun...',
        'host:~ #',
        'host:~ # export PS1="\\u$"'
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

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

COMMAND_RESULT_rm = {
    'LINES': [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!",
        "Someone could be eavesdropping on you right now (man-in-the-middle attack)!",
        "It is also possible that a host key has just been changed.",
        "The fingerprint for the RSA key sent by the remote host is",
        "[...].",
        "Please contact your system administrator.",
        "Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.",
        "Offending RSA key in /home/you/.ssh/known_hosts:86",
        "id_dsa:",
        "RSA host key for host.domain.net has changed and you have requested strict checking.",
        "Host key verification failed.",
        # "client:~/>rm /home/you/.ssh/known_hosts",
        # "client:~/>TERM=xterm-mono ssh -p 25 -l user host.domain.net",
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

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
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#",
    "options": None,
}

COMMAND_RESULT_keygen = {
    "LINES": [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!",
        "Someone could be eavesdropping on you right now (man-in-the-middle attack)!",
        "It is also possible that a host key has just been changed.",
        "The fingerprint for the RSA key sent by the remote host is",
        "[...].",
        "Please contact your system administrator.",
        "Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.",
        "Offending RSA key in /home/you/.ssh/known_hosts:86",
        "RSA host key for host.domain.net has changed and you have requested strict checking.",
        "Host key verification failed.",
        # "client:~/>sh-keygen -R host.domain.net",
        # "client:~/>TERM=xterm-mono ssh -l user host.domain.net",
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

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
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#",
    "options": None,
}

COMMAND_RESULT_2_passwords = {
    'LINES': [
        "You are about to access a private system. This system is for the use of",
        "authorized users only. All connections are logged to the extent and by means",
        "acceptable by the local legislation. Any unauthorized access or access attempts",
        "may be punished to the fullest extent possible under the applicable local",
        "legislation.",
        "Password:",
        "This account is used as a fallback account. The only thing it provides is",
        "the ability to switch to the root account.",
        "",
        "Please enter the root password",
        "Password:",
        "",
        "USAGE OF THE ROOT ACCOUNT AND THE FULL BASH IS RECOMMENDED ONLY FOR LIMITED USE. PLEASE USE A NON-ROOT ACCOUNT AND THE SCLI SHELL (fsclish) AND/OR LIMITED BASH SHELL.",
        "",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}


COMMAND_OUTPUT_2_passwords_repeat = """
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

COMMAND_KWARGS_2_passwords_repeat = {
    "login": "user", "password": "english", "repeat_password": True,
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#",
    "options": None,
}

COMMAND_RESULT_2_passwords_repeat = {
    'LINES': [
        "You are about to access a private system. This system is for the use of",
        "authorized users only. All connections are logged to the extent and by means",
        "acceptable by the local legislation. Any unauthorized access or access attempts",
        "may be punished to the fullest extent possible under the applicable local",
        "legislation.",
        "Password:",
        "This account is used as a fallback account. The only thing it provides is",
        "the ability to switch to the root account.",
        "",
        "Please enter the root password",
        "Password:",
        "",
        "USAGE OF THE ROOT ACCOUNT AND THE FULL BASH IS RECOMMENDED ONLY FOR LIMITED USE. PLEASE USE A NON-ROOT ACCOUNT AND THE SCLI SHELL (fsclish) AND/OR LIMITED BASH SHELL.",
        "",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

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
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#",
    "options": None,
}

COMMAND_RESULT_resize_window = {
    'LINES': [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!",
        "Someone could be eavesdropping on you right now (man-in-the-middle attack)!",
        "It is also possible that a host key has just been changed.",
        "The fingerprint for the RSA key sent by the remote host is",
        "[...].",
        "Please contact your system administrator.",
        "Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.",
        "Offending RSA key in /home/you/.ssh/known_hosts:86",
        "RSA host key for host.domain.net has changed and you have requested strict checking.",
        "Host key verification failed.",
        # "client:~/>sh-keygen -R host.domain.net",
        # "client:~/>TERM=xterm-mono ssh -l user host.domain.net",
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Sun Jan  6 13:42:05 UTC+2 2019 on ttyAMA2",
        "7[r[999;999H[6n",
        "resize: unknown character, exiting.",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\""
    ],
    'LAST_LOGIN': {
        'KIND': 'on',
        'WHERE': 'ttyAMA2',
        'RAW_DATE': 'Sun Jan  6 13:42:05 UTC+2 2019',
        'DATE': parser.parse('Sun Jan  6 13:42:05 UTC+2 2019'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_options = """
client:~/>TERM=xterm-mono ssh -l user -o Interval=100 host.domain.net
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

COMMAND_KWARGS_options = {
    "login": "user", "password": "english", "known_hosts_on_failure": "keygen",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#",
    "options": "-o Interval=100"
}

COMMAND_RESULT_options = {
    'LINES': [
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @",
        "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
        "IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!",
        "Someone could be eavesdropping on you right now (man-in-the-middle attack)!",
        "It is also possible that a host key has just been changed.",
        "The fingerprint for the RSA key sent by the remote host is",
        "[...].",
        "Please contact your system administrator.",
        "Add correct host key in /home/you/.ssh/known_hosts to get rid of this message.",
        "Offending RSA key in /home/you/.ssh/known_hosts:86",
        "RSA host key for host.domain.net has changed and you have requested strict checking.",
        "Host key verification failed.",
        # "client:~/>sh-keygen -R host.domain.net",
        # "client:~/>TERM=xterm-mono ssh -l user host.domain.net",
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Sun Jan  6 13:42:05 UTC+2 2019 on ttyAMA2",
        "7[r[999;999H[6n",
        "resize: unknown character, exiting.",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\""
    ],
    'LAST_LOGIN': {
        'KIND': 'on',
        'WHERE': 'ttyAMA2',
        'RAW_DATE': 'Sun Jan  6 13:42:05 UTC+2 2019',
        'DATE': parser.parse('Sun Jan  6 13:42:05 UTC+2 2019'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_failure_exception = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
Password:
Notice: The use of this system is restricted to users who have been granted access.
You have new mail.
Last login: Tue Jul 23 13:59:25 2029 from 127.0.0.2
Could not chdir to home directory /home/user: Permission denied
Can't open display
-bash: /home/user/.bash_profile: Permission denied
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_failure_exception = {
    "login": "user", "password": "english", "known_hosts_on_failure": "keygen",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#", "options": None,
    "failure_exceptions_indication":
        r"/home/user/.bash_profile: Permission denied|Could not chdir to home directory /home/user: Permission denied",
}

COMMAND_RESULT_failure_exception = {
    'LINES': [
        "Password:",
        "Notice: The use of this system is restricted to users who have been granted access.",
        "You have new mail.",
        "Last login: Tue Jul 23 13:59:25 2029 from 127.0.0.2",
        "Could not chdir to home directory /home/user: Permission denied",
        "Can't open display",
        "-bash: /home/user/.bash_profile: Permission denied",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\""
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.2',
        'RAW_DATE': 'Tue Jul 23 13:59:25 2029',
        'DATE': parser.parse('Tue Jul 23 13:59:25 2029'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_OUTPUT_prompt_fingerprint = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
Do you want to continue (yes/no/[fingerprint])? yes
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1
There was 1 failed login attempts since the last successful login.
Have a lot of fun...
host:~ #
host:~ # export PS1="\\u$"
user$"""

COMMAND_KWARGS_prompt_fingerprint = {
    "login": "user", "password": "english", "set_prompt": r'export PS1="\\u$"',
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": r"host.*#|user\$",
    "options": None,
}

COMMAND_RESULT_prompt_fingerprint = {
    'LINES': [
        "Do you want to continue (yes/no/[fingerprint])? yes",
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Thu Nov 23 10:38:16 2017 from 127.0.0.1",
        'There was 1 failed login attempts since the last successful login.',
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export PS1=\"\\u$\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:38:16 2017',
        'DATE': parser.parse('Thu Nov 23 10:38:16 2017'),
    },
    'FAILED_LOGIN_ATTEMPTS': 1,
}

COMMAND_OUTPUT_wrong_date = """
client:~/>TERM=xterm-mono ssh -l user host.domain.net
To edit this message please edit /etc/ssh_banner
You may put information to /etc/ssh_banner who is owner of this PC
Password:
Last login: Thu Nov 23 10:78:16 2017 from 127.0.0.1
Have a lot of fun...
host:~ #
host:~ # export TMOUT="2678400"
host:~ #"""

COMMAND_KWARGS_wrong_date = {
    "login": "user", "password": "english",
    "host": "host.domain.net", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_RESULT_wrong_date = {
    'LINES': [
        "To edit this message please edit /etc/ssh_banner",
        "You may put information to /etc/ssh_banner who is owner of this PC",
        "Password:",
        "Last login: Thu Nov 23 10:78:16 2017 from 127.0.0.1",
        "Have a lot of fun...",
        "host:~ #",
        "host:~ # export TMOUT=\"2678400\"",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '127.0.0.1',
        'RAW_DATE': 'Thu Nov 23 10:78:16 2017',
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_KWARGS_pts0 = {
    "login": "user", "password": "pass", "set_timeout": None,
    "host": "10.0.1.67", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_OUTPUT_pts0 = """TERM=xterm-mono ssh -l user -o ServerAliveInterval=7 -o ServerAliveCountMax=2 10.0.1.67
Warning: Permanently added '10.0.1.67' (RSA) to the list of known hosts.
"You are about to access a private system. This system is for the use of authorized users only. All connections are logged to the extent and by means acceptable by the local legislation. Any unauthorized access or access attempts may be punished to the fullest extent possible under the applicable local legislation."
Password:
****

Last login: Fri Jul  3 11:50:03 CEST 2020 from 192.168.255.126 on pts/0
host:~ #"""

COMMAND_RESULT_pts0 = {
    'LINES': [
        r"Warning: Permanently added '10.0.1.67' (RSA) to the list of known hosts.",
        r'"You are about to access a private system. This system is for the use of authorized users only. All connections are logged to the extent and by means acceptable by the local legislation. Any unauthorized access or access attempts may be punished to the fullest extent possible under the applicable local legislation."',
        "Password:",
        "****",
        "",
        "Last login: Fri Jul  3 11:50:03 CEST 2020 from 192.168.255.126 on pts/0",
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '192.168.255.126',
        'RAW_DATE': 'Fri Jul  3 11:50:03 CEST 2020',
        'DATE': parser.parse('Fri Jul  3 11:50:03 CEST 2020'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_KWARGS_override_keygen = {
    "login": "user", "password": "pass", "set_timeout": None,
    "host": "10.0.1.67", "prompt": "client.*>", "expected_prompt": "host.*#"
}

COMMAND_OUTPUT_override_keygen = """TERM=xterm-mono ssh -l user -o ServerAliveInterval=7 -o ServerAliveCountMax=2 10.0.1.67
Offending ECDSA key in /home/ute/.ssh/known_hosts:17

remove with:

  ssh-keygen -f "/home/user/.ssh/known_hosts" -R "10.0.1.67"

Password authentication is disabled to avoid man-in-the-middle attacks.

Keyboard-interactive authentication is disabled to avoid man-in-the-middle attacks.

user@client: Permission denied (publickey,password,keyboard-interactive).
user@client: ssh-keygen -f "/home/user/.ssh/known_hosts" -R "10.0.1.67"
user@client: TERM=xterm-mono ssh -l user -o ServerAliveInterval=7 -o ServerAliveCountMax=2 10.0.1.67
Password:
****

Last login: Fri Jul  3 11:50:03 CEST 2020 from 192.168.255.126
user@host:~ #"""

COMMAND_RESULT_override_keygen = {
    'LINES': [
        r'Offending ECDSA key in /home/ute/.ssh/known_hosts:17',
        r'',
        r'remove with:',
        r'',
        r'  ssh-keygen -f "/home/user/.ssh/known_hosts" -R "10.0.1.67"',
        r'',
        r'Password authentication is disabled to avoid '
        r'man-in-the-middle attacks.',
        r'',
        r'Keyboard-interactive authentication is disabled to avoid '
        r'man-in-the-middle attacks.',
        r'',
        r'user@client: Permission denied '
        r'(publickey,password,keyboard-interactive).',
        r'Password:',
        r'****',
        r'',
        r'Last login: Fri Jul  3 11:50:03 CEST 2020 from 192.168.255.126'
    ],
    'LAST_LOGIN': {
        'KIND': 'from',
        'WHERE': '192.168.255.126',
        'RAW_DATE': 'Fri Jul  3 11:50:03 CEST 2020',
        'DATE': parser.parse('Fri Jul  3 11:50:03 CEST 2020'),
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}

COMMAND_KWARGS_tunnel = {
    "set_timeout": None, "host": None, "prompt": "moler_bash#", "expected_prompt": "moler_bash#",
    "password": 'pass',
    "suffix": r"-f -N -L 22:target.machine:22 user@proxy.machine $ scp target-user@local.machine:/remote/file -P 22 ."
}

COMMAND_OUTPUT_tunnel = """TERM=xterm-mono ssh -f -N -L 22:target.machine:22 user@proxy.machine $ scp target-user@local.machine:/remote/file -P 22 .
Password:
moler_bash#"""

COMMAND_RESULT_tunnel = {
    'LINES': [
        r'Password:',
    ],
    'LAST_LOGIN': {
    },
    'FAILED_LOGIN_ATTEMPTS': None,
}
