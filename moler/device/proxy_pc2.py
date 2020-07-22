# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Michal Ernst, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'michal.ernst@nokia.com, grzegorz.latuszek@nokia.com'
import six
import abc
import platform

from moler.device.textualdevice import TextualDevice
from moler.device.unixlocal import UnixLocal
try:
    from moler.io.raw.terminal import ThreadedTerminal
except ImportError:  # ThreadedTerminal won't load on Windows
    pass
from moler.events.shared.wait4 import Wait4

# helper variables to improve readability of state machines
# f.ex. moler.device.textualdevice introduces state TextualDevice.not_connected = "NOT_CONNECTED"
NOT_CONNECTED = TextualDevice.not_connected
CONNECTION_HOPS = TextualDevice.connection_hops
UNIX_LOCAL = UnixLocal.unix_local
UNIX_LOCAL_ROOT = UnixLocal.unix_local_root
PROXY_PC = "PROXY_PC"


def want_local_unix_state(io_type=None, io_connection=None):
    """
    Check if device is intended to work with local machine or remote ones only.
    :return: True for local.
    """
    if io_type == "terminal":
        return True
    if (platform.system() != 'Windows') and isinstance(io_connection, ThreadedTerminal):
        return True
    else:  # all remote-access connections (tcp, udp, telnet, ssh); even connecting to localhost
        return False


@six.add_metaclass(abc.ABCMeta)
class ProxyPc2(UnixLocal):

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, io_constructor_kwargs=None,
                 initial_state=None, lazy_cmds_events=False):
        """
        Create Unix device communicating over io_connection
        :param sm_params: dict with parameters of state machine for device
        :param name: name of device
        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: type of connection - tcp, udp, ssh, telnet, ...
        :param variant: connection implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
                        (if not given then default one is taken)
        :param io_constructor_kwargs: additional parameter into constructor of selected connection type
                        (if not given then default one is taken)
        :param initial_state: name of initial state. State machine tries to enter this state just after creation.
        :param lazy_cmds_events: set False to load all commands and events when device is initialized, set True to load
                        commands and events when they are required for the first time.
        """
        self._use_local_unix_state = want_local_unix_state(io_type, io_connection)
        base_state = UNIX_LOCAL if self._use_local_unix_state else NOT_CONNECTED
        self._use_proxy_pc = self._should_use_proxy_pc(sm_params, PROXY_PC)
        base_or_final_state = PROXY_PC if self._use_proxy_pc else base_state
        initial_state = initial_state if initial_state is not None else base_or_final_state
        super(ProxyPc2, self).__init__(name=name, io_connection=io_connection,
                                       io_type=io_type, variant=variant,
                                       io_constructor_kwargs=io_constructor_kwargs,
                                       sm_params=sm_params, initial_state=initial_state,
                                       lazy_cmds_events=lazy_cmds_events)
        self._prompt_detector_timeout = 0.5
        self._after_open_prompt_detector = None
        self._warn_about_temporary_life_of_class()

    def _warn_about_temporary_life_of_class(self):
        what = "experimental/temporary implementation of device utilizing sshshell connection"
        temporary_classname = self.__class__.__name__
        target_classname = temporary_classname[:-1]
        merge_info = "It's functionality will be merged"
        future_change = "{} into {} device in Moler 2.0.0 and {} will be removed".format(merge_info,
                                                                                         target_classname,
                                                                                         temporary_classname)
        warn_msg = "Class {} is an {}. {}.".format(temporary_classname, what, future_change)
        self.logger.warning(warn_msg)

    def _should_use_proxy_pc(self, sm_params, proxy):
        proxy_in_config = self._is_proxy_pc_in_sm_params(sm_params, proxy)
        if (not proxy_in_config) and (not self._use_local_unix_state) and (self.__class__.__name__ == 'ProxyPc2'):
            return True  # ProxyPc is target of connection open
        return proxy_in_config

    def goto_state(self, state, *args, **kwargs):
        """Goes to specific state."""
        if ((state == UNIX_LOCAL) or (state == UNIX_LOCAL_ROOT)) and (not self._use_local_unix_state):
            used_io = "{} {}".format(self.io_connection.__class__.__name__, self.io_connection)
            msg = "Device {} has no {}/{} states".format(self, UNIX_LOCAL, UNIX_LOCAL_ROOT)
            why = "since it uses following io: {}".format(used_io)
            fix = 'You need io of type "terminal" to have unix-local states'
            err_msg = "{} {}. {}.".format(msg, why, fix)
            raise ValueError(err_msg)
        super(ProxyPc2, self).goto_state(state=state, *args, **kwargs)

    def _get_default_sm_configuration(self):
        """
        Create State Machine default configuration.
        :return: default sm configuration.
        """
        config = {}
        if self._use_local_unix_state:
            config = super(ProxyPc2, self)._get_default_sm_configuration()

        if self._use_proxy_pc:
            default_config = self._get_default_sm_configuration_with_proxy_pc()
        else:
            default_config = self._get_default_sm_configuration_without_proxy_pc()
        self._update_dict(config, default_config)
        return config

    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration with proxy_pc state.
        :return: default sm configuration with proxy_pc state.
        """
        if self._use_local_unix_state:
            config = {
                CONNECTION_HOPS: {
                    UNIX_LOCAL: {  # from
                        PROXY_PC: {  # to
                            "execute_command": "ssh",  # using command
                            "command_params": {  # with parameters
                                "target_newline": "\n"
                            },
                            "required_command_params": [
                                "host",
                                "login",
                                "password",
                                "expected_prompt"
                            ]
                        },
                    },
                    PROXY_PC: {  # from
                        UNIX_LOCAL: {  # to
                            "execute_command": "exit",  # using command
                            "command_params": {  # with parameters
                                "target_newline": "\n",
                                "expected_prompt": r'^moler_bash#',
                            },
                            "required_command_params": [
                            ]
                        }
                    },
                }
            }
        else:
            config = {}  # no config needed, will open connection to directly jump NOT_CONNECTED -> PROXY_PC
        return config

    def _get_default_sm_configuration_without_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        config = {}
        return config

    def _prepare_transitions(self):
        """
        Prepare transitions to change states.
        :return: Nothing.
        """
        if self._use_local_unix_state:
            super(ProxyPc2, self)._prepare_transitions()

        if self._use_proxy_pc:
            transitions = self._prepare_transitions_with_proxy_pc()
        else:
            transitions = self._prepare_transitions_without_proxy_pc()
        self._add_transitions(transitions=transitions)

    def _prepare_transitions_with_proxy_pc(self):
        """
        Prepare transitions to change states with proxy_pc state.
        :return: transitions with proxy_pc state.
        """
        if self._use_local_unix_state:
            transitions = {
                UNIX_LOCAL: {
                    PROXY_PC: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    }
                },
                PROXY_PC: {
                    UNIX_LOCAL: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    },
                },
            }
        else:  # directly from NOT_CONNECTED to PROXY_PC
            transitions = {
                NOT_CONNECTED: {
                    PROXY_PC: {
                        "action": [
                            "_open_connection"
                        ],
                    }
                },
                PROXY_PC: {
                    NOT_CONNECTED: {
                        "action": [
                            "_close_connection"
                        ],
                    },
                },
            }
        return transitions

    def _prepare_transitions_without_proxy_pc(self):
        """
        Prepare transitions to change states without proxy_pc state.
        :return: transitions without proxy_pc state.
        """
        transitions = {}
        return transitions

    def on_connection_made(self, connection):
        """
        Execute action when connection made.
        :param connection: device connection.
        :return: Nothing.
        """
        if self._use_local_unix_state:
            super(ProxyPc2, self).on_connection_made(connection)
        else:
            self._set_state(PROXY_PC)
            self._detect_after_open_prompt(self._set_after_open_prompt)

    def on_connection_lost(self, connection):
        """
        Execute action when connection lost.
        :param connection: device connection.
        :return: Nothing.
        """
        self._set_state(NOT_CONNECTED)

    def _detect_after_open_prompt(self, set_callback):
        self._after_open_prompt_detector = Wait4(detect_patterns=[r'^(.+)echo DETECTING PROMPT'],
                                                 connection=self.io_connection.moler_connection,
                                                 till_occurs_times=1)
        detector = self._after_open_prompt_detector
        detector.add_event_occurred_callback(callback=set_callback,
                                             callback_params={"event": detector})
        self.io_connection.moler_connection.sendline("echo DETECTING PROMPT")
        self._after_open_prompt_detector.start(timeout=self._prompt_detector_timeout)

    def _set_after_open_prompt(self, event):
        occurrence = event.get_last_occurrence()
        prompt = occurrence['groups'][0]
        state = self._get_current_state()
        with self._state_prompts_lock:
            self._state_prompts[state] = prompt.rstrip()

    def _prepare_state_prompts(self):
        """
        Prepare textual prompt for each state.
        :return: Nothing.
        """
        if self._use_local_unix_state:
            super(ProxyPc2, self)._prepare_state_prompts()

        if self._use_proxy_pc:
            state_prompts = self._prepare_state_prompts_with_proxy_pc()
        else:
            state_prompts = self._prepare_state_prompts_without_proxy_pc()

        self._update_dict(self._state_prompts, state_prompts)

    def _prepare_state_prompts_with_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine with proxy_pc state.
        :return: textual prompt for each state with proxy_pc state.
        """
        state_prompts = {}
        if self._use_local_unix_state:
            state_prompts = {
                PROXY_PC:
                    self._configurations[CONNECTION_HOPS][UNIX_LOCAL][PROXY_PC]["command_params"]["expected_prompt"],
                UNIX_LOCAL:
                    self._configurations[CONNECTION_HOPS][PROXY_PC][UNIX_LOCAL]["command_params"]["expected_prompt"],
            }
        # else detects prompt after establishing connection: _detect_after_open_prompt() & _set_after_open_prompt()
        return state_prompts

    def _prepare_state_prompts_without_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        state_prompts = {}
        return state_prompts

    def _prepare_newline_chars(self):
        """
        Prepare newline char for each state.
        :return: Nothing.
        """
        if self._use_local_unix_state:
            super(ProxyPc2, self)._prepare_newline_chars()

        if self._use_proxy_pc:
            newline_chars = self._prepare_newline_chars_with_proxy_pc()
        else:
            newline_chars = self._prepare_newline_chars_without_proxy_pc()

        self._update_dict(self._newline_chars, newline_chars)

    def _prepare_newline_chars_with_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine with proxy_pc state.
        :return: newline char for each state with proxy_pc state.
        """
        newline_chars = {}
        if self._use_local_unix_state:
            newline_chars = {
                PROXY_PC:
                    self._configurations[CONNECTION_HOPS][UNIX_LOCAL][PROXY_PC]["command_params"]["target_newline"],
                UNIX_LOCAL:
                    self._configurations[CONNECTION_HOPS][PROXY_PC][UNIX_LOCAL]["command_params"]["target_newline"],
            }
        return newline_chars

    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        newline_chars = {}
        return newline_chars

    def _prepare_state_hops(self):
        """
        Prepare hops for non direct transitions between states.
        :return: Nothing.
        """
        if self._use_local_unix_state:
            super(ProxyPc2, self)._prepare_state_hops()

        if self._use_proxy_pc:
            state_hops = self._prepare_state_hops_with_proxy_pc()
        else:
            state_hops = self._prepare_state_hops_without_proxy_pc()

        self._update_dict(self._state_hops, state_hops)

    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine with proxy_pc state.
        :return: non direct transitions for each state with proxy_pc state.
        """
        state_hops = {}
        if self._use_local_unix_state:
            state_hops = {
                NOT_CONNECTED: {
                    PROXY_PC: UNIX_LOCAL,
                },
                UNIX_LOCAL_ROOT: {
                    PROXY_PC: UNIX_LOCAL,
                },
                PROXY_PC: {
                    NOT_CONNECTED: UNIX_LOCAL,
                    UNIX_LOCAL_ROOT: UNIX_LOCAL,
                },
            }
        return state_hops

    def _prepare_state_hops_without_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine without proxy_pc state.
        :return: non direct transitions for each state without proxy_pc state.
        """
        state_hops = {}
        return state_hops

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages contain cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = []
        if self._use_local_unix_state:
            available = super(ProxyPc2, self)._get_packages_for_state(state, observer)

        if not available:
            if state == PROXY_PC:
                available = {TextualDevice.cmds: ['moler.cmd.unix'],
                             TextualDevice.events: ['moler.events.shared', 'moler.events.unix']}
            if available:
                return available[observer]

        return available
