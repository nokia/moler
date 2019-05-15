# -*- coding: utf-8 -*-
"""
SCPI device class
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import logging

from moler.device.unixlocal import UnixLocal


class Scpi(UnixLocal):
    """Scpi device class."""

    scpi = "SCPI"
    proxy_pc = "PROXY_PC"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, initial_state=None):
        """
        Create SCPI device communicating over io_connection.

        :param sm_params: params with machine state description.
        :param name: name of device.
        :param io_connection: External-IO connection having embedded moler-connection.
        :param io_type: External-IO connection type
        :param variant: External-IO connection variant
        :param initial_state: Initial state for device
        """
        sm_params = sm_params.copy()
        self.use_proxy_pc = self._is_proxy_pc_in_sm_params(sm_params, Scpi.proxy_pc)
        initial_state = initial_state if initial_state is not None else Scpi.scpi
        super(Scpi, self).__init__(sm_params=sm_params, name=name, io_connection=io_connection, io_type=io_type,
                                   variant=variant, initial_state=initial_state)
        self.logger = logging.getLogger('moler.scpi')

    def _get_default_sm_configuration(self):
        config = super(Scpi, self)._get_default_sm_configuration()
        if self.use_proxy_pc:
            default_config = self._get_default_sm_configuration_with_proxy_pc()
        else:
            default_config = self._get_default_sm_configuration_without_proxy_pc()

        self._update_dict(config, default_config)
        return config

    def _get_default_sm_configuration_with_proxy_pc(self):
        config = {
            Scpi.connection_hops: {
                Scpi.unix_local: {  # from
                    Scpi.proxy_pc: {  # to
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
                    }
                },
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
                    Scpi.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
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

    def _get_default_sm_configuration_without_proxy_pc(self):
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

    def _prepare_transitions(self):
        super(Scpi, self)._prepare_transitions()

        if self.use_proxy_pc:
            transitions = self._prepare_transitions_with_proxy_pc()
        else:
            transitions = self._prepare_transitions_without_proxy_pc()
        self._add_transitions(transitions=transitions)

    def _prepare_transitions_with_proxy_pc(self):
        transitions = {
            Scpi.scpi: {
                Scpi.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            UnixLocal.unix_local: {
                Scpi.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            Scpi.proxy_pc: {
                UnixLocal.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                Scpi.scpi: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
        }
        return transitions

    def _prepare_transitions_without_proxy_pc(self):
        transitions = {
            Scpi.scpi: {
                UnixLocal.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            UnixLocal.unix_local: {
                Scpi.scpi: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
        }
        return transitions

    def _prepare_state_prompts(self):
        super(Scpi, self)._prepare_state_prompts()

        if self.use_proxy_pc:
            state_prompts = self._prepare_state_prompts_with_proxy_pc()
        else:
            state_prompts = self._prepare_state_prompts_without_proxy_pc()
        self._update_dict(self._state_prompts, state_prompts)

    def _prepare_state_prompts_with_proxy_pc(self):
        state_prompts = {
            UnixLocal.unix_local:
                self._configurations[Scpi.connection_hops][Scpi.proxy_pc][Scpi.unix_local][
                    "command_params"]["expected_prompt"],
            Scpi.proxy_pc:
                self._configurations[Scpi.connection_hops][Scpi.unix_local][Scpi.proxy_pc][
                    "command_params"]["expected_prompt"],
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.proxy_pc][Scpi.scpi][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    def _prepare_state_prompts_without_proxy_pc(self):
        state_prompts = {
            Scpi.unix_local:
                self._configurations[Scpi.connection_hops][Scpi.scpi][Scpi.unix_local][
                    "command_params"]["expected_prompt"],
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.unix_local][Scpi.scpi][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    def _prepare_state_hops(self):
        super(Scpi, self)._prepare_state_hops()

        if self.use_proxy_pc:
            state_hops = self._prepare_state_hops_with_proxy_pc()
        else:
            state_hops = self._prepare_state_hops_without_proxy_pc()

        self._update_dict(self._state_hops, state_hops)

    def _prepare_state_hops_with_proxy_pc(self):
        state_hops = {
            UnixLocal.not_connected: {
                Scpi.scpi: UnixLocal.unix_local,
            },
            Scpi.scpi: {
                UnixLocal.not_connected: Scpi.proxy_pc,
                UnixLocal.unix_local: Scpi.proxy_pc
            },
            Scpi.unix_local: {
                Scpi.scpi: Scpi.proxy_pc,
            }
        }
        return state_hops

    def _prepare_state_hops_without_proxy_pc(self):
        state_hops = {
            UnixLocal.not_connected: {
                Scpi.scpi: UnixLocal.unix_local,
            },
            Scpi.scpi: {
                UnixLocal.not_connected: UnixLocal.unix_local,
            },
        }
        return state_hops

    def _get_packages_for_state(self, state, observer):
        available = super(Scpi, self)._get_packages_for_state(state, observer)

        if not available:
            if state == Scpi.proxy_pc:
                available = {UnixLocal.cmds: ['moler.cmd.unix'],
                             UnixLocal.events: ['moler.events.shared', 'moler.events.unix']}
            elif state == Scpi.scpi:
                available = {UnixLocal.cmds: ['moler.cmd.scpi.scpi'],
                             UnixLocal.events: ['moler.events.unix', 'moler.events.scpi']}
            if available:
                return available[observer]

        return available

    def _prepare_newline_chars(self):
        super(Scpi, self)._prepare_newline_chars()

        if self.use_proxy_pc:
            newline_chars = self._prepare_newline_chars_with_proxy_pc()
        else:
            newline_chars = self._prepare_newline_chars_without_proxy_pc()

        self._update_dict(self._newline_chars, newline_chars)

    def _prepare_newline_chars_with_proxy_pc(self):
        newline_chars = {
            Scpi.proxy_pc:
                self._configurations[Scpi.connection_hops][Scpi.unix_local][Scpi.proxy_pc][
                    "command_params"]["target_newline"],
            Scpi.unix_local:
                self._configurations[Scpi.connection_hops][Scpi.proxy_pc][Scpi.unix_local][
                    "command_params"]["target_newline"],
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.proxy_pc][Scpi.scpi][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    def _prepare_newline_chars_without_proxy_pc(self):
        newline_chars = {
            Scpi.scpi:
                self._configurations[Scpi.connection_hops][Scpi.unix_local][Scpi.scpi][
                    "command_params"]["target_newline"],
            Scpi.unix_local:
                self._configurations[Scpi.connection_hops][Scpi.scpi][Scpi.unix_local][
                    "command_params"]["target_newline"],
        }
        return newline_chars


"""
Example of device in yaml configuration file:

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

Example of device in yaml with proxy PC:
SCPI_2:
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

"""
