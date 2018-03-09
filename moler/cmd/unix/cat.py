# -*- coding: utf-8 -*-
"""
Cat command module.
"""
from moler.cmd.unix.genericunix import GenericUnix

__author__ = 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.plichta@nokia.com'


class Cat(GenericUnix):
    def __init__(self, connection, file=None):
        super(Cat, self).__init__(connection)
        self.file = file

    def data_received(self, data):
        super(Cat, self).data_received(data)

    def start(self, *args, **kwargs):
        return super(Cat, self).start(*args, **kwargs)

    def get_cmd(self, cmd=None):
        super(Cat, self).get_cmd(cmd)

    def on_new_line(self, line):
        super(Cat, self).on_new_line(line)

    def has_cmd_run(self):
        return super(Cat, self).has_cmd_run()

    def break_cmd(self):
        super(Cat, self).break_cmd()

    def cancel(self):
        return super(Cat, self).cancel()

    def on_timeout(self):
        super(Cat, self).on_timeout()

    def is_ret(self):
        return super(Cat, self).is_ret()
