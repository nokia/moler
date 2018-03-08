"""
:copyright: Nokia Networks
:author: Marcin Usielski
:contact: marcin.usielski@nokia.com
:maintainer:
"""

from command.regexhelper import RegexHelper
from moler.command import Command
import re


class GenericUnix(Command):
    _reg_fail = re.compile(
        r'command not found|No such file or directory|running it may require superuser privileges')

    def __init__(self, connection):
        super(GenericUnix, self).__init__(connection)
        self.ret = dict()
        self._cmd_escaped = None
        self._cmd_matched = False
        self._stored_status = None
        self._status = None
        self._regex_helper = RegexHelper()
        self.ret_required = True
        self.break_on_timeout = True
        self._last_not_full_line = None

        self._reg_prompt = re.compile(r'^[^<]*[\$|%|#|>|~]\s*$')

    def data_received(self, data):
        lines = data.splitlines(True)
        for line in lines:
            if self._last_not_full_line is not None:
                line = self._last_not_full_line + line
            self.on_new_line(line)
            if line.endswith(("\n", "\r")):
                self._last_not_full_line = None
            else:
                self._last_not_full_line = line

    def start(self, *args, **kwargs):
        return super(GenericUnix, self).start(args, kwargs)

    def get_cmd(self, cmd=None):
        pass

    def on_new_line(self, line):
        if not self._cmd_matched and (self._regex_helper.search(self._cmd_escaped, line)):
            self._cmd_matched = True
        elif self._cmd_matched and (self._stored_status is None) and (
                self._regex_helper.search_compiled(GenericUnix._reg_fail, line)):
            self.set_exception(Exception("command failed in line '%s'" % (line)))
        elif self._cmd_matched and (self._regex_helper.search_compiled(self._reg_prompt, line)):
            if self._stored_status:
                if (self.ret_required and self.is_ret()) or not self.ret_required:
                    if not self.done():
                        self.set_result(self.ret)
                else:
                    #print("Found candidate for final prompt but ret is undef, required not undef.")
                    pass
            else:
                if (self.ret_required and self.is_ret()) or not self.ret_required:
                    if not self.done():
                        self.set_result(self.ret)
                else:
                    #print("Found candidate for final prompt but ret is undef, required not undef.")
                    pass

    def has_cmd_run(self):
        return self._cmd_matched

    def break_cmd(self):
        self.connection.send("\x03")# ctrl+c

    def cancel(self):
        self.break_cmd()
        return super(GenericUnix, self).cancel()

    def on_timeout(self):
        if self.break_on_timeout:
            self.break_cmd()

    def is_ret(self):
        is_ret = False
        if self.ret:
            is_ret = True
        return is_ret

