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

                self._authentication_failure(line)
                self._file_error(line)
                self._connection_error(line)

                self._check_if_connected(line)
                self._send_command_if_prompt(line)
                self._parse_line(line)
                self._parse_line_from_prompt(line)
            except ParsingDone:
                pass
        super(Sftp, self).on_new_line(line, is_full_line)

    _re_confirm_connection = re.compile(r"Are\syou\ssure\syou\swant\sto\scontinue\sconnecting\s\(yes/no\)\?", re.I)

    def _confirm_connection(self, line):
        if self._regex_helper.search_compiled(Sftp._re_confirm_connection, line):
            if self.confirm_connection:
                self.connection.sendline("yes")
            else:
                self.connection.sendline("no")
            raise ParsingDone

    _re_password = re.compile(r"(?P<USER_HOST>.*)\spassword:", re.IGNORECASE)

    def _send_password(self, line):
        if self._regex_helper.search_compiled(Sftp._re_password, line):
            self.connection.sendline(self.password)
            raise ParsingDone

    _re_connected = re.compile(r"Connected\sto\s.+", re.I)

    def _check_if_connected(self, line):
        if self._regex_helper.search_compiled(Sftp._re_connected, line):
            self.ready_to_parse_line = True
            raise ParsingDone

    _re_prompt = re.compile(r"sftp>", re.I)

    def _send_command_if_prompt(self, line):
        if not self.command_sent and self._regex_helper.search_compiled(Sftp._re_prompt, line):
            self.connection.sendline(self.command)
            self.command_sent = True
            raise ParsingDone
        elif self.command_sent and self._regex_helper.search_compiled(Sftp._re_prompt, line):
            self.connection.sendline("exit")
            raise ParsingDone

    def _parse_line_from_prompt(self, line):
        if self.ready_to_parse_line:
            if self.command_sent:
                self.current_ret['RESULT'].append(line)

    _re_fetching = re.compile(r"(Fetching\s.*)", re.I)
    _re_progress_bar = re.compile(r"(.+\s+\d+%\s+\d+\s+.+\s+\d+:\d+)", re.I)

    def _parse_line(self, line):
        if self.ready_to_parse_line:
            if self._regex_helper.search_compiled(Sftp._re_fetching, line):
                self.sending_started = True
                raise ParsingDone
            elif self.sending_started and self._regex_helper.search_compiled(Sftp._re_progress_bar, line):
                raise ParsingDone
            elif self.sending_started:
                self.set_exception(CommandFailure(self, "ERROR: {}".format(line)))

    _re_resend_password = re.compile(r"(?P<RESEND>Permission\sdenied,\splease\stry\sagain)", re.I)
    _re_authentication = re.compile(r"(?P<AUTH>Authentication\sfailed.*)|(?P<PERM>Permission\sdenied\s.*)", re.I)

    def _authentication_failure(self, line):
        if self._regex_helper.search_compiled(Sftp._re_resend_password, line):
            raise ParsingDone
        elif self._regex_helper.search_compiled(Sftp._re_authentication, line):
            auth = self._regex_helper.group("AUTH")
            perm = self._regex_helper.group("PERM")
            self.set_exception(CommandFailure(self, "ERROR: {msg}".format(msg=auth if auth else perm)))
            raise ParsingDone

    _re_file_error = re.compile(r"(?P<NOT_FOUND>File.*not\sfound.*)|"
                                r"(?P<NO_FILE>.*No\ssuch\sfile\sor\sdirectory.*)", re.I)

    def _file_error(self, line):
        if self._regex_helper.search_compiled(Sftp._re_file_error, line):
            not_found = self._regex_helper.group("NOT_FOUND")
            no_file = self._regex_helper.group("NO_FILE")
            self.set_exception(CommandFailure(self, "ERROR: {msg}".format(msg=not_found if not_found else no_file)))
            raise ParsingDone

    _re_connection_error = re.compile(r"(?P<CONNECTION>Couldn't\sread\spacket:\sConnection\sreset\sby\speer)", re.I)

    def _connection_error(self, line):
        if self._regex_helper.search_compiled(Sftp._re_connection_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("CONNECTION"))))

    _re_unknown_option = re.compile(r"(?P<OPTION>(unknown|invalid)\soption\s.*)", re.I)
    _re_help_msg = re.compile(r"(?P<HELP_MSG>usage:\ssftp\s.*)", re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Sftp._re_unknown_option, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("OPTION"))))
            raise ParsingDone
        elif self._regex_helper.search_compiled(Sftp._re_help_msg, line):
            self.set_exception(CommandFailure(self, "ERROR: Invalid command syntax."))
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
    'RESULT': []
}


COMMAND_OUTPUT_no_confirm_connection = """xyz@debian:/home$ sftp fred@192.168.0.102:cat /home/xyz/Docs/cat
The authenticity of host '192.168.0.102 (192.168.0.102)' can't be established.
ECDSA key fingerprint is SHA256:ghQ3iy/gH4YTqZOggql1eJCe3EETOOpn5yANJwFeRt0.
Are you sure you want to continue connecting (yes/no)?
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
sftp> pwd
Remote working directory: /upload
sftp>
sftp> exit
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
sftp> put /home/xyz/Docs/echo/special_chars.py
Uploading /home/xyz/Docs/echo/special_chars.py to /upload/special_chars.py
/home/xyz/Docs/echo/special_chars.py         100%   95   377.2KB/s   00:00
sftp>
sftp> exit
xyz@debian:/home$"""

COMMAND_KWARGS_upload = {
    'host': '192.168.0.102',
    'user': 'fred',
    'password': '1234',
    'command': 'put /home/xyz/Docs/echo/special_chars.py'
}
COMMAND_RESULT_upload = {
    'RESULT': ["Uploading /home/xyz/Docs/echo/special_chars.py to /upload/special_chars.py",
               "/home/xyz/Docs/echo/special_chars.py         100%   95   377.2KB/s   00:00"]
}


COMMAND_OUTPUT_multiple_commands = """xyz@debian:/home$ sftp fred@192.168.0.102
fred@192.168.0.102's password:
Permission denied, please try again.
fred@192.168.0.102's password:
Connected to 192.168.0.102.
sftp>
sftp> mkdir pets
sftp>
sftp> exit
xyz@debian:/home$"""

COMMAND_KWARGS_multiple_commands = {
    'host': '192.168.0.102',
    'user': 'fred',
    'password': '1234',
    'command': 'mkdir pets'
}
COMMAND_RESULT_multiple_commands = {
    'RESULT': []
}
