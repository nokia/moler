# -*- coding: utf-8 -*-
"""
SFTP command module.
"""
__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class Sftp(GenericUnixCommand):
    def __init__(self, connection, host, user=None, password="", confirm_connection=True, pathname=None,
                 new_pathname=None, options=None, command=None, prompt=None, new_line_chars=None):
        super(Sftp, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        self.host = host
        self.user = user
        self.password = password
        self.confirm_connection = confirm_connection
        self.ready_to_parse_line = False

        self.pathname = pathname
        self.new_pathname = new_pathname

        self.options = options
        self.command = command

        self.command_sent = False
        self.sending_started = False

        self.current_ret['RESULT'] = list()

    def build_command_string(self):
        cmd = "sftp"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.user:
            cmd = "{} {}@{}".format(cmd, self.user, self.host)
        else:
            cmd = "{} {}".format(cmd, self.host)
        if self.pathname:
            cmd = "{}:{}".format(cmd, self.pathname)
        if self.new_pathname:
            cmd = "{} {}".format(cmd, self.new_pathname)
        return cmd

    def on_new_line(self, line, is_full_line):
        if is_full_line:
            try:
                self._command_error(line)

                self._confirm_connection(line)
                self._send_password(line)
                self._check_if_connected(line)

                self._send_command_if_prompt(line)
                self._parse_line_fetching_uploading(line)
                self._authentication_failure(line)

                self._parse_line_from_prompt(line)
            except ParsingDone:
                pass
        super(Sftp, self).on_new_line(line, is_full_line)

    _re_confirm_connection = re.compile(r"Are\syou\ssure\syou\swant\sto\scontinue\sconnecting\s\(yes/no\)\?", re.I)

    def _confirm_connection(self, line):
        if self._regex_helper.search_compiled(Sftp._re_confirm_connection, line):
            if self.confirm_connection:
                self.connection.sendline("yes")
                print("1")
            else:
                self.connection.sendline("no")
                print("2")
            raise ParsingDone

    _re_password = re.compile(r"(?P<USER_HOST>.*)\spassword:", re.IGNORECASE)

    def _send_password(self, line):
        if self._regex_helper.search_compiled(Sftp._re_password, line):
            self.connection.sendline(self.password)
            print("3")
            raise ParsingDone

    _re_connected = re.compile(r"Connected\sto\s.+", re.I)

    def _check_if_connected(self, line):
        if self._regex_helper.search_compiled(Sftp._re_connected, line):
            self.ready_to_parse_line = True
            print("4")
            raise ParsingDone

    _re_prompt = re.compile(r"sftp>", re.I)

    def _send_command_if_prompt(self, line):
        if not self.command_sent and self._regex_helper.search_compiled(Sftp._re_prompt, line):
            self.connection.sendline(self.command)
            self.command_sent = True
            print("5: command sent " + self.command)
            raise ParsingDone
        elif self.command_sent and self._regex_helper.search_compiled(Sftp._re_prompt, line):
            self.connection.sendline("exit")
            print("6: exit sent " + self.command)
            raise ParsingDone

    _re_fetching = re.compile(r"(Fetching\s.*|Uploading\s.*)", re.I)
    _re_progress_bar = re.compile(r"(.+\s+\d+%\s+\d+\s+.+/s\s+\d+:\d+)", re.I)

    def _parse_line_fetching_uploading(self, line):
        if self.ready_to_parse_line:
            print("7")
            if self._regex_helper.search_compiled(Sftp._re_fetching, line):
                self.sending_started = True
                self.current_ret['RESULT'].append(line)
                print("8")
                raise ParsingDone
            elif self.sending_started and self._regex_helper.search_compiled(Sftp._re_progress_bar, line):
                self.current_ret['RESULT'].append(line)
                print("9")
                raise ParsingDone
            elif self.sending_started and not self._regex_helper.search_compiled(Sftp._re_progress_bar, line):
                print("10")
                self.set_exception(CommandFailure(self, "ERROR: {}".format(line)))
                print("after 10")
                raise ParsingDone

    def _parse_line_from_prompt(self, line):
        if self.ready_to_parse_line:
            if self.command_sent:
                print("11")
                self.current_ret['RESULT'].append(line)

    _re_resend_password = re.compile(r"(?P<RESEND>Permission\sdenied,\splease\stry\sagain)", re.I)
    _re_authentication = re.compile(r"(?P<AUTH>Authentication\sfailed.*)|(?P<PERM>.*Permission\sdenied.*)", re.I)

    def _authentication_failure(self, line):
        if self._regex_helper.search_compiled(Sftp._re_resend_password, line):
            print("12")
            raise ParsingDone
        elif self._regex_helper.search_compiled(Sftp._re_authentication, line):
            auth = self._regex_helper.group("AUTH")
            perm = self._regex_helper.group("PERM")
            print("13")
            print(perm)
            self.set_exception(CommandFailure(self, "ERROR: {msg}".format(msg=auth if auth else perm)))
            print("14")
            raise ParsingDone

    _error_regex_compiled = list()
    _error_regex_compiled.append(re.compile(r"(?P<NOT_FOUND>File.*not\sfound.*)", re.I))
    _error_regex_compiled.append(re.compile(r"(?P<NO_FILE>.*No\ssuch\sfile\sor\sdirectory.*)", re.I))
    _error_regex_compiled.append(re.compile(r"(?P<CONNECTION>Couldn't\sread\spacket:"
                                            r"\sConnection\sreset\sby\speer)", re.I))
    _error_regex_compiled.append(re.compile(r"(?P<OPTION>(unknown|invalid)\soption\s.*)", re.I))
    _re_help = re.compile(r"(?P<HELP_MSG>usage:\ssftp\s.*)", re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Sftp._re_help, line):
            self.set_exception(CommandFailure(self, "ERROR: invalid command"))
        for _re_error in Sftp._error_regex_compiled:
            if self._regex_helper.search_compiled(_re_error, line):
                self.set_exception(CommandFailure(self, "ERROR: {}".format(line)))
                print("15")
                raise ParsingDone


COMMAND_OUTPUT = """xyz@debian:/home$ sftp fred@192.168.0.102:cat /home/xyz/Docs/cat
The authenticity of host '192.168.0.102 (192.168.0.102)' can't be established.
ECDSA key fingerprint is SHA256:ghQ3iy/gH4YTqZOggql1eJCe3EETOOpn5yANJwFeRt0.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '192.168.0.102' (ECDSA) to the list of known hosts.
fred@192.168.0.102's password:
Connected to 192.168.0.102.
Fetching /upload/cat to /home/xyz/Docs/cat
/upload/cat                                   100%   23    34.4KB/s   00:00
xyz@debian:/home$"""

COMMAND_KWARGS = {
    'host': '192.168.0.102',
    'user': 'fred',
    'pathname': 'cat',
    'new_pathname': '/home/xyz/Docs/cat',
    'password': '1234'
}

COMMAND_RESULT = {
    'RESULT': ["Fetching /upload/cat to /home/xyz/Docs/cat",
               "/upload/cat                                   100%   23    34.4KB/s   00:00"]
}


COMMAND_OUTPUT_no_confirm_connection = """xyz@debian:/home$ sftp fred@192.168.0.102:cat /home/xyz/Docs/cat
The authenticity of host '192.168.0.102 (192.168.0.102)' can't be established.
ECDSA key fingerprint is SHA256:ghQ3iy/gH4YTqZOggql1eJCe3EETOOpn5yANJwFeRt0.
Are you sure you want to continue connecting (yes/no)?
Are you sure you want to continue connecting (yes/no)? no
Host key verification failed.
xyz@debian:/home$"""

COMMAND_KWARGS_no_confirm_connection = {
    'host': '192.168.0.102',
    'user': 'fred',
    'pathname': 'cat',
    'new_pathname': '/home/xyz/Docs/cat',
    'confirm_connection': False,
    'password': '1234'
}

COMMAND_RESULT_no_confirm_connection = {
    'RESULT': []
}


COMMAND_OUTPUT_prompt = """xyz@debian:/home$ sftp fred@192.168.0.102
fred@192.168.0.102's password:
Connected to 192.168.0.102.
sftp>
Remote working directory: /upload
sftp>
xyz@debian:/home$"""

COMMAND_KWARGS_prompt = {
    'host': '192.168.0.102',
    'user': 'fred',
    'password': '1234',
    'command': 'pwd'
}

COMMAND_RESULT_prompt = {
    'RESULT': ["Remote working directory: /upload"]
}


COMMAND_OUTPUT_upload = """xyz@debian:/home$ sftp fred@192.168.0.102
fred@192.168.0.102's password:
Connected to 10.0.2.15.
sftp>
Uploading /home/xyz/Docs/echo/special_chars.py to /upload/special_chars.py
/home/xyz/Docs/echo/special_chars.py         100%   95   377.2KB/s   00:00
Uploading /home/xyz/Docs/echo/special_chars2.py to /upload/special_chars2.py
/home/xyz/Docs/echo/special_chars.py         100%   26   17.2KB/s   00:00
sftp>
xyz@debian:/home$"""

COMMAND_KWARGS_upload = {
    'host': '192.168.0.102',
    'user': 'fred',
    'password': '1234',
    'command': 'put /home/xyz/Docs/echo/*.py'
}

COMMAND_RESULT_upload = {
    'RESULT': ["Uploading /home/xyz/Docs/echo/special_chars.py to /upload/special_chars.py",
               "/home/xyz/Docs/echo/special_chars.py         100%   95   377.2KB/s   00:00",
               "Uploading /home/xyz/Docs/echo/special_chars2.py to /upload/special_chars2.py",
               "/home/xyz/Docs/echo/special_chars.py         100%   26   17.2KB/s   00:00"]
}


COMMAND_OUTPUT_mkdir = """xyz@debian:/home$ sftp fred@192.168.0.102:animals
fred@192.168.0.102's password:
Permission denied, please try again.
fred@192.168.0.102's password:
Connected to 192.168.0.102.
Changing to: /upload/animals
sftp>
sftp>
xyz@debian:/home$"""

COMMAND_KWARGS_mkdir = {
    'host': '192.168.0.102',
    'user': 'fred',
    'password': '1234',
    'pathname': 'animals',
    'command': 'mkdir pets'
}

COMMAND_RESULT_mkdir = {
    'RESULT': []
}
