# -*- coding: utf-8 -*-
"""
SCPI device class
"""

__author__ = 'Marcin Usielski, Marcin Szlapa'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com, marcin.szlapa@nokia.com'

import logging

from moler.device.proxy_pc import ProxyPc
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name


@call_base_class_method_with_same_name
class Scpi(ProxyPc):
    r"""
    Scpi device class.


    ::


        Example of device in yaml configuration file:
        - with PROXY_PC:
            SCPI_1:
            DEVICE_CLASS: moler.device.scpi.Scpi
            CONNECTION_HOPS:
            PROXY_PC:
                SCPI:
                execute_command: telnet # default value
                command_params:
                    expected_prompt: SCPI>
                    host: 10.0.0.1
                    port: 99999
            SCPI:
                PROXY_PC:
                execute_command: exit_telnet # default value
                command_params:
                    expected_prompt: proxy_pc.*>
            UNIX_LOCAL:
                PROXY_PC:
                execute_command: ssh # default value
                command_params:
                    expected_prompt: proxy_pc.*>
                    host: 10.0.0.2
                    login: user
                    password: password
        -without PROXY_PC:
            SCPI_1:
                DEVICE_CLASS: moler.device.scpi.Scpi
                CONNECTION_HOPS:
                UNIX_LOCAL:
                    SCPI:
                    execute_command: telnet # default value
                    command_params:
                        expected_prompt: SCPI>
                        host: 10.0.0.1
                        port: 99999
    """

    scpi = "SCPI"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None,
                 io_constructor_kwargs=None, initial_state=None, lazy_cmds_events=False):
        """
        Create SCPI device communicating over io_connection.

        :param sm_params: params with machine state description.
        :param name: name of device.
        :param io_connection: External-IO connection having embedded moler-connection.
        :param io_type: External-IO connection type
        :param variant: External-IO connection variant
        :param io_constructor_kwargs: additional parameters for constructor of selected io_type
        :param initial_state: Initial state for device
        :param lazy_cmds_events: set False to load all commands and events when device is initialized, set True to load
                        commands and events when they are required for the first time.
        """
        sm_params = sm_params.copy()
        initial_state = initial_state if initial_state is not None else Scpi.scpi
        super(Scpi, self).__init__(sm_params=sm_params, name=name, io_connection=io_connection, io_type=io_type,
                                   variant=variant, io_constructor_kwargs=io_constructor_kwargs,
                                   initial_state=initial_state, lazy_cmds_events=lazy_cmds_events)
        self.logger = logging.getLogger('moler.scpi')

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration with proxy_pc state.
        :return: default sm configuration with proxy_pc state.
        """
        config = {
            Scpi.connection_hops: {
                Scpi.proxy_pc: {  # from
                    Scpi.scpi: {  # to
                        "execute_command": "telnet",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'SCPI>',
                            "set_timeout": None,
                            "target_newline": "\r\n",
                        },
                        "required_command_params": [
                            "host",
                            "port",
                        ]
                    },
                },
                Scpi.scpi: {  # from
                    Scpi.proxy_pc: {  # to
                        "execute_command": "exit_telnet",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                            "expected_prompt"
                        ]
                    },
                },
            }
        }
        return config

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_without_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        config = {
            Scpi.connection_hops: {
                Scpi.unix_local: {  # from
                    Scpi.scpi: {  # to
                        "execute_command": "telnet",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\r\n",
                            "expected_prompt": r'\w+>',
                            "set_timeout": None,
                        },
                        "required_command_params": [
                            "host",
                            "port",
                        ]
                    },
                },
                Scpi.scpi: {  # from
                    Scpi.unix_local: {  # to
                        "execute_command": "exit_telnet",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#',
                            "target_newline": "\n",
                        },
                        "required_command_params": [
                        ]
                    },
                },
            }
        }
        return config

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_with_proxy_pc(self):
        transitions = {
            Scpi.scpi: {
                Scpi.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            Scpi.proxy_pc: {
                Scpi.scpi: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
        }
        return transitions

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_without_proxy_pc(self):
        """
       Prepare transitions to change states without proxy_pc state.
       :return: transitions without proxy_pc state.
       """
        transitions = {
            Scpi.scpi: {
                Scpi.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            Scpi.unix_local: {
                Scpi.scpi: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
        }
        return transitions

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_with_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine with proxy_pc state.
        :return: textual prompt for each state with proxy_pc state.
        """
        state_prompts = {
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.proxy_pc][Scpi.scpi][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_without_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        state_prompts = {
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.unix_local][Scpi.scpi][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine with proxy_pc state.
        :return: non direct transitions for each state with proxy_pc state.
        """
        state_hops = {
            Scpi.not_connected: {
                Scpi.scpi: Scpi.unix_local,
                Scpi.proxy_pc: Scpi.unix_local,
                Scpi.unix_local_root: Scpi.unix_local,
            },
            Scpi.scpi: {
                Scpi.not_connected: Scpi.proxy_pc,
                Scpi.unix_local: Scpi.proxy_pc,
                Scpi.unix_local_root: Scpi.proxy_pc
            },
            Scpi.unix_local: {
                Scpi.scpi: Scpi.proxy_pc,
            },
            Scpi.unix_local_root: {
                Scpi.scpi: Scpi.unix_local,
                Scpi.not_connected: Scpi.unix_local,
            },
            Scpi.proxy_pc: {
                Scpi.not_connected: Scpi.unix_local,
            }
        }
        return state_hops

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_without_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine without proxy_pc state.
        :return: non direct transitions for each state without proxy_pc state.
        """
        state_hops = {
            Scpi.not_connected: {
                Scpi.scpi: Scpi.unix_local,
                Scpi.unix_local_root: Scpi.unix_local,
            },
            Scpi.scpi: {
                Scpi.not_connected: Scpi.unix_local,
                Scpi.unix_local_root: Scpi.unix_local
            },
            Scpi.unix_local_root: {
                Scpi.scpi: Scpi.unix_local,
                Scpi.not_connected: Scpi.unix_local,
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
        available = super(Scpi, self)._get_packages_for_state(state, observer)

        if not available:
            if state == Scpi.scpi:
                available = {Scpi.cmds: ['moler.cmd.scpi.scpi'],
                             Scpi.events: ['moler.events.unix', 'moler.events.scpi']}
            if available:
                return available[observer]

        return available

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_with_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine with proxy_pc state.
        :return: newline char for each state with proxy_pc state.
        """
        newline_chars = {
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.proxy_pc][Scpi.scpi][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        newline_chars = {
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.unix_local][Scpi.scpi][
                    "command_params"]["target_newline"],
        }
        return newline_chars
