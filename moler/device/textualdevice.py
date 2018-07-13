# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""
import traceback

from moler.cmd.commandtextualgeneric import CommandTextualGeneric

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import abc
import functools
import importlib
import inspect
import logging
import pkgutil
import time
import re

from moler.connection import get_connection
from moler.device.state_machine import StateMachine
from moler.exceptions import CommandWrongState, DeviceFailure, EventWrongState, DeviceChangeStateFailure


# TODO: name, logger/logger_name as param
class TextualDevice(object):
    cmds = "cmd"
    events = "event"

    connected = "CONNECTED"
    not_connected = "NOT_CONNECTED"

    def __init__(self, io_connection=None, io_type=None, variant=None):
        """
        Create Device communicating over io_connection
        CAUTION: Device owns (takes over ownership) of connection. It will be open when device "is born" and close when
        device "dies".

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: type of connection - tcp, udp, ssh, telnet, ...
        :param variant: connection implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
                        (if not given then default one is taken)
        """
        self.logger = logging.getLogger('moler.textualdevice')
        self.logger.setLevel(logging.DEBUG)
        self.states = []
        self.goto_states_triggers = []
        # Below line will modify self extending it with methods and atributes od StateMachine
        # For eg. it will add atribute self.state
        self.SM = StateMachine(model=self, states=self.states, initial=TextualDevice.not_connected,
                               auto_transitions=False,
                               queued=True)

        self._state_hops = {}
        self._state_prompts = {}
        self._prompts_events = {}

        self._prepare_transitions()
        self._prepare_state_hops()

        if io_connection:
            self.io_connection = io_connection
        else:
            self.io_connection = get_connection(io_type=io_type, variant=variant)
        self.io_connection.notify(callback=self.on_connection_made, when="connection_made")
        # TODO: Need test to ensure above sentence for all connection
        self.io_connection.open()
        self.io_connection.notify(callback=self.on_connection_lost, when="connection_lost")
        self._cmdnames_available_in_state = dict()
        self._eventnames_available_in_state = dict()

        self._collect_cmds_for_state_machine()
        self._collect_events_for_state_machine()
        self._prepare_state_prompts()
        self._run_prompts_observers()
        self._default_prompt = re.compile(r'^[^<]*[\$|%|#|>|~]\s*$')

    def calc_timeout_for_command(self, passed_timeout, configurations):
        command_timeout = None
        configuration_timeout = -1
        if "timeout" in configurations:
            configuration_timeout = float(configurations["timeout"])
        if passed_timeout <= 0 and configuration_timeout > 0:
            command_timeout = configuration_timeout
        elif passed_timeout > 0 and configuration_timeout <= 0:
            command_timeout = timeout
        elif passed_timeout > 0 and configuration_timeout > 0:
            command_timeout = passed_timeout
            if configuration_timeout < passed_timeout:
                command_timeout = configuration_timeout
        return command_timeout

    def _prepare_transitions(self):
        transitions = {
            TextualDevice.connected: {
                TextualDevice.not_connected: {
                    "action": [
                        "_open_connection"
                    ],
                },
            },
            TextualDevice.not_connected: {
                TextualDevice.connected: {
                    "action": [
                        "_close_connection"
                    ],
                },
            }
        }

        self._add_transitions(transitions=transitions)

    def _prepare_state_prompts(self):
        state_prompts = {
            TextualDevice.connected: r'bash-\d+\.*\d*',
        }

        self._state_prompts.update(state_prompts)

    def _prepare_state_hops(self):
        # both state are directly connected, no hops needed
        pass

    @classmethod
    def from_named_connection(cls, connection_name):
        io_conn = get_connection(name=connection_name)
        return cls(io_connection=io_conn)

    def __del__(self):
        self.io_connection.close()

    def _collect_cmds_for_state_machine(self):
        for state in self._get_available_states():
            self._cmdnames_available_in_state[state] = dict()

            cmds = self._collect_cmds_for_state(state)

            self._cmdnames_available_in_state[state].update(cmds)

    def _collect_events_for_state_machine(self):
        for state in self._get_available_states():
            self._eventnames_available_in_state[state] = dict()

            events = self._collect_events_for_state(state)

            self._eventnames_available_in_state[state].update(events)

    @property
    def current_state(self):
        return self.state

    @property
    def name(self):
        return self.io_connection.moler_connection.name

    def _set_state(self, state):
        if self.current_state != state:
            self.logger.debug("Changing state from '%s' into '%s'" % (self.current_state, state))
            self.SM.set_state(state=state)

    def goto_state(self, dest_state, timeout=-1):
        if self.current_state == dest_state:
            return
        self.logger.debug("Go to state '%s' from '%s'" % (dest_state, self.current_state))
        is_dest_state = False
        is_timeout = False
        start_time = time.time()
        next_stage_timeout = timeout
        while (not is_dest_state) and (not is_timeout):
            next_state = self._get_next_state(dest_state)
            self._trigger_change_state(next_state=next_state, timeout=next_stage_timeout)

            if self.current_state == dest_state:
                is_dest_state = True

            if timeout > 0:
                next_stage_timeout = timeout - (time.time() - start_time)
                if next_stage_timeout <= 0:
                    is_timeout = True

    def _get_next_state(self, dest_state):
        next_state = None
        if self.current_state in self._state_hops.keys():
            if dest_state in self._state_hops[self.current_state].keys():
                next_state = self._state_hops[self.current_state][dest_state]

        if not next_state:  # direct transition without hops
            next_state = dest_state

        return next_state

    def _trigger_change_state(self, next_state, timeout):
        self.logger.debug("Changing state from '%s' into '%s'" % (self.current_state, next_state))
        change_state_method = None
        # all state triggers used by SM are methods with names starting from "GOTO_"
        # for e.g. GOTO_REMOTE, GOTO_CONNECTED
        for goto_method in self.goto_states_triggers:
            if "GOTO_{}".format(next_state) == goto_method:
                change_state_method = getattr(self, goto_method)

        if change_state_method:
            try:
                change_state_method(self.current_state, next_state, timeout=timeout)
            except Exception as ex:
                ex_traceback = traceback.format_exc()
                raise DeviceChangeStateFailure(device=self.__class__.__name__, exception=ex_traceback)

            self.logger.debug("Successfully enter state '{}'".format(next_state))
        else:
            raise DeviceFailure(
                "Try to change state to incorrect state {}. Available states: {}".format(next_state, self.states))

    def on_connection_made(self, connection):
        self._set_state(TextualDevice.connected)

    def on_connection_lost(self, connection):
        self._set_state(TextualDevice.not_connected)

    @abc.abstractmethod
    def _get_packages_for_state(self, state, observer):
        """
        Returns list of packages (list of strings) for a given state
        :param state: state name
        :param observer: type of return packages - Device.events or Device.cmds
        :return: list of packages
        """
        return []  # Workaround for test_device.py test test_device_may_be_created_on_named_connection

    # Overload when more states
    def _get_available_states(self):
        """
        :return: List of all states for a device.
        """
        return self.states

    def _load_cmds_from_package(self, package_name):
        available_cmds = dict()
        basic_module = importlib.import_module(package_name)
        for importer, modname, is_pkg in pkgutil.iter_modules(basic_module.__path__):
            module_name = "{}.{}".format(package_name, modname)
            module = importlib.import_module(module_name)
            for (cmd_class_name, cmd_module_name) in inspect.getmembers(module, inspect.isclass):
                if cmd_module_name.__module__ == module_name:
                    cmd_class_obj = getattr(module, cmd_class_name)
                    # like:  IpAddr --> ip_addr
                    cmd_name = cmd_class_obj.observer_name
                    # like:  IpAddr --> moler.cmd.unix.ip_addr.IpAddr
                    cmd_class_fullname = "{}.{}".format(module_name, cmd_class_name)

                    available_cmds.update({cmd_name: cmd_class_fullname})
        return available_cmds

    def _get_observer_in_state(self, observer_name, observer_type, **kwargs):
        """Return Observable object assigned to obserber_name of given device"""
        # TODO: return observer object wrapped in decorator mocking it's start()
        # TODO:  to check it it is starting in correct state (do it on flag)
        available_observer_names = []

        if observer_type == TextualDevice.cmds:
            available_observer_names = self._cmdnames_available_in_state[self.current_state]
        elif observer_type == TextualDevice.events:
            available_observer_names = self._eventnames_available_in_state[self.current_state]

        if observer_name in available_observer_names:
            # TODO: GL refactor to instance_loader
            observer_splited = available_observer_names[observer_name].split('.')
            observer_module_name = ".".join(observer_splited[:-1])
            observer_class_name = observer_splited[-1]

            observer_module = importlib.import_module(observer_module_name)
            observer_class = getattr(observer_module, observer_class_name)
            observer = observer_class(connection=self.io_connection.moler_connection, **kwargs)

            return observer

        raise KeyError(
            "Failed to create {}-object for '{}' {}. '{}' {} is unknown for state '{}' of device '{}'.".format(
                observer_type, observer_name, observer_type, observer_name, observer_type, self.current_state,
                self.__class__.__name__))

    def _create_cmd_instance(self, cmd_name, **kwargs):
        """
        CAUTION: it checks if cmd may be created in current_state of device
        """
        return self._get_observer_in_state(observer_name=cmd_name, observer_type=TextualDevice.cmds, **kwargs)

    def _create_event_instance(self, event_name, **kwargs):
        """
        CAUTION: it checks if event may be created in current_state of device
        """
        return self._get_observer_in_state(observer_name=event_name, observer_type=TextualDevice.events, **kwargs)

    def get_observer(self, observer_name, observer_type, observer_exception, check_state=True, **kwargs):
        observer = None
        if observer_type == TextualDevice.cmds:
            observer = self._create_cmd_instance(observer_name, **kwargs)
        elif observer_type == TextualDevice.events:
            observer = self._create_event_instance(observer_name, **kwargs)

        if check_state:
            original_fun = observer._validate_start
            creation_state = self.current_state

            @functools.wraps(observer._validate_start)
            def validate_device_state_before_observer_start(*args, **kargs):
                current_state = self.current_state
                if current_state == creation_state:
                    ret = original_fun(*args, **kargs)
                    return ret
                else:
                    raise observer_exception(observer, creation_state, current_state)

            observer._validate_start = validate_device_state_before_observer_start
        return observer

    def get_cmd(self, cmd_name, check_state=True, **kwargs):
        if "prompt" not in kwargs:
            kwargs["prompt"] = self.get_prompt()
        cmd = self.get_observer(observer_name=cmd_name, observer_type=TextualDevice.cmds,
                                observer_exception=CommandWrongState, check_state=check_state, **kwargs)
        assert isinstance(cmd, CommandTextualGeneric)
        return cmd

    def get_event(self, event_name, check_state=True, **kwargs):
        event = self.get_observer(observer_name=event_name, observer_type=TextualDevice.events,
                                  observer_exception=EventWrongState, check_state=check_state, **kwargs)

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

    def _collect_observer_for_state(self, observer_type, state):
        observer = dict()

        for package_name in self._get_packages_for_state(state=state, observer=observer_type):
            observer.update(self._load_cmds_from_package(package_name))

        return observer

    def _collect_cmds_for_state(self, state):
        cmds = self._collect_observer_for_state(observer_type=TextualDevice.cmds, state=state)

        return cmds

    def _collect_events_for_state(self, state):
        events = self._collect_observer_for_state(observer_type=TextualDevice.events, state=state)

        return events

    def _add_transitions(self, transitions):
        for source_state in transitions.keys():
            for dest_state in transitions[source_state].keys():
                self._update_SM_states(dest_state)

                single_transition = [
                    {'trigger': self.build_trigger_to_state(dest_state),
                     'source': source_state,
                     'dest': dest_state,
                     'before': transitions[source_state][dest_state]["action"]},
                ]

                self.SM.add_state(dest_state)
                self.SM.add_transitions(single_transition)

    def _update_SM_states(self, state):
        if state not in self.states:
            self.states.append(state)

    def _open_connection(self, source_state, dest_state, timeout):
        self.io_connection.open()

    def _close_connection(self, source_state, dest_state, timeout):
        self.io_connection.close()

    def _prompt_observer_callback(self, event, state):
        self._set_state(state)

    def _run_prompts_observers(self):
        for state in self._state_prompts.keys():
            prompt_event = self.get_event(event_name="wait4prompt",
                                          prompt=self._state_prompts[state],
                                          till_occurs_times=-1)

            prompt_event_callback = functools.partial(self._prompt_observer_callback, event=prompt_event, state=state)
            prompt_event.add_event_occurred_callback(callback=prompt_event_callback)

            prompt_event.start()
            self._prompts_events[state] = prompt_event

    def build_trigger_to_state(self, state):
        trigger = "GOTO_{}".format(state)
        if trigger not in self.goto_states_triggers:
            self.goto_states_triggers += [trigger]
        return trigger

    def get_prompt(self):
        state = self.current_state
        prompt = self._default_prompt
        if state in self._state_prompts:
            prompt = self._state_prompts[state]
            if not hasattr(prompt, "match"):
                prompt = re.compile(prompt)
        return prompt
