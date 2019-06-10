# -*- coding: utf-8 -*-
"""
Passwd command module.
"""
import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'michal.ernst@nokia.com'


class Passwd(GenericUnixCommand):
    def __init__(self, connection, current_password, new_password, user=None, options=None,
                 encrypt_password_sending=True, newline_chars=None, runner=None):
        """
        Moler class of Unix command passwd.

        :param connection: moler connection to device, terminal when command is executed
        :param current_password: user current password
        :param new_password: user new password
        :param user: user to change password
        :param options: additional command parameters
        :param encrypt_password_sending:
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        """
        super(Passwd, self).__init__(connection=connection, newline_chars=newline_chars, runner=runner)
        self.user = user
        self.current_password = current_password
        self.new_password = new_password
        self.options = options

        self.current_password_sent = False
        self.new_password_sent = False
        self.retype_new_password_sent = False
        self.encrypt_password_sending = encrypt_password_sending

        self.cancel_cmd = False
        self.current_ret["PASSWORD_CHANGED"] = False

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "passwd"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.user:
            cmd = "{} {}".format(cmd, self.user)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parses the output of the command.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        try:
            if self.cancel_cmd:
                self._send_enters_to_cancel_cmd()
            self._parse_re_too_short_password(line)
            self._parse_too_simple_password(line)
            self._parse_error(line)
            self._parse_password_updated_successfully(line)
            self._parse_current_password(line)
            self._parse_new_password(line)
            self._parse_retype_new_password(line)
        except ParsingDone:
            pass
        return super(Passwd, self).on_new_line(line, is_full_line)

    # Current password:
    _re_current_password = re.compile(r'Current .* password:')

    def _parse_current_password(self, line):
        """
        Detect current password prompt.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        if self._regex_helper.search_compiled(Passwd._re_current_password, line) and not self.current_password_sent:
            self.connection.sendline(data=self.current_password, encrypt=self.encrypt_password_sending)
            self.current_password_sent = True
            raise ParsingDone

    # New password:
    _re_new_password = re.compile(r'New .* password:', re.IGNORECASE)

    def _parse_new_password(self, line):
        """
        Detect new password prompt.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        if self._regex_helper.search_compiled(Passwd._re_new_password, line) and not self.new_password_sent:
            self.connection.sendline(data=self.new_password, encrypt=self.encrypt_password_sending)
            self.new_password_sent = True
            raise ParsingDone

    # Retype new password:
    _re_retype_new_password = re.compile(r'Retype new .* password:')

    def _parse_retype_new_password(self, line):
        """
        Detect retype new password prompt.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        if self._regex_helper.search_compiled(Passwd._re_retype_new_password,
                                              line) and not self.retype_new_password_sent:
            self.connection.sendline(data=self.new_password, encrypt=self.encrypt_password_sending)
            self.retype_new_password_sent = True
            raise ParsingDone

    # Bad: new password is too simple
    _re_too_simple_password = re.compile(r'Bad: new password is too simple')

    def _parse_too_simple_password(self, line):
        """
        Parse too simple password error.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        if self._regex_helper.search_compiled(Passwd._re_too_simple_password, line):
            self.set_exception(CommandFailure(self, "New password is too simple."))

            self.cancel_cmd = True

    # You must choose a longer password
    _re_too_short_password = re.compile(r'You must choose a longer password')

    def _parse_re_too_short_password(self, line):
        """
        Parse too short password error.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        if self._regex_helper.search_compiled(Passwd._re_too_short_password, line):
            self.set_exception(CommandFailure(self, "New password is too short."))

            self.cancel_cmd = True
            raise ParsingDone

    # passwd: Authentication token manipulation error
    _re_passwd_error = re.compile(r"passwd: (?P<ERROR>.* error)")

    def _parse_error(self, line):
        """
        Parse another error.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        if self._regex_helper.search_compiled(Passwd._re_passwd_error, line):
            self.set_exception(CommandFailure(self, "Unexpected error: '{}'".format(self._regex_helper.group('ERROR'))))

            self.cancel_cmd = True
            raise ParsingDone

    # passwd: password updated successfully
    _re_password_updated_successfully = re.compile(r'passwd: password updated successfully')

    def _parse_password_updated_successfully(self, line):
        """
        Parse password updated successfully.

        :param line: Line from device.
        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        if self._regex_helper.search_compiled(Passwd._re_password_updated_successfully, line):
            self.current_ret["PASSWORD_CHANGED"] = True

            raise ParsingDone

    def _send_enters_to_cancel_cmd(self, ):
        """
        Send enter to cancel cmd.

        :return: Nothing but raises ParsingDone if all required commands are sent.
        """
        self.connection.sendline("")
        raise ParsingDone


COMMAND_OUTPUT_no_user = """user@host:~$: passwd
Changing password for user.
Current password:
New password:
Retype new password:
passwd: password updated successfully
user@host:~$"""

COMMAND_KWARGS_no_user = {
    "current_password": "old_password",
    "new_password": "new_password"
}

COMMAND_RESULT_no_user = {
    "PASSWORD_CHANGED": True
}

COMMAND_OUTPUT_with_user = """user@host:~$: passwd user
Changing password for user.
Current password:
New password:
Retype new password:
passwd: password updated successfully
user@host:~$"""

COMMAND_KWARGS_with_user = {
    "user": "user",
    "current_password": "old_password",
    "new_password": "new_password"
}

COMMAND_RESULT_with_user = {
    "PASSWORD_CHANGED": True
}
