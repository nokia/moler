# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.connection import get_connection
from moler.exceptions import CommandWrongState
import functools


# TODO: name, logger/logger_name as param
class Device(object):
    def __init__(self, io_connection):
        """
        Create Device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        """
        self.io_connection = io_connection
        self._current_state = ""

    def get_state(self):
        return self._current_state

    def _get_cmds_in_state(self, state):
        return dict()

    def _get_cmd_in_state(self, cmd_name, **kwargs):
        """Return Command object assigned to cmd_name of given device"""
        # TODO: return command object wrapped in decorator mocking it's start()
        # TODO:  to check it it is starting in correct state (do it on flag)
        commands_of_device = self._get_cmds_in_state(self.get_state())
        if cmd_name in commands_of_device:
            cmd_class = commands_of_device[cmd_name]  # load from factory/registry
            cmd = cmd_class(connection=self.io_connection.moler_connection, **kwargs)
            return cmd
        for_whom = "for '{}' command of {} device".format(cmd_name, self.__class__.__name__)
        raise KeyError("Unknown Command-derived class to instantiate " + for_whom)

    def get_cmd(self, cmd_name, check_states=True, **kwargs):
        cmd = self._get_cmd_in_state(cmd_name, kwargs)
        if check_states:
            org_fun = cmd._validate_start
            created_state = self.get_state()

            @functools.wraps(cmd._validate_start)
            def validate_device_state_before_cmd_start(*args, **kargs):
                print "get_cmd::Device validate"
                current_state = self.get_state()
                if current_state == created_state:
                    ret = org_fun(*args, **kargs)
                    return ret
                else:
                    raise CommandWrongState(cmd, created_state, current_state)

            cmd._validate_start = validate_device_state_before_cmd_start
        return cmd

    def get_observer(self, observer_name, **kwargs):
        """Return ConnectionObserver object assigned to observer_name of given device"""
        raise NotImplemented

    @classmethod
    def from_named_connection(cls, connection_name):
        io_conn = get_connection(name=connection_name)
        return cls(io_connection=io_conn)
