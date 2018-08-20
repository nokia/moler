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
    def __init__(self, connection, host, user="", password="", pathname=None, new_pathname=None, options=None,
                 confirm_connection=True, command=None, prompt=None, new_line_chars=None):
        super(Sftp, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        self.host = host
        self.user = user
        self.password = password
        self.pathname = pathname
        self.new_pathname = new_pathname
        self.confirm_connection = confirm_connection

        self.options = options

        self.command = command
        self.ready_to_parse_line = False
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
                self._confirm_connection(line)
                self._send_password(line)
                self._authentication_failure(line)
                self._file_error(line)
                self._check_if_connected(line)
                self._send_command_if_prompt(line)
                self._parse_line(line)
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
        if self.command and self._regex_helper.search_compiled(Sftp._re_prompt, line):
            self.connection.sendline(self.command)
            self.command = None
            raise ParsingDone
        elif not self.command and self._regex_helper.search_compiled(Sftp._re_prompt, line):
            self.connection.sendline("exit")
            raise ParsingDone

    def _parse_line(self, line):
        if self.ready_to_parse_line:
            self.current_ret['RESULT'].append(line)
        raise ParsingDone

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
    'password': '1234'
}
COMMAND_RESULT_prompt = {
    'RESULT': ["Remote working directory: /upload"]
}
