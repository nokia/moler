# -*- coding: utf-8 -*-
"""
Juniper Generic module.
"""

__author__ = 'Sylwester Golonka, Jakub Kupiec'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com, jakub.kupiec@nokia.com'

import logging
from abc import ABCMeta
from six import add_metaclass
from moler.device.proxy_pc import ProxyPc
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name


@call_base_class_method_with_same_name
@add_metaclass(ABCMeta)
class JuniperGeneric(ProxyPc):
    """Junipergeneric device class."""

    cli = "CLI"
    configure = "CONFIGURE"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, initial_state=None):
        """
        Create unix device communicating over io_connection.

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        :param initial_state: Initial state for device
        """
        sm_params = sm_params.copy()
        initial_state = initial_state if initial_state is not None else JuniperGeneric.cli
        super(JuniperGeneric, self).__init__(sm_params=sm_params, name=name, io_connection=io_connection,
                                             io_type=io_type,
                                             variant=variant, initial_state=initial_state)
        self.logger = logging.getLogger('moler.juniper')

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration with proxy_pc state.

        :return: default sm configuration with proxy_pc state.
        """
        config = {
            JuniperGeneric.connection_hops: {
                JuniperGeneric.proxy_pc: {  # from
                    JuniperGeneric.cli: {  # to
                        "execute_command": "ssh",  # using command
                        "command_params": {  # with parameters
                            "set_timeout": None,
                            "expected_prompt": "^admin@switch>"
                        },
                        "required_command_params": [
                            "host",
                            "login",
                            "password",
                        ]
                    }
                },
                JuniperGeneric.cli: {  # from
                    JuniperGeneric.proxy_pc: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                        },
                        "required_command_params": [
                            "expected_prompt"
                        ]
                    },
                    JuniperGeneric.configure: {
                        "execute_command": "configure",
                        "command_params": {
                            "expected_prompt": "^admin@switch#"
                        }
                    }
                },
                JuniperGeneric.configure: {  # from
                    JuniperGeneric.cli: {  # to
                        "execute_command": "exit_configure",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": "^admin@switch>"
                        }
                    },
                }

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
            JuniperGeneric.connection_hops: {
                JuniperGeneric.unix_local: {  # from
                    JuniperGeneric.cli: {  # to
                        "execute_command": "ssh",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": "^admin@switch>",
                            "set_timeout": None
                        },
                        "required_command_params": [
                            "host",
                            "login",
                            "password",
                        ]
                    }
                },
                JuniperGeneric.cli: {  # from
                    JuniperGeneric.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#'
                        },
                    },
                    JuniperGeneric.configure: {
                        "execute_command": "configure",
                        "command_params": {
                            "expected_prompt": "^admin@switch#"
                        }
                    }
                },
                JuniperGeneric.configure: {  # from
                    JuniperGeneric.cli: {  # to
                        "execute_command": "exit_configure",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": "^admin@switch>"
                        }
                    }
                }
            }
        }
        return config

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_with_proxy_pc(self):
        """
        Prepare transitions to change states with proxy_pc state.

        :return: transitions with proxy_pc state.
        """

        transitions = {
            JuniperGeneric.proxy_pc: {
                JuniperGeneric.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            JuniperGeneric.cli: {

                JuniperGeneric.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                JuniperGeneric.configure: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            JuniperGeneric.configure: {
                JuniperGeneric.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            }
        }
        return transitions

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_without_proxy_pc(self):
        """
        Prepare transitions to change states without proxy_pc state.

        :return: transitions without proxy_pc state.
        """
        transitions = {
            JuniperGeneric.cli: {
                JuniperGeneric.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                JuniperGeneric.configure: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },

            },
            JuniperGeneric.unix_local: {
                JuniperGeneric.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            JuniperGeneric.configure: {
                JuniperGeneric.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            }
        }
        return transitions

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_with_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine with proxy_pc state.

        :return: textual prompt for each state with proxy_pc state.
        """
        state_prompts = {
            JuniperGeneric.cli:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.proxy_pc][
                    JuniperGeneric.cli][
                    "command_params"]["expected_prompt"],
            JuniperGeneric.configure:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.cli][JuniperGeneric.configure][
                    "command_params"]["expected_prompt"]
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_without_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.

        :return: textual prompt for each state without proxy_pc state.
        """
        state_prompts = {
            JuniperGeneric.cli:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.unix_local][JuniperGeneric.cli][
                    "command_params"]["expected_prompt"],
            JuniperGeneric.configure:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.cli][JuniperGeneric.configure][
                    "command_params"]["expected_prompt"]
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine with proxy_pc state.

        :return: non direct transitions for each state with proxy_pc state.
        """
        state_hops = {
            JuniperGeneric.not_connected: {
                JuniperGeneric.cli: JuniperGeneric.unix_local,
                JuniperGeneric.configure: JuniperGeneric.unix_local,
            },
            JuniperGeneric.cli: {
                JuniperGeneric.not_connected: JuniperGeneric.proxy_pc,
                JuniperGeneric.unix_local: JuniperGeneric.proxy_pc,
                JuniperGeneric.unix_local_root: JuniperGeneric.proxy_pc,
            },
            JuniperGeneric.configure: {
                JuniperGeneric.unix_local: JuniperGeneric.cli,
                JuniperGeneric.proxy_pc: JuniperGeneric.cli,
                JuniperGeneric.not_connected: JuniperGeneric.cli,
                JuniperGeneric.unix_local_root: JuniperGeneric.cli
            },
            JuniperGeneric.unix_local: {
                JuniperGeneric.cli: JuniperGeneric.proxy_pc,
                JuniperGeneric.configure: JuniperGeneric.proxy_pc,
            },
            JuniperGeneric.unix_local_root: {
                JuniperGeneric.cli: JuniperGeneric.unix_local,
                JuniperGeneric.configure: JuniperGeneric.unix_local,
            },
            JuniperGeneric.proxy_pc: {
                JuniperGeneric.configure: JuniperGeneric.cli,
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
            JuniperGeneric.not_connected: {
                JuniperGeneric.cli: JuniperGeneric.unix_local,
                JuniperGeneric.configure: JuniperGeneric.unix_local,
            },
            JuniperGeneric.unix_local: {
                JuniperGeneric.configure: JuniperGeneric.cli,
            },
            JuniperGeneric.unix_local_root: {
                JuniperGeneric.cli: JuniperGeneric.unix_local,
                JuniperGeneric.configure: JuniperGeneric.unix_local,
            },
            JuniperGeneric.cli: {
                JuniperGeneric.not_connected: JuniperGeneric.unix_local,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local,
            },
            JuniperGeneric.configure: {
                JuniperGeneric.unix_local: JuniperGeneric.cli,
                JuniperGeneric.not_connected: JuniperGeneric.cli,
                JuniperGeneric.unix_local_root: JuniperGeneric.cli,
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
        available = super(JuniperGeneric, self)._get_packages_for_state(state, observer)

        if not available:
            if state == JuniperGeneric.cli:
                available = {
                    JuniperGeneric.cmds: ['moler.cmd.unix', 'moler.cmd.juniper.cli', 'moler.cmd.juniper_ex.cli'],
                    JuniperGeneric.events: ['moler.events.unix', 'moler.events.juniper', 'moler.events.juniper_ex']}
            elif state == JuniperGeneric.configure:
                available = {
                    JuniperGeneric.cmds: ['moler.events.unix', 'moler.cmd.juniper.configure',
                                          'moler.cmd.juniper_ex.configure'],
                    JuniperGeneric.events: ['moler.events.unix', 'moler.events.juniper', 'moler.events.juniper_ex']}

            if available:
                return available[observer]

        return available
