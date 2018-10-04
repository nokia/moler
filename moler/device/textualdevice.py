# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""
import logging
import traceback

from moler.cmd.commandtextualgeneric import CommandTextualGeneric
from moler.config.loggers import configure_device_logger

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import functools
import importlib
import inspect
import pkgutil
import time
import re
import abc

from moler.connection import get_connection
from moler.device.state_machine import StateMachine
from moler.exceptions import CommandWrongState, DeviceFailure, EventWrongState, DeviceChangeStateFailure


# TODO: name, logger/logger_name as param
class TextualDevice(object):
    cmds = "cmd"
    events = "event"

    not_connected = "NOT_CONNECTED"
    connection_hops = "CONNECTION_HOPS"

    def __init__(self, name=None, io_connection=None, io_type=None, variant=None, sm_params=dict()):
        """
        Create Device communicating over io_connection
        CAUTION: Device owns (takes over ownership) of connection. It will be open when device "is born" and close when
        device "dies".

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: type of connection - tcp, udp, ssh, telnet, ...
        :param variant: connection implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
                        (if not given then default one is taken)
        """
        self.states = []
        self.goto_states_triggers = []
        self._name = name
        self.device_data_logger = None

        # Below line will modify self extending it with methods and atributes od StateMachine
        # For eg. it will add attribute self.state
        self.SM = StateMachine(model=self, states=self.states, initial=TextualDevice.not_connected,
                               auto_transitions=False,
                               queued=True)

        self._state_hops = {}
        self._state_prompts = {}
        self._prompts_events = {}
        self._configurations = dict()

        self._prepare_transitions()
        self._prepare_state_hops()
        self._configure_state_machine(sm_params)

        if io_connection:
            self.io_connection = io_connection
        else:
            self.io_connection = get_connection(io_type=io_type, variant=variant)

        self.io_connection.name = self.name
        self.io_connection.moler_connection.name = self.name
        self.logger = logging.getLogger('moler.connection.{}'.format(self.name))
        self.configure_logger(name=self.name, propagate=False)
        self.io_connection.notify(callback=self.on_connection_made, when="connection_made")
        # TODO: Need test to ensure above sentence for all connection
        self.io_connection.open()
        self.io_connection.notify(callback=self.on_connection_lost, when="connection_lost")
        self._cmdnames_available_in_state = dict()
        self._eventnames_available_in_state = dict()

        self._collect_cmds_for_state_machine()
        self._collect_events_for_state_machine()
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
            command_timeout = passed_timeout
        elif passed_timeout > 0 and configuration_timeout > 0:
            command_timeout = passed_timeout
            if configuration_timeout < passed_timeout:
                command_timeout = configuration_timeout
        return command_timeout

    def configure_logger(self, name, propagate):
        if not self.device_data_logger:
            self.device_data_logger = configure_device_logger(connection_name=name, propagate=propagate)

        self.io_connection.moler_connection.set_data_logger(self.device_data_logger)

    @abc.abstractmethod
    def _prepare_transitions(self):
        pass

    @abc.abstractmethod
    def _prepare_state_prompts(self):
        pass

    @abc.abstractmethod
    def _prepare_state_hops(self):
        pass

    @classmethod
    def from_named_connection(cls, connection_name):
        io_conn = get_connection(name=connection_name)
        return cls(io_connection=io_conn)

    def __del__(self):
        self._stop_prompts_observers()

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
        if self._name:
            return self._name
        else:
            return self.io_connection.moler_connection.name

    @name.setter
    def name(self, value):
        self._name = value

    def _log(self, level, msg, extra=None):
        if self.logger:
            extra_params = {
                'log_name': self.name
            }

            if extra:
                extra_params.update(extra)

            self.logger.log(level, msg, extra=extra_params)

        self.device_data_logger.log(level, msg)

    def _set_state(self, state):
        if self.current_state != state:
            self._log(logging.INFO, "Changed state from '%s' into '%s'" % (self.current_state, state))
            self.SM.set_state(state=state)

    def goto_state(self, state, timeout=-1, rerun=0, send_enter_after_changed_state=False):
        dest_state = state

        if self.current_state == dest_state:
            return

        self._log(logging.DEBUG, "Go to state '%s' from '%s'" % (dest_state, self.current_state))

        is_dest_state = False
        is_timeout = False
        start_time = time.time()
        next_stage_timeout = timeout

        while (not is_dest_state) and (not is_timeout):
            next_state = self._get_next_state(dest_state)
            self._trigger_change_state(next_state=next_state, timeout=next_stage_timeout, rerun=rerun,
                                       send_enter_after_changed_state=send_enter_after_changed_state)

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

    def _trigger_change_state(self, next_state, timeout, rerun, send_enter_after_changed_state):
        self._log(logging.DEBUG, "Changing state from '%s' into '%s'" % (self.current_state, next_state))
        change_state_method = None
        entered_state = False
        retrying = 0
        # all state triggers used by SM are methods with names starting from "GOTO_"
        # for e.g. GOTO_REMOTE, GOTO_CONNECTED
        for goto_method in self.goto_states_triggers:
            if "GOTO_{}".format(next_state) == goto_method:
                change_state_method = getattr(self, goto_method)

        if change_state_method:
            while (retrying <= rerun) and (not entered_state):
                try:
                    change_state_method(self.current_state, next_state, timeout=timeout)

                    if send_enter_after_changed_state:
                        self._send_enter_after_changed_state()

                    entered_state = True
                except Exception as ex:
                    if retrying == rerun:
                        ex_traceback = traceback.format_exc()
                        exc = DeviceChangeStateFailure(device=self.__class__.__name__, exception=ex_traceback)
                        self._log(logging.ERROR, exc)
                        raise exc
                    else:
                        retrying += 1
                        self._log(logging.DEBUG, "Cannot change state into '{}'. "
                                                 "Retrying '{}' of '{}' times.".format(next_state, retrying, rerun))

                        if send_enter_after_changed_state:
                            self._send_enter_after_changed_state()

            self._log(logging.DEBUG, "Successfully enter state '{}'".format(next_state))
        else:
            exc = DeviceFailure(
                device=self.__class__.__name__,
                message="Failed to change state to '{}'. "
                        "Either target state does not exist in SM or there is no direct/indirect transition "
                        "towards target state. Try to change state machine definition. "
                        "Available states: {}".format(next_state, self.states))
            self._log(logging.ERROR, exc)
            raise exc

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

        exc = DeviceFailure(
            device=self.__class__.__name__,
            message="Failed to create {}-object for '{}' {}. '{}' {} is unknown for state '{}' of device '{}'. Available names: {}".format(
                observer_type, observer_name, observer_type, observer_name, observer_type, self.current_state,
                self.__class__.__name__, available_observer_names))
        self._log(logging.ERROR, exc)
        raise exc

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
                    exc = observer_exception(observer, creation_state, current_state)
                    self._log(logging.ERROR, exc)
                    raise exc

            observer._validate_start = validate_device_state_before_observer_start
        return observer

    def get_cmd(self, cmd_name, cmd_params={}, check_state=True):
        if "prompt" not in cmd_params:
            cmd_params["prompt"] = self.get_prompt()
        cmd = self.get_observer(observer_name=cmd_name, observer_type=TextualDevice.cmds,
                                observer_exception=CommandWrongState, check_state=check_state, **cmd_params)
        assert isinstance(cmd, CommandTextualGeneric)
        return cmd

    def get_event(self, event_name, event_params={}, check_state=True):
        event = self.get_observer(observer_name=event_name, observer_type=TextualDevice.events,
                                  observer_exception=EventWrongState, check_state=check_state, **event_params)

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
                     'prepare': transitions[source_state][dest_state]["action"]},
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
            prompt_event = self.get_event(
                event_name="wait4prompt",
                event_params={
                    "prompt": self._state_prompts[state],
                    "till_occurs_times": -1
                }
            )

            prompt_event_callback = functools.partial(self._prompt_observer_callback, event=prompt_event, state=state)
            prompt_event.add_event_occurred_callback(callback=prompt_event_callback)

            prompt_event.start()
            self._prompts_events[state] = prompt_event

    def _stop_prompts_observers(self):
        for device_state in self._prompts_events:
            self._prompts_events[device_state].cancel()
            self._prompts_events[device_state].remove_event_occurred_callback()

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

    def _configure_state_machine(self, sm_params):
        default_configurations = self._get_default_sm_configuration()
        configuration = self._update_configuration(default_configurations, sm_params)
        self._configurations = configuration
        self._validate_device_configuration()
        self._prepare_state_prompts()

    def _update_configuration(self, destination, source):
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                self._update_configuration(value, node)
            else:
                destination[key] = value

        return destination

    def _get_default_sm_configuration(self):
        return {TextualDevice.connection_hops: {}}

    def get_configurations(self, source_state, dest_state):
        if source_state and dest_state:
            return self._configurations[TextualDevice.connection_hops][source_state][dest_state]

    def _validate_device_configuration(self):
        exception_message = ""
        configuration = self._configurations[TextualDevice.connection_hops]

        for source_state in configuration.keys():
            for dest_state in configuration[source_state].keys():
                if "required_command_params" in configuration[source_state][dest_state].keys():
                    for required_command_param in configuration[source_state][dest_state]["required_command_params"]:
                        if required_command_param not in configuration[source_state][dest_state]["command_params"]:
                            exception_message += "\n'{}' in 'command_params' in transition from '{}' to '{}'".format(
                                required_command_param, source_state, dest_state)

        if exception_message:
            exc = DeviceFailure(device=self.__class__.__name__,
                                message="Missing required parameter(s). There is no required parameter(s):{}".format(
                                    exception_message))
            self._log(logging.ERROR, exc)
            raise exc

    def _send_enter_after_changed_state(self, *args, **kwargs):
        from moler.cmd.unix.enter import Enter

        try:
            cmd_enter = Enter(connection=self.io_connection.moler_connection)
            result = cmd_enter()
        except Exception as ex:
            self._log(logging.DEBUG, "Cannot execute command 'enter' properly: {}".format(ex))
            pass
