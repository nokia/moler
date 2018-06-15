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
from moler.cmd.unix.cd import Cd

# hardcode factory-registry for now.
# TODO Future: make it dynamic import or alike to not touch this class when new cmd is created
commands_of_device = {
    'cd': Cd,
}


# TODO: name, logger/logger_name as param
class Unix(Device):
    def __init__(self, io_connection):
        """
        Create Unix device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        """
        super(Unix, self).__init__(io_connection=io_connection)

    def get_cmd(self, cmd_name, **kwargs):
        """Return Command object assigned to cmd_name of given device"""
        # TODO: return command object wrapped in decorator mocking it's start()
        # TODO:  to check it it is starting in correct state (do it on flag)
        if cmd_name in commands_of_device:
            cmd_class = commands_of_device[cmd_name]  # load from factory/registry
            cmd = cmd_class(connection=self.io_connection.moler_connection, **kwargs)
            return cmd
        for_whom = "for '{}' command of {} device".format(cmd_name, self.__class__.__name__)
        raise KeyError("Unknown Command-derived class to instantiate " + for_whom)

    def get_observer(self, observer_name, **kwargs):
        """Return ConnectionObserver object assigned to observer_name of given device"""
        raise NotImplemented

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
