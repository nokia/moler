# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'
import six
import abc
import logging

from moler.device.unixlocal import UnixLocal
from moler.helpers import remove_state_from_sm, remove_state_hops_from_sm


@six.add_metaclass(abc.ABCMeta)
class ProxyPc3(UnixLocal):
    proxy_pc = "PROXY_PC"

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
        initial_state = initial_state if initial_state is not None else ProxyPc3.unix_local
        self._use_proxy_pc = self._is_proxy_pc_in_sm_params(sm_params, ProxyPc3.proxy_pc)
        super(ProxyPc3, self).__init__(name=name, io_connection=io_connection,
                                       io_type=io_type, variant=variant,
                                       io_constructor_kwargs=io_constructor_kwargs,
                                       sm_params=sm_params, initial_state=initial_state,
                                       lazy_cmds_events=lazy_cmds_events)
        self._log(level=logging.WARNING, msg="Experimental device. May be deleted at any moment. Please don't use it in your scripts.")

    def _prepare_sm_data(self, sm_params):
        self._prepare_dicts_for_sm(sm_params=sm_params)

        self._prepare_newline_chars()
        self._send_transitions_to_sm(self._stored_transitions)

    def _prepare_transitions(self):
        """
        Prepare transitions to change states.
        :return: None.
        """

        stored_is_proxy_pc = self._use_proxy_pc
        self._use_proxy_pc = True
        super(ProxyPc3, self)._prepare_transitions()
        self._use_proxy_pc = stored_is_proxy_pc
        transitions = self._prepare_transitions_with_proxy_pc()
        self._add_transitions(transitions=transitions)

    def _prepare_dicts_for_sm(self, sm_params):
        """
        Prepare transitions to change states.
        :return: None.
        """

        self._prepare_transitions()
        transitions = self._stored_transitions
        state_hops = self._prepare_state_hops_with_proxy_pc()

        default_sm_configurations = self._get_default_sm_configuration()

        if not self._use_proxy_pc:
            (connection_hops, transitions) = remove_state_from_sm(
                source_sm=default_sm_configurations[ProxyPc3.connection_hops],
                source_transitions=transitions,
                state_to_remove=ProxyPc3.proxy_pc,
            )
            state_hops = remove_state_hops_from_sm(
                source_hops=state_hops, state_to_remove=ProxyPc3.proxy_pc
            )
            default_sm_configurations[ProxyPc3.connection_hops] = connection_hops

        self._stored_transitions = transitions
        self._update_dict(self._state_hops, state_hops)

        self._configurations = self._prepare_sm_configuration(
            default_sm_configurations, sm_params
        )
        self._overwrite_prompts()
        self._validate_device_configuration()
        self._prepare_state_prompts()

    def _overwrite_prompts(self) -> None:
        """
        Method to overwrite prompts in commands.
        :return: None
        """

    def _get_default_sm_configuration(self):
        """
        Create State Machine default configuration.
        :return: default sm configuration.
        """
        config = super(ProxyPc3, self)._get_default_sm_configuration()
        default_config = self._get_default_sm_configuration_with_proxy_pc()

        self._update_dict(config, default_config)
        return config

    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration with proxy_pc state.
        :return: default sm configuration with proxy_pc state.
        """
        config = {
            ProxyPc3.connection_hops: {
                ProxyPc3.unix_local: {  # from
                    ProxyPc3.proxy_pc: {  # to
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
                ProxyPc3.proxy_pc: {  # from
                    ProxyPc3.unix_local: {  # to
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
        return config

    def _prepare_transitions(self):
        """
        Prepare transitions to change states.
        :return: None.
        """

        stored_is_proxy_pc = self._use_proxy_pc
        self._use_proxy_pc = True
        super(ProxyPc3, self)._prepare_transitions()
        self._use_proxy_pc = stored_is_proxy_pc
        transitions = self._prepare_transitions_with_proxy_pc()
        self._add_transitions(transitions=transitions)

    def _prepare_transitions_with_proxy_pc(self):
        """
        Prepare transitions to change states with proxy_pc state.
        :return: transitions with proxy_pc state.
        """
        transitions = {
            ProxyPc3.unix_local: {
                ProxyPc3.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            ProxyPc3.proxy_pc: {
                ProxyPc3.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
        }
        return transitions

    def _prepare_state_prompts(self):
        """
        Prepare textual prompt for each state.
        :return: None.
        """
        super(ProxyPc3, self)._prepare_state_prompts()

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
        state_prompts = {
            ProxyPc3.proxy_pc:
                self._configurations[ProxyPc3.connection_hops][ProxyPc3.unix_local][ProxyPc3.proxy_pc][
                    "command_params"]["expected_prompt"],
            ProxyPc3.unix_local:
                self._configurations[ProxyPc3.connection_hops][ProxyPc3.proxy_pc][ProxyPc3.unix_local][
                    "command_params"]["expected_prompt"],
        }
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
        :return: None.
        """
        super(ProxyPc3, self)._prepare_newline_chars()

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
        newline_chars = {
            ProxyPc3.proxy_pc:
                self._configurations[ProxyPc3.connection_hops][ProxyPc3.unix_local][ProxyPc3.proxy_pc][
                    "command_params"]["target_newline"],
            ProxyPc3.unix_local:
                self._configurations[ProxyPc3.connection_hops][ProxyPc3.proxy_pc][ProxyPc3.unix_local][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        newline_chars = {}
        return newline_chars

    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine with proxy_pc state.
        :return: non direct transitions for each state with proxy_pc state.
        """
        state_hops = {
            UnixLocal.not_connected: {
                ProxyPc3.proxy_pc: ProxyPc3.unix_local,
            },
            UnixLocal.unix_local_root: {
                ProxyPc3.proxy_pc: ProxyPc3.unix_local,
                ProxyPc3.not_connected: ProxyPc3.unix_local,
            },
            ProxyPc3.proxy_pc: {
                ProxyPc3.not_connected: ProxyPc3.unix_local,
                ProxyPc3.unix_local_root: ProxyPc3.unix_local,
            },
        }
        return state_hops

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages contain cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = super(ProxyPc3, self)._get_packages_for_state(state, observer)

        if not available:
            if state == ProxyPc3.proxy_pc:
                available = {UnixLocal.cmds: ['moler.cmd.unix'],
                             UnixLocal.events: ['moler.events.shared', 'moler.events.unix']}
            if available:
                return available[observer]

        return available
