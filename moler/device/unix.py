# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.device import Device
from threading import Lock


# TODO: name, logger/logger_name as param
class Unix(Device):
    unix = "UNIX"
    unix2 = "UNIX2"
    states = [unix, unix2]

    transitions = [
        {'trigger': Device.get_trigger_to_state(unix), 'source': Device.connected, 'dest': unix,
         'before': '_connect_to_remote_host'},
        {'trigger': Device.get_trigger_to_state(Device.connected), 'source': unix, 'dest': Device.connected,
         'before': '_exit_from_remote_host'}
    ]

    def __init__(self, io_connection=None, io_type=None, variant=None):
        """
        Create Unix device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        """
        super(Unix, self).__init__(io_connection=io_connection, io_type=io_type, variant=variant, states=Unix.states)
        self.SM.add_transitions(transitions=Unix.transitions)

        self._events = dict()
        self._events_lock = Lock()
        self._configurations = dict()

    def _get_packages_for_state(self, state, observable):
        if state == Unix.connected:
            available = {Unix.cmds: ['moler.cmd.unix'],
                         Unix.events: ['moler.events.unix']}
            return available[observable]
        elif state == Unix.unix:
            available = {Unix.cmds: ['moler.cmd.unix'],
                         Unix.events: ['moler.events.unix']}
            return available[observable]
        return []

    def _connect_to_remote_host(self, source_state, dest_state):
        configurations = self.get_configurations(dest_state)
        connection_type = configurations.pop("connection_type")
        self._events[dest_state] = []

        logout_event = self.get_event(event_name="wait4",
                                      detect_patterns=[
                                          r"Connection to .* closed.".format(configurations["host"])
                                      ],
                                      end_on_caught=False)

        logout_event.subscribe(callback=self._logout_callback,
                               callback_params={"source_state": source_state, "dest_state": dest_state})

        logout_event.start()
        self._events[dest_state].append(logout_event)

        cmd = self.get_cmd(cmd_name=connection_type, **configurations)
        cmd()

    def _exit_from_remote_host(self, current_state=None, dest_state=None):
        # Cancel run of observers when exiting current state
        if current_state in self._events.keys():
            while self._events[current_state]:
                event = self._events[current_state].pop(0)
                event.stop_observer()
                event.unsubscribe()

        cmd = self.get_cmd('exit')
        cmd()

    def _logout_callback(self, event, **kwargs):
        # Cancel run of observers when exiting current state
        dest_state = kwargs["dest_state"]
        source_state = kwargs["source_state"]
        current_state = self.get_state()

        if current_state == dest_state:
            event.cancel()
            event.unsubscribe()
            self._set_state(source_state)
            self._events[dest_state].remove(event)

    def get_configurations(self, state=None):
        if not (state is None):
            return self._configurations[state]
        else:
            return self._configurations

    def set_configurations(self, configurations):
        self._configurations = configurations
