# -*- coding: utf-8 -*-
"""

"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

import logging
from moler.device.unixlocal import UnixLocal


class JUNOS(UnixLocal):
    """Junos device class."""

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
        self.use_proxy_pc = self._is_proxy_pc_in_sm_params(sm_params, JUNOS.proxy_pc)
        initial_state = initial_state if initial_state is not None else JUNOS.cli
        super(JUNOS, self).__init__(sm_params=sm_params, name=name, io_connection=io_connection, io_type=io_type,
                                    variant=variant, initial_state=initial_state)
        self.logger = logging.getLogger('moler.junos')

    def _get_default_sm_configuration(self):
        if self.use_proxy_pc:
            config = self._get_default_sm_configuration_with_proxy_pc()
        else:
            config = self._get_default_sm_configuration_without_proxy_pc()

        return config

    def _get_default_sm_configuration_with_proxy_pc(self):
        config = {
            JUNOS.connection_hops: {
                JUNOS.unix_local: {  # from
                    JUNOS.proxy_pc: {  # to
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
                JUNOS.proxy_pc: {  # from
                    UnixLocal.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                    JUNOS.cli: {  # to
                        "execute_command": "ssh",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n",
                            "expected_prompt": "^admin@switch>"
                        },
                        "required_command_params": [
                            "host",
                            "login",
                            "password",
                        ]
                    }
                },
                JUNOS.cli: {  # from
                    JUNOS.proxy_pc: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                        },
                        "required_command_params": [
                            "expected_prompt"
                        ]
                    },
                    JUNOS.configure: {
                        "execute_command": "configure",
                        "command_params": {
                            "expected_prompt": "^admin@switch#"
                        }
                    }
                },
                JUNOS.configure: {  # from
                    JUNOS.cli: {  # to
                        "execute_command": "exit",  # using command
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
            JUNOS.connection_hops: {
                JUNOS.unix_local: {  # from
                    JUNOS.cli: {  # to
                        "execute_command": "ssh",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n",
                            "expected_prompt": "^admin@switch>"
                        },
                        "required_command_params": [
                            "host",
                            "login",
                            "password",
                        ]
                    }
                },
                JUNOS.cli: {  # from
                    JUNOS.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#'
                        },
                    },
                    JUNOS.configure: {
                        "execute_command": "configure",
                        "command_params": {
                            "expected_prompt": "^admin@switch#"
                        }
                    }
                },
                JUNOS.configure: {  # from
                    JUNOS.cli: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": "^admin@switch>"
                        }
                    },
                }
            }
        }
        return config

    def _prepare_transitions(self):
        super(JUNOS, self)._prepare_transitions()

        if self.use_proxy_pc:
            transitions = self._prepare_transitions_with_proxy_pc()
        else:
            transitions = self._prepare_transitions_without_proxy_pc()
        self._add_transitions(transitions=transitions)

    def _prepare_transitions_with_proxy_pc(self):
        transitions = {
            JUNOS.cli: {
                JUNOS.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                JUNOS.configure: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            UnixLocal.unix_local: {
                JUNOS.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            JUNOS.proxy_pc: {
                UnixLocal.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                JUNOS.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            JUNOS.configure: {
                JUNOS.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
        }
        return transitions

    def _prepare_transitions_without_proxy_pc(self):
        transitions = {
            JUNOS.cli: {
                UnixLocal.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                JUNOS.configure: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },

            },
            UnixLocal.unix_local: {
                JUNOS.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            JUNOS.configure: {
                JUNOS.cli: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },

        }
        return transitions

    def _prepare_state_prompts(self):
        super(JUNOS, self)._prepare_state_prompts()

        if self.use_proxy_pc:
            state_prompts = self._prepare_state_prompts_with_proxy_pc()
        else:
            state_prompts = self._prepare_state_prompts_without_proxy_pc()
        self._update_dict(self._state_prompts, state_prompts)

    def _prepare_state_prompts_with_proxy_pc(self):
        state_prompts = {
            JUNOS.unix_local:
                self._configurations[JUNOS.connection_hops][JUNOS.proxy_pc][JUNOS.unix_local][
                    "command_params"]["expected_prompt"],
            JUNOS.proxy_pc:
                self._configurations[JUNOS.connection_hops][JUNOS.unix_local][JUNOS.proxy_pc][
                    "command_params"]["expected_prompt"],
            JUNOS.cli:
                self._configurations[JUNOS.connection_hops][JUNOS.configure][JUNOS.cli][
                    "command_params"]["expected_prompt"],
            JUNOS.configure:
                self._configurations[JUNOS.connection_hops][JUNOS.cli][JUNOS.configure][
                    "command_params"]["expected_prompt"],

        }
        return state_prompts

    def _prepare_state_prompts_without_proxy_pc(self):
        state_prompts = {
            JUNOS.unix_local:
                self._configurations[JUNOS.connection_hops][JUNOS.cli][JUNOS.unix_local][
                    "command_params"]["expected_prompt"],
            JUNOS.cli:
                self._configurations[JUNOS.connection_hops][JUNOS.configure][JUNOS.cli][
                    "command_params"]["expected_prompt"],
            JUNOS.configure:
                self._configurations[JUNOS.connection_hops][JUNOS.cli][JUNOS.configure][
                    "command_params"]["expected_prompt"],

        }
        return state_prompts

    def _prepare_state_hops(self):
        super(JUNOS, self)._prepare_state_hops()

        if self.use_proxy_pc:
            state_hops = self._prepare_state_hops_with_proxy_pc()
        else:
            state_hops = self._prepare_state_hops_without_proxy_pc()

        self._update_dict(self._state_hops, state_hops)

    def _prepare_state_hops_with_proxy_pc(self):
        state_hops = {
            UnixLocal.not_connected: {
                JUNOS.cli: UnixLocal.unix_local,
                JUNOS.configure: UnixLocal.unix_local,
                JUNOS.proxy_pc: UnixLocal.unix_local
            },
            JUNOS.cli: {
                UnixLocal.not_connected: JUNOS.proxy_pc,
                UnixLocal.unix_local: JUNOS.proxy_pc
            },
            JUNOS.configure: {
                UnixLocal.unix_local: JUNOS.cli,
                JUNOS.proxy_pc: JUNOS.cli,
                UnixLocal.not_connected: JUNOS.cli,

            },
            JUNOS.unix_local: {
                JUNOS.cli: JUNOS.proxy_pc,
                JUNOS.configure: JUNOS.proxy_pc,
            }
        }
        return state_hops

    def _prepare_state_hops_without_proxy_pc(self):
        state_hops = {
            UnixLocal.not_connected: {
                JUNOS.cli: UnixLocal.unix_local,
                JUNOS.configure: UnixLocal.unix_local,
            },
            JUNOS.cli: {
                UnixLocal.not_connected: UnixLocal.unix_local,
            },
            JUNOS.configure: {
                UnixLocal.unix_local: JUNOS.cli,
                UnixLocal.not_connected: JUNOS.cli,

            },
        }
        return state_hops

    def _get_packages_for_state(self, state, observer):
        available = {UnixLocal.cmds: [], UnixLocal.events: []}
        if state == UnixLocal.unix_local or state == JUNOS.proxy_pc:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
        elif state == JUNOS.cli:
            available = {UnixLocal.cmds: ['moler.cmd.junos.cli'],
                         UnixLocal.events: ['moler.events.junos']}
        elif state == JUNOS.configure:
            available = {UnixLocal.cmds: ['moler.cmd.junos.configure'],
                         UnixLocal.events: ['moler.events.junos']}
        return available[observer]

    def _execute_command_to_change_state(self, source_state, dest_state, timeout=-1):
        configurations = self.get_configurations(source_state=source_state, dest_state=dest_state)
        # will be telnet or ssh
        command_name = configurations["execute_command"]
        command_params = configurations["command_params"]

        command_timeout = self.calc_timeout_for_command(timeout, command_params)
        command = self.get_cmd(cmd_name=command_name, cmd_params=command_params)
        command(timeout=command_timeout)
