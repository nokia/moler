# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.device.proxy_pc import ProxyPc
from moler.helpers import call_base_class_method_with_same_name


# TODO: name, logger/logger_name as param
class UnixRemote(ProxyPc):
    unix_remote = "UNIX_REMOTE"
    unix_remote_root = "UNIX_REMOTE_ROOT"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, io_constructor_kwargs={},
                 initial_state=None):
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
        """
        initial_state = initial_state if initial_state is not None else UnixRemote.unix_remote
        super(UnixRemote, self).__init__(name=name, io_connection=io_connection,
                                         io_type=io_type, variant=variant,
                                         io_constructor_kwargs=io_constructor_kwargs,
                                         sm_params=sm_params, initial_state=initial_state)

    @call_base_class_method_with_same_name
    def _get_default_sm_configuration_with_proxy_pc(self):
        config = {
            UnixRemote.connection_hops: {
                UnixRemote.proxy_pc: {  # from
                    UnixRemote.unix_remote: {  # to
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
                UnixRemote.unix_remote: {  # from
                    UnixRemote.proxy_pc: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                            "expected_prompt"
                        ]
                    },
                    UnixRemote.unix_remote_root: {  # to
                        "execute_command": "su",  # using command
                        "command_params": {  # with parameters
                            "password": "root_password",
                            "expected_prompt": r'remote_root_prompt',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                },
                UnixRemote.unix_remote_root: {  # from
                    UnixRemote.unix_remote: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n",
                            "expected_prompt": r'remote_user_prompt'
                        },
                        "required_command_params": [
                        ]
                    }
                }
            }
        }
        return config

    @call_base_class_method_with_same_name
    def _get_default_sm_configuration_without_proxy_pc(self):
        config = {
            UnixRemote.connection_hops: {
                UnixRemote.unix_local: {  # from
                    UnixRemote.unix_remote: {  # to
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
                UnixRemote.unix_remote: {  # from
                    UnixRemote.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                    UnixRemote.unix_remote_root: {  # to
                        "execute_command": "su",  # using command
                        "command_params": {  # with parameters
                            "password": "root_password",
                            "expected_prompt": r'remote_root_prompt',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                    UnixRemote.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                },
                UnixRemote.unix_remote_root: {  # from
                    UnixRemote.unix_remote: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'remote_user_prompt',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                }
            }
        }
        return config

    @call_base_class_method_with_same_name
    def _prepare_transition_with_proxy_pc(self):
        transitions = {
            UnixRemote.proxy_pc: {
                UnixRemote.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote.unix_remote: {
                UnixRemote.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                UnixRemote.unix_remote_root: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote.unix_remote_root: {
                UnixRemote.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            }
        }
        return transitions

    @call_base_class_method_with_same_name
    def _prepare_transition_without_proxy_pc(self):
        transitions = {
            UnixRemote.unix_remote: {
                UnixRemote.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                UnixRemote.unix_remote_root: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote.unix_local: {
                UnixRemote.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote.unix_remote_root: {
                UnixRemote.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            }
        }
        return transitions

    @call_base_class_method_with_same_name
    def _prepare_state_prompts_with_proxy_pc(self):
        state_prompts = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.proxy_pc][UnixRemote.unix_remote][
                    "command_params"]["expected_prompt"],
            UnixRemote.unix_remote_root:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_remote_root][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    @call_base_class_method_with_same_name
    def _prepare_state_prompts_without_proxy_pc(self):
        state_prompts = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.unix_remote][
                    "command_params"]["expected_prompt"],
            UnixRemote.unix_remote_root:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_remote_root][
                    "command_params"]["expected_prompt"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_local][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    @call_base_class_method_with_same_name
    def _prepare_newline_chars_with_proxy_pc(self):
        newline_chars = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.proxy_pc][UnixRemote.unix_remote][
                    "command_params"]["target_newline"],
            UnixRemote.unix_remote_root:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_remote_root][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    @call_base_class_method_with_same_name
    def _prepare_newline_chars_without_proxy_pc(self):
        newline_chars = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.unix_remote][
                    "command_params"]["target_newline"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_local][
                    "command_params"]["target_newline"],
            UnixRemote.unix_remote_root:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_remote_root][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    @call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        state_hops = {
            UnixRemote.not_connected: {
                UnixRemote.unix_remote: UnixRemote.unix_local,
                UnixRemote.proxy_pc: UnixRemote.unix_local,
                UnixRemote.unix_local_root: UnixRemote.unix_local,
                UnixRemote.unix_remote_root: UnixRemote.unix_local
            },
            UnixRemote.unix_remote: {
                UnixRemote.not_connected: UnixRemote.proxy_pc,
                UnixRemote.unix_local: UnixRemote.proxy_pc,
                UnixRemote.unix_local_root: UnixRemote.unix_local
            },
            UnixRemote.proxy_pc: {
                UnixRemote.not_connected: UnixRemote.unix_local,
                UnixRemote.unix_local_root: UnixRemote.unix_local,
                UnixRemote.unix_remote_root: UnixRemote.unix_remote
            },
            UnixRemote.unix_local: {
                UnixRemote.unix_remote: UnixRemote.proxy_pc,
                UnixRemote.unix_remote_root: UnixRemote.proxy_pc
            },
            UnixRemote.unix_remote_root: {
                UnixRemote.not_connected: UnixRemote.unix_remote,
                UnixRemote.unix_local: UnixRemote.unix_remote,
                UnixRemote.unix_local_root: UnixRemote.unix_remote,
                UnixRemote.proxy_pc: UnixRemote.unix_remote,
            }
        }
        return state_hops

    @call_base_class_method_with_same_name
    def _prepare_state_hops_without_proxy_pc(self):
        state_hops = {
            UnixRemote.not_connected: {
                UnixRemote.unix_remote: UnixRemote.unix_local,
                UnixRemote.unix_local_root: UnixRemote.unix_local,
                UnixRemote.unix_remote_root: UnixRemote.unix_local,
            },
            UnixRemote.unix_local: {
                UnixRemote.unix_remote_root: UnixRemote.unix_remote
            },
            UnixRemote.unix_remote: {
                UnixRemote.not_connected: UnixRemote.unix_local,
                UnixRemote.unix_local_root: UnixRemote.unix_local
            },
            UnixRemote.unix_remote_root: {
                UnixRemote.not_connected: UnixRemote.unix_remote,
                UnixRemote.unix_local: UnixRemote.unix_remote,
                UnixRemote.unix_local_root: UnixRemote.unix_remote,
                UnixRemote.proxy_pc: UnixRemote.unix_remote,
            }
        }
        return state_hops

    def _configure_state_machine(self, sm_params):
        super(UnixRemote, self)._configure_state_machine(sm_params)

        if self.use_proxy_pc:
            self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote_root][UnixRemote.unix_remote][
                "command_params"]["expected_prompt"] = \
                self._configurations[UnixRemote.connection_hops][UnixRemote.proxy_pc][UnixRemote.unix_remote][
                    "command_params"]["expected_prompt"]
        else:
            self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote_root][UnixRemote.unix_remote][
                "command_params"]["expected_prompt"] = \
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.unix_remote][
                    "command_params"]["expected_prompt"]

    def _get_packages_for_state(self, state, observer):
        available = super(UnixRemote, self)._get_packages_for_state(state, observer)

        if not available:
            if state == UnixRemote.unix_remote or state == UnixRemote.unix_remote_root:
                available = {UnixRemote.cmds: ['moler.cmd.unix'],
                             UnixRemote.events: ['moler.events.shared', 'moler.events.unix']}
            if available:
                return available[observer]

        return available


"""
Example of device in yaml configuration file:
    - with PROXY_PC:
     UNIX_1:
       DEVICE_CLASS: moler.device.unixremote.UnixRemote
       CONNECTION_HOPS:
         PROXY_PC:
           UNIX_REMOTE:
             execute_command: ssh # default value
             command_params:
               expected_prompt: unix_remote_prompt
               host: host_ip
               login: login
               password: password
         UNIX_REMOTE:
           PROXY_PC:
             execute_command: exit # default value
             command_params:
               expected_prompt: proxy_pc_prompt
         UNIX_LOCAL:
           PROXY_PC:
             execute_command: ssh # default value
             command_params:
               expected_prompt: proxy_pc_prompt
               host: host_ip
               login: login
               password: password
    -without PROXY_PC:
      UNIX_1:
       DEVICE_CLASS: moler.device.unixremote.UnixRemote
       CONNECTION_HOPS:
         UNIX_LOCAL:
           UNIX_REMOTE:
             execute_command: ssh # default value
             command_params:
               expected_prompt: unix_remote_prompt
               host: host_ip
               login: login
               password: password
"""
