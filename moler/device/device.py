# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""
import importlib
import inspect

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.connection import get_connection
from moler.exceptions import CommandWrongState
import functools
import pkgutil


# TODO: name, logger/logger_name as param
class Device(object):
    def __init__(self, io_connection=None, io_type=None, variant=None):
        """
        Create Device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        """
        if io_connection:
            self.io_connection = io_connection
        else:
            self.io_connection = get_connection(io_type=io_type, variant=variant)
            self.io_connection.open()
        self._current_state = ""

    def __del__(self):
        self.io_connection.close()

    def get_state(self):
        return self._current_state

    def _get_cmds_in_state(self, state):
        available_cmds = dict()
        basic_module = importlib.import_module(state)
        for importer, modname, is_pkg in pkgutil.iter_modules(basic_module.__path__):
            module_name = "{}.{}".format(state, modname)
            module = importlib.import_module(module_name)

            for (cmd_class_name, cmd_module_name) in inspect.getmembers(module, inspect.isclass):
                if cmd_module_name.__module__ == module_name:
                    cmd_class_obj = getattr(module, cmd_class_name)
                    cmd_name = cmd_class_obj.registration_name
                    cmd_class = "{}.{}".format(module_name, cmd_class_name)

                    available_cmds.update({cmd_name: cmd_class})
        return available_cmds

    def _get_cmd_in_state(self, cmd_name, **kwargs):
        """Return Command object assigned to cmd_name of given device"""
        # TODO: return command object wrapped in decorator mocking it's start()
        # TODO:  to check it it is starting in correct state (do it on flag)
        commands_of_device = self._get_cmds_in_state(self.get_state())
        if cmd_name in commands_of_device:
            cmd_splited = commands_of_device[cmd_name].split('.')
            cmd_module_name = ".".join(cmd_splited[:-1])
            cmd_class_name = cmd_splited[-1]

            cmd_module = importlib.import_module(cmd_module_name)
            cmd_class = getattr(cmd_module, cmd_class_name)
            cmd = cmd_class(connection=self.io_connection.moler_connection, **kwargs)

            return cmd
        for_whom = "for '{}' command of {} device".format(cmd_name, self.__class__.__name__)
        raise KeyError("Unknown Command-derived class to instantiate " + for_whom)

    def get_cmd(self, cmd_name, check_states=True, **kwargs):
        cmd = self._get_cmd_in_state(cmd_name, **kwargs)
        if check_states:
            org_fun = cmd._validate_start
            created_state = self.get_state()

            @functools.wraps(cmd._validate_start)
            def validate_device_state_before_cmd_start(*args, **kargs):
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
