# -*- coding: utf-8 -*-
"""
Juniper Generic module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

import logging
from moler.device.unixlocal import UnixLocal
from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class JuniperGeneric(UnixLocal):
    """Junipergeneric device class."""

    cli = "CLI"
    configure = "CONFIGURE"
    proxy_pc = "PROXY_PC"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, initial_state=None):
        """
        Create unix device communicating over io_connection.

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        :param initial_state: Initial state for device
        """
        sm_params = sm_params.copy()
        self._use_proxy_pc = self._is_proxy_pc_in_sm_params(sm_params, JuniperGeneric.proxy_pc)
        initial_state = initial_state if initial_state is not None else JuniperGeneric.cli
        super(JuniperGeneric, self).__init__(sm_params=sm_params, name=name, io_connection=io_connection,
                                             io_type=io_type,
                                             variant=variant, initial_state=initial_state)
        self.logger = logging.getLogger('moler.juniper')

    def _get_default_sm_configuration(self):
        config = super(JuniperGeneric, self)._get_default_sm_configuration()
        if self._use_proxy_pc:
            default_config = self._get_default_sm_configuration_with_proxy_pc()
        else:
            default_config = self._get_default_sm_configuration_without_proxy_pc()
        self._update_dict(config, default_config)
        return config

    def _get_default_sm_configuration_with_proxy_pc(self):
        config = {
            JuniperGeneric.connection_hops: {
                JuniperGeneric.unix_local: {  # from
                    JuniperGeneric.proxy_pc: {  # to
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
                JuniperGeneric.proxy_pc: {  # from
                    UnixLocal.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
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

    def _get_default_sm_configuration_without_proxy_pc(self):
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
                    },
                }
            }
        }
        return config

    def _prepare_transitions(self):
        super(JuniperGeneric, self)._prepare_transitions()
        if self._use_proxy_pc:
            transitions = self._prepare_transitions_with_proxy_pc()
        else:
            transitions = self._prepare_transitions_without_proxy_pc()
        self._add_transitions(transitions=transitions)

    def _prepare_transitions_with_proxy_pc(self):
        transitions = {
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
            UnixLocal.unix_local: {
                JuniperGeneric.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            JuniperGeneric.proxy_pc: {
                UnixLocal.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                JuniperGeneric.cli: {
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
            },
        }
        return transitions

    def _prepare_transitions_without_proxy_pc(self):
        transitions = {
            JuniperGeneric.cli: {
                UnixLocal.unix_local: {
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
            UnixLocal.unix_local: {
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
            },

        }
        return transitions

    def _prepare_state_prompts(self):
        super(JuniperGeneric, self)._prepare_state_prompts()

        if self._use_proxy_pc:
            state_prompts = self._prepare_state_prompts_with_proxy_pc()
        else:
            state_prompts = self._prepare_state_prompts_without_proxy_pc()
        self._update_dict(self._state_prompts, state_prompts)

    def _prepare_state_prompts_with_proxy_pc(self):
        state_prompts = {
            JuniperGeneric.unix_local:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.proxy_pc][
                    JuniperGeneric.unix_local][
                    "command_params"]["expected_prompt"],
            JuniperGeneric.proxy_pc:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.unix_local][
                    JuniperGeneric.proxy_pc][
                    "command_params"]["expected_prompt"],
            JuniperGeneric.cli:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.proxy_pc][JuniperGeneric.cli][
                    "command_params"]["expected_prompt"],
            JuniperGeneric.configure:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.cli][JuniperGeneric.configure][
                    "command_params"]["expected_prompt"],

        }
        return state_prompts

    def _prepare_state_prompts_without_proxy_pc(self):
        state_prompts = {
            JuniperGeneric.unix_local:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.cli][JuniperGeneric.unix_local][
                    "command_params"]["expected_prompt"],
            JuniperGeneric.cli:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.unix_local][JuniperGeneric.cli][
                    "command_params"]["expected_prompt"],
            JuniperGeneric.configure:
                self._configurations[JuniperGeneric.connection_hops][JuniperGeneric.cli][JuniperGeneric.configure][
                    "command_params"]["expected_prompt"],

        }
        return state_prompts

    def _prepare_state_hops(self):
        super(JuniperGeneric, self)._prepare_state_hops()

        if self._use_proxy_pc:
            state_hops = self._prepare_state_hops_with_proxy_pc()
        else:
            state_hops = self._prepare_state_hops_without_proxy_pc()

        self._update_dict(self._state_hops, state_hops)

    def _prepare_state_hops_with_proxy_pc(self):
        state_hops = {
            JuniperGeneric.not_connected: {
                JuniperGeneric.cli: JuniperGeneric.unix_local,
                JuniperGeneric.configure: JuniperGeneric.unix_local,
                JuniperGeneric.proxy_pc: JuniperGeneric.unix_local,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local,
            },
            JuniperGeneric.cli: {
                JuniperGeneric.not_connected: JuniperGeneric.proxy_pc,
                JuniperGeneric.unix_local: JuniperGeneric.proxy_pc,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local,
            },
            JuniperGeneric.configure: {
                JuniperGeneric.unix_local: JuniperGeneric.cli,
                JuniperGeneric.proxy_pc: JuniperGeneric.cli,
                JuniperGeneric.not_connected: JuniperGeneric.cli,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local
            },
            JuniperGeneric.unix_local: {
                JuniperGeneric.cli: JuniperGeneric.proxy_pc,
                JuniperGeneric.configure: JuniperGeneric.proxy_pc,
            },
            JuniperGeneric.proxy_pc: {
                JuniperGeneric.configure: JuniperGeneric.cli,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local
            }
        }
        return state_hops

    def _prepare_state_hops_without_proxy_pc(self):
        state_hops = {
            UnixLocal.not_connected: {
                JuniperGeneric.cli: UnixLocal.unix_local,
                JuniperGeneric.configure: UnixLocal.unix_local,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local,

            },
            UnixLocal.unix_local: {
                JuniperGeneric.configure: JuniperGeneric.cli
            },
            JuniperGeneric.cli: {
                UnixLocal.not_connected: UnixLocal.unix_local,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local,
            },
            JuniperGeneric.configure: {
                UnixLocal.unix_local: JuniperGeneric.cli,
                UnixLocal.not_connected: JuniperGeneric.cli,
                JuniperGeneric.unix_local_root: JuniperGeneric.unix_local,

            },
        }
        return state_hops

    def _get_packages_for_state(self, state, observer):
        available = {UnixLocal.cmds: [], UnixLocal.events: []}
        if state == UnixLocal.unix_local or state == JuniperGeneric.proxy_pc:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
        elif state == JuniperGeneric.cli:
            available = {UnixLocal.cmds: ['moler.cmd.unix', 'moler.cmd.juniper.cli'],
                         UnixLocal.events: ['moler.events.unix', 'moler.events.juniper']}
        elif state == JuniperGeneric.configure:
            available = {UnixLocal.cmds: ['moler.cmd.juniper.configure'],
                         UnixLocal.events: ['moler.events.juniper']}
        return available[observer]
