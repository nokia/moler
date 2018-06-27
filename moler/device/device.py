# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import abc
import functools
import importlib
import inspect
import logging
import pkgutil

from moler.connection import get_connection
from moler.device.state_machine import StateMachine
from moler.exceptions import CommandWrongState, DeviceFailure, EventWrongState


# TODO: name, logger/logger_name as param
class Device(object):
    cmds = "cmds"
    events = "events"
    connected = "CONNECTED"
    not_connected = "NOT_CONNECTED"
    states = [connected, not_connected]

    goto_connected = "GOTO_CONNECTED"
    goto_not_connected = "GOTO_NOT_CONNECTED"
    goto_states_triggers = [goto_connected, goto_not_connected]

    transitions = [
        {'trigger': goto_connected, 'source': not_connected, 'dest': connected},
        {'trigger': goto_not_connected, 'source': connected, 'dest': not_connected}
    ]

    def __init__(self, io_connection=None, io_type=None, variant=None, states=[]):
        """
        Create Device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        """
        Device.states += states
        self.SM = StateMachine(model=self, states=Device.states, initial=Device.not_connected, auto_transitions=False,
                               queued=True)
        self.SM.add_transitions(Device.transitions)

        self.logger = logging.getLogger('moler.conn-observer')
        if io_connection:
            self.io_connection = io_connection
            # TODO what if not open?
            self.goto_state(Device.connected)
            self.io_connection.subscribe_on_connect(subscriber=self.call_on_connect)
        else:
            self.io_connection = get_connection(io_type=io_type, variant=variant)
            self.io_connection.subscribe_on_connect(subscriber=self.call_on_connect)
            self.io_connection.open()
        self.io_connection.subscribe_on_disconnect(subscriber=self.call_on_disconnect)
        self._cmds_in_states = dict()
        self._events_in_states = dict()
        self._feed_cmds_and_events_on_start()

    def __del__(self):
        self.io_connection.close()

    def get_state(self):
        return self.state

    def get_name(self):
        return self.io_connection.moler_connection.name

    def _set_state(self, state):
        self.logger.debug("Changing state from '%s' into '%s'" % (self.get_state, state))
        self.SM.set_state(state=state)

    def goto_state(self, state):
        current_state = self.get_state()

        if current_state == state:
            return
        self.logger.debug("Go to state '%s' from '%s'" % (state, current_state))
        change_state_method = None

        for goto_method in Device.goto_states_triggers:
            if "GOTO_{}".format(state) == goto_method:
                change_state_method = getattr(self, goto_method)

        if change_state_method:
            change_state_method(current_state, state)
        else:
            raise DeviceFailure(
                "Try to change state to incorrect state {}. Available states: {}".format(state, Device.states))

    def call_on_connect(self, connection):
        self._set_state(Device.connected)

    def call_on_disconnect(self, connection):
        self._set_state(Device.not_connected)

    @abc.abstractmethod
    def _get_packages_for_state(self, state, observable):
        """
        Returns list of packages (list of strings) for a given state
        :param state: state name
        :param observable: type of return packages - Device.events or Device.cmds
        :return: list of packages
        """
        return []  # Workaround for test_device.py test test_device_may_be_created_on_named_connection

    # Overload when more states
    def _get_available_states(self):
        """
        :return: List of all states for a device.
        """
        return Device.states

    def _load_cmds_from_package(self, package_name):
        available_cmds = dict()
        basic_module = importlib.import_module(package_name)
        for importer, modname, is_pkg in pkgutil.iter_modules(basic_module.__path__):
            module_name = "{}.{}".format(package_name, modname)
            module = importlib.import_module(module_name)
            for (cmd_class_name, cmd_module_name) in inspect.getmembers(module, inspect.isclass):
                if cmd_module_name.__module__ == module_name:
                    cmd_class_obj = getattr(module, cmd_class_name)
                    cmd_name = cmd_class_obj.registration_name
                    cmd_class = "{}.{}".format(module_name, cmd_class_name)

                    available_cmds.update({cmd_name: cmd_class})
        return available_cmds

    def _get_observable_in_state(self, observable_name, observable_type, **kwargs):
        """Return Observable object assigned to cmd_name of given device"""
        # TODO: return observable object wrapped in decorator mocking it's start()
        # TODO:  to check it it is starting in correct state (do it on flag)
        observable_of_device = []

        if observable_type == Device.cmds:
            observable_of_device = self._get_cmds_in_state(self.get_state())
        elif observable_type == Device.events:
            observable_of_device = self._get_events_in_state(self.get_state())

        if observable_name in observable_of_device:
            observable_splited = observable_of_device[observable_name].split('.')
            observable_module_name = ".".join(observable_splited[:-1])
            observable_class_name = observable_splited[-1]

            observable_module = importlib.import_module(observable_module_name)
            observable_class = getattr(observable_module, observable_class_name)
            observable = observable_class(connection=self.io_connection.moler_connection, **kwargs)

            return observable

        for_whom = "for '{}' command of {} device".format(observable_name, self.__class__.__name__)
        raise KeyError("Unknown {}-derived class to instantiate {}".format(observable_type, for_whom))

    def _get_cmd_in_state(self, cmd_name, **kwargs):
        return self._get_observable_in_state(observable_name=cmd_name, observable_type=Device.cmds, **kwargs)

    def _get_event_in_state(self, event_name, **kwargs):
        return self._get_observable_in_state(observable_name=event_name, observable_type=Device.events, **kwargs)

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

    def get_event(self, event_name, check_states=True, **kwargs):
        event = self._get_event_in_state(event_name, **kwargs)
        if check_states:
            org_fun = event._validate_start
            created_state = self.get_state()

            @functools.wraps(event._validate_start)
            def validate_device_state_before_cmd_start(*args, **kargs):
                current_state = self.get_state()
                if current_state == created_state:
                    ret = org_fun(*args, **kargs)
                    return ret
                else:
                    raise EventWrongState(event, created_state, current_state)

            event._validate_start = validate_device_state_before_cmd_start
        return event

    def run(self, cmd_name, **kwargs):
        """
        Wrapper for simple use:

        return ux.run('cd', path="/home/user/")

        Command/observer object is created locally
        """
        cmd = self.get_cmd(cmd_name=cmd_name, **kwargs)
        return cmd()

    def start(self, cmd_name, **kwargs):
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

    def _get_cmds_in_state(self, state):
        return self._cmds_in_states[state]

    def _get_events_in_state(self, state):
        return self._events_in_states[state]

    def _feed_cmds_and_events_for_state(self, state):
        cmds = dict()
        events = dict()

        for package_name in self._get_packages_for_state(state=state, observable=Device.cmds):
            cmds.update(self._load_cmds_from_package(package_name))
        for package_name in self._get_packages_for_state(state=state, observable=Device.events):
            events.update(self._load_cmds_from_package(package_name))

        return cmds, events

    def _feed_cmds_and_events_on_start(self):
        for state in self._get_available_states():
            self._cmds_in_states[state] = dict()
            self._events_in_states[state] = dict()

            cmds, events = self._feed_cmds_and_events_for_state(state)

            self._cmds_in_states[state].update(cmds)
            self._events_in_states[state].update(events)

    @classmethod
    def from_named_connection(cls, connection_name):
        io_conn = get_connection(name=connection_name)
        return cls(io_connection=io_conn)

    @classmethod
    def get_trigger_to_state(cls, state):
        trigger = "GOTO_{}".format(state)
        if trigger not in cls.goto_states_triggers:
            cls.goto_states_triggers += [trigger]
        return trigger
