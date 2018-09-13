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
    def __init__(self, connection, host, password, user=None, confirm_connection=True, source_path=None,
                 destination_path=None, options=None, command=None, no_result=False, prompt=None, new_line_chars=None):
        super(Sftp, self).__init__(connection=connection, prompt=prompt, new_line_chars=new_line_chars)

        self.host = host
        self.user = user
        self.password = password
        self.confirm_connection = confirm_connection
        self.ready_to_parse_line = False

        self.source_path = source_path
        self.destination_path = destination_path

        self.options = options
        self.command = command
        self.no_result = no_result
        self._re_command_sent = re.compile(r"sftp> {}".format(self.command), re.I)
        self.connection_confirmed = False
        self.password_sent = False
        self.command_entered = False
        self.command_sent = False
        self.exit_sent = False
        self.sending_started = False
        print("INIT")

    def build_command_string(self):
        cmd = "sftp"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.user:
            cmd = "{} {}@{}".format(cmd, self.user, self.host)
        else:
            cmd = "{} {}".format(cmd, self.host)
        if self.source_path:
            cmd = "{}:{}".format(cmd, self.source_path)
        if self.destination_path:
            cmd = "{} {}".format(cmd, self.destination_path)
        return cmd

    def on_new_line(self, line, is_full_line):
        try:
            print("line:" + line)
            if is_full_line:
                self._check_if_command_sent(line)
            self._ignore_empty_or_repeated_line(line)
            self._confirm_connection(line)
            self._send_password(line)
            self._send_command_if_prompt(line)
            if is_full_line:
                self._check_if_connected(line)
                self._parse_line_fetching_uploading(line)
                self._authentication_failure(line)
                self._command_error(line)
                self._parse_line_from_prompt(line)
            print("On_new_line end, line not parsed: {}".format(line))
        except ParsingDone:
            print("in line {} ,current_ret: {}".format(line, str(self.current_ret)))
        super(Sftp, self).on_new_line(line, is_full_line)

    _re_prompt_with_command = re.compile(r"sftp>\s\w+", re.I)

    def _ignore_empty_or_repeated_line(self, line):
        if not line:
            print("useless...1 " + line)
            raise ParsingDone
        elif not line.strip():
            print("useless...2 " + line)
            raise ParsingDone

    _re_confirm_connection = re.compile(r"Are\syou\ssure\syou\swant\sto\scontinue\sconnecting\s\(yes/no\)\?", re.I)

    def _confirm_connection(self, line):
        if not self.connection_confirmed and self._regex_helper.search_compiled(Sftp._re_confirm_connection, line):
            print("confirmed:.... " + line)
            if self.confirm_connection:
                self.connection.sendline("yes")
            else:
                self.connection.sendline("no")
            self.connection_confirmed = True
            raise ParsingDone

    _re_password = re.compile(r"(?P<USER_HOST>.*)\spassword:", re.IGNORECASE)

    def _send_password(self, line):
        if not self.password_sent and self._regex_helper.search_compiled(Sftp._re_password, line):
            print("before sending password")
            self.connection.sendline(self.password)  # encrypt=True
            print("after sending password")
            self.password_sent = True
            raise ParsingDone

    def _check_if_command_sent(self, line):
        print("enter command_sent")
        if self.command_entered and self._regex_helper.match_compiled(self._re_command_sent, line):
            self.command_sent = True
            print("!!!!!!!!!!!!!!!!!!! command {} sent !!!!!!!!!!!!!!!!!".format(self.command))
            raise ParsingDone

    _re_prompt = re.compile(r"sftp>", re.I)

    def _send_command_if_prompt(self, line):
        if not self.command_sent and self._regex_helper.match_compiled(Sftp._re_prompt, line):
            print("line in send_command_if_prompt: " + line)
            self.connection.sendline(self.command)
            self.command_entered = True
            print("command {} entered".format(self.command))
            raise ParsingDone
        elif not self.exit_sent and self.command_sent and self._regex_helper.match_compiled(Sftp._re_prompt, line):
            print("line in send_command_if_prompt: " + line)
            print("!!! EXIT !!!")
            self.connection.sendline("exit")
            self.exit_sent = True
            raise ParsingDone
        elif self._regex_helper.match_compiled(Sftp._re_prompt, line):
            print("line in send_command_if_prompt: " + line)
            print("sftp prompt")
            raise ParsingDone

    _re_connected = re.compile(r"Connected\sto\s.+", re.I)

    def _check_if_connected(self, line):
        if self._regex_helper.search_compiled(Sftp._re_connected, line):
            print("connected:******* " + line)
            self.ready_to_parse_line = True
            raise ParsingDone

    _re_fetching = re.compile(r"(Fetching\s.*|Uploading\s.*)", re.I)
    _re_progress_bar = re.compile(r"(.+\s+\d{1,2}%\s+\d+\s+.+/s\s+(\d+:\d+)?--:--\sETA)", re.I)
    _re_success_bar = re.compile(r"(.+\s+100%\s+\d+\s+.+/s\s+\d+:\d+)", re.I)

    def _parse_line_fetching_uploading(self, line):
        if self.ready_to_parse_line:
            if self._regex_helper.search_compiled(Sftp._re_fetching, line):
                if not self.sending_started:
                    self.current_ret['RESULT'] = list()
                self.sending_started = True
                self.current_ret['RESULT'].append(line)
                print("fetching:... " + line)
                raise ParsingDone
            elif self.sending_started and self._regex_helper.search_compiled(Sftp._re_success_bar, line):
                self.current_ret['RESULT'].append(line)
                print("success bar... " + line)
                raise ParsingDone
            elif self.sending_started and self._regex_helper.search_compiled(Sftp._re_progress_bar, line):
                print("progress bar... " + line)
                raise ParsingDone
            elif self.sending_started:
                print("fetching error... \'{}\'".format(line))
                self.set_exception(CommandFailure(self, "ERROR: {}".format(line)))
                print("after fetching error " + line)
                raise ParsingDone

    def _parse_line_from_prompt(self, line):
        print("in parse line, command sent: " + str(self.command_sent))
        if self.ready_to_parse_line:
            if self.command_sent:
                if self.no_result:
                    self.set_result({})
                if 'RESULT' not in self.current_ret:
                    self.current_ret['RESULT'] = list()
                self.current_ret['RESULT'].append(line)
                print("inside parse from prompt" + str(self.current_ret))
                raise ParsingDone

    _re_resend_password = re.compile(r"(?P<RESEND>Permission\sdenied,\splease\stry\sagain)", re.I)
    _re_authentication = re.compile(r"(?P<AUTH>Authentication\sfailed.*)|(?P<PERM>.*Permission\sdenied.*)", re.I)

    def _authentication_failure(self, line):
        if self._regex_helper.search_compiled(Sftp._re_resend_password, line):
            self.password_sent = False
            raise ParsingDone
        elif self._regex_helper.search_compiled(Sftp._re_authentication, line):
            auth = self._regex_helper.group("AUTH")
            perm = self._regex_helper.group("PERM")
            self.set_exception(CommandFailure(self, "ERROR: {msg}".format(msg=auth if auth else perm)))
            print("AUTH ERROR")
            raise ParsingDone

    _error_regex_compiled = list()
    _error_regex_compiled.append(re.compile(r"(?P<NOT_FOUND>File.*not\sfound.*)", re.I))
    _error_regex_compiled.append(re.compile(r"(?P<NO_FILE>.*No\ssuch\sfile\sor\sdirectory.*)", re.I))
    _error_regex_compiled.append(re.compile(r"(?P<CONNECTION>Couldn't\sread\spacket:"
                                            r"\sConnection\sreset\sby\speer)", re.I))
    _error_regex_compiled.append(re.compile(r"(?P<OPTION>(unknown|invalid)\soption\s.*)", re.I))
    _error_regex_compiled.append(re.compile(r"(?P<SSH_ERROR>ssh:.+)", re.I))
    _re_help = re.compile(r"(?P<HELP_MSG>usage:\ssftp\s.*)", re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(Sftp._re_help, line):
            self.set_exception(CommandFailure(self, "ERROR: invalid command"))
            print("ERROR")
            raise ParsingDone
        for _re_error in Sftp._error_regex_compiled:
            if self._regex_helper.search_compiled(_re_error, line):
                self.set_exception(CommandFailure(self, "ERROR: {}".format(line)))
                print("ERROR")
                raise ParsingDone


COMMAND_OUTPUT = """xyz@debian:/home$ sftp fred@192.168.0.102:cat /home/xyz/Docs/cat
The authenticity of host '192.168.0.102 (192.168.0.102)' can't be established.
ECDSA key fingerprint is SHA256:ghQ3iy/gH4YTqZOggql1eJCe3EETOOpn5yANJwFeRt0.
Are you sure you want to continue connecting (yes/no)?
Warning: Permanently added '192.168.0.102' (ECDSA) to the list of known hosts.
fred@192.168.0.102's password:
Connected to 192.168.0.102.
Fetching /upload/cat to /home/xyz/Docs/cat
/upload/cat                                   100%   23    34.4KB/s   00:00
xyz@debian:/home$"""

COMMAND_KWARGS = {
    'host': '192.168.0.102',
    'user': 'fred',
    'source_path': 'cat',
    'destination_path': '/home/xyz/Docs/cat',
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
Host key verification failed.
xyz@debian:/home$"""

COMMAND_KWARGS_no_confirm_connection = {
    'host': '192.168.0.102',
    'user': 'fred',
    'source_path': 'cat',
    'destination_path': '/home/xyz/Docs/cat',
    'confirm_connection': False,
    'password': '1234',
    'no_result': True
}

COMMAND_RESULT_no_confirm_connection = {
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
sftp> put /home/xyz/Docs/echo/*.py
Uploading /home/xyz/Docs/echo/special_chars.py to /upload/special_chars.py
/home/xyz/Docs/echo/special_chars.py         100%   95   377.2KB/s   00:00
Uploading /home/xyz/Docs/echo/special_chars2.py to /upload/special_chars2.py
/home/xyz/Docs/echo/special_chars2.py         100%   26   17.2KB/s   00:00
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
               "/home/xyz/Docs/echo/special_chars2.py         100%   26   17.2KB/s   00:00"]
}


COMMAND_OUTPUT_mkdir = """xyz@debian:/home$ sftp fred@192.168.0.102:animals
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
fred@192.168.0.102's password:
Permission denied, please try again.
fred@192.168.0.102's password:
Connected to 192.168.0.102.
Changing to: /upload/animals
sftp>
sftp> mkdir pets
sftp>
xyz@debian:/home$"""

COMMAND_KWARGS_mkdir = {
    'host': '192.168.0.102',
    'user': 'fred',
    'password': '1234',
    'source_path': 'animals',
    'command': 'mkdir pets',
    'no_result': True
}

COMMAND_RESULT_mkdir = {
}
