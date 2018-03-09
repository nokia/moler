# -*- coding: utf-8 -*-
"""
ps command module.
"""
from moler.command import Command

__author__ = 'Dariusz Rosinski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'dariusz.rosinski@nokia.com'


class Ps(Command):
    def __init__(self, connection=None):
        pass

    def data_received(self):
        pass

    def on_prepare_run(self):
        pass

    def on_new_line(self):
        pass

    def get_final_timeout(self):
        pass

    def get_pid_to_name(self):
        pass

    def get_pids(self):
        pass
