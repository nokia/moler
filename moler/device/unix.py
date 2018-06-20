# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

from moler.device import Device


# TODO: name, logger/logger_name as param
class Unix(Device):
    def __init__(self, io_connection):
        """
        Create Unix device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        """
        super(Unix, self).__init__(io_connection=io_connection)

    def run(self, cmd_name='cd', **kwargs):
        """
        Wrapper for simple use:

        return ux.run('cd', path="/home/user/")

        Command/observer object is created locally
        """
        cmd = self.get_cmd(cmd_name=cmd_name, **kwargs)
        return cmd()

    def start(self, cmd_name='cd', **kwargs):
        """
        Wrapper for simple use:

        localhost_ping = ux.start('ping', destination="localhost", options="-c 5")
        ...
        result = localhost_ping.await_finish()

        result = await localhost_ping  # py3 notation

        Command/observer object is created locally
        """
        cmd = self.get_cmd(cmd_name=cmd_name, **kwargs)
        return cmd.start()
