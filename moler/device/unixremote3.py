# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2025, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.device.proxy_pc3 import ProxyPc3
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name
from moler.exceptions import DeviceFailure


@call_base_class_method_with_same_name
class UnixRemote3(ProxyPc3):
    r"""
    UnixRemote device class.


    ::


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

    unix_remote = "UNIX_REMOTE"
    unix_remote_root = "UNIX_REMOTE_ROOT"

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
        initial_state = initial_state if initial_state is not None else UnixRemote3.unix_remote
        super(UnixRemote3, self).__init__(name=name, io_connection=io_connection,
                                          io_type=io_type, variant=variant,
                                          io_constructor_kwargs=io_constructor_kwargs,
                                          sm_params=sm_params, initial_state=initial_state,
                                          lazy_cmds_events=lazy_cmds_events)

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration with proxy_pc state.
        :return: default sm configuration with proxy_pc state.
        """
        config = {
            UnixRemote3.connection_hops: {
                UnixRemote3.proxy_pc: {  # from
                    UnixRemote3.unix_remote: {  # to
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
                UnixRemote3.unix_remote: {  # from
                    UnixRemote3.proxy_pc: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                            "expected_prompt"
                        ]
                    },
                    UnixRemote3.unix_remote_root: {  # to
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
                UnixRemote3.unix_remote_root: {  # from
                    UnixRemote3.unix_remote: {  # to
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

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_without_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        config = {
            UnixRemote3.connection_hops: {
                UnixRemote3.unix_local: {  # from
                    UnixRemote3.unix_remote: {  # to
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
                UnixRemote3.unix_remote: {  # from
                    UnixRemote3.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^moler_bash#',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                    UnixRemote3.unix_remote_root: {  # to
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
                UnixRemote3.unix_remote_root: {  # from
                    UnixRemote3.unix_remote: {  # to
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

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_with_proxy_pc(self):
        """
        Prepare transitions to change states with proxy_pc state.
        :return: transitions with proxy_pc state.
        """
        transitions = {
            UnixRemote3.proxy_pc: {
                UnixRemote3.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote3.unix_remote: {
                UnixRemote3.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                UnixRemote3.unix_remote_root: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote3.unix_remote_root: {
                UnixRemote3.unix_remote: {
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
            UnixRemote3.unix_remote: {
                UnixRemote3.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                UnixRemote3.unix_remote_root: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote3.unix_local: {
                UnixRemote3.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote3.unix_remote_root: {
                UnixRemote3.unix_remote: {
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
            UnixRemote3.unix_remote:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.proxy_pc][UnixRemote3.unix_remote][
                    "command_params"]["expected_prompt"],
            UnixRemote3.unix_remote_root:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote][UnixRemote3.unix_remote_root][
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
            UnixRemote3.unix_remote:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_local][UnixRemote3.unix_remote][
                    "command_params"]["expected_prompt"],
            UnixRemote3.unix_remote_root:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote][UnixRemote3.unix_remote_root][
                    "command_params"]["expected_prompt"],
            UnixRemote3.unix_local:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote][UnixRemote3.unix_local][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_with_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine with proxy_pc state.
        :return: newline char for each state with proxy_pc state.
        """
        newline_chars = {
            UnixRemote3.unix_remote:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.proxy_pc][UnixRemote3.unix_remote][
                    "command_params"]["target_newline"],
            UnixRemote3.unix_remote_root:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote][UnixRemote3.unix_remote_root][
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
            UnixRemote3.unix_remote:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_local][UnixRemote3.unix_remote][
                    "command_params"]["target_newline"],
            UnixRemote3.unix_local:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote][UnixRemote3.unix_local][
                    "command_params"]["target_newline"],
            UnixRemote3.unix_remote_root:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote][UnixRemote3.unix_remote_root][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine with proxy_pc state.
        :return: non direct transitions for each state with proxy_pc state.
        """
        state_hops = {
            UnixRemote3.not_connected: {
                UnixRemote3.unix_remote: UnixRemote3.unix_local,
                UnixRemote3.proxy_pc: UnixRemote3.unix_local,
                UnixRemote3.unix_local_root: UnixRemote3.unix_local,
                UnixRemote3.unix_remote_root: UnixRemote3.unix_local
            },
            UnixRemote3.unix_remote: {
                UnixRemote3.not_connected: UnixRemote3.proxy_pc,
                UnixRemote3.unix_local: UnixRemote3.proxy_pc,
                UnixRemote3.unix_local_root: UnixRemote3.proxy_pc
            },
            UnixRemote3.unix_local_root: {
                UnixRemote3.not_connected: UnixRemote3.unix_local,
                UnixRemote3.unix_remote: UnixRemote3.unix_local,
                UnixRemote3.unix_remote_root: UnixRemote3.unix_local
            },
            UnixRemote3.proxy_pc: {
                UnixRemote3.not_connected: UnixRemote3.unix_local,
                UnixRemote3.unix_local_root: UnixRemote3.unix_local,
                UnixRemote3.unix_remote_root: UnixRemote3.unix_remote
            },
            UnixRemote3.unix_local: {
                UnixRemote3.unix_remote: UnixRemote3.proxy_pc,
                UnixRemote3.unix_remote_root: UnixRemote3.proxy_pc
            },
            UnixRemote3.unix_remote_root: {
                UnixRemote3.not_connected: UnixRemote3.unix_remote,
                UnixRemote3.unix_local: UnixRemote3.unix_remote,
                UnixRemote3.unix_local_root: UnixRemote3.unix_remote,
                UnixRemote3.proxy_pc: UnixRemote3.unix_remote,
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
            UnixRemote3.not_connected: {
                UnixRemote3.unix_remote: UnixRemote3.unix_local,
                UnixRemote3.unix_local_root: UnixRemote3.unix_local,
                UnixRemote3.unix_remote_root: UnixRemote3.unix_local,
            },
            UnixRemote3.unix_local: {
                UnixRemote3.unix_remote_root: UnixRemote3.unix_remote
            },
            UnixRemote3.unix_local_root: {
                UnixRemote3.not_connected: UnixRemote3.unix_local,
                UnixRemote3.unix_remote: UnixRemote3.unix_local,
                UnixRemote3.unix_remote_root: UnixRemote3.unix_local
            },
            UnixRemote3.unix_remote: {
                UnixRemote3.not_connected: UnixRemote3.unix_local,
                UnixRemote3.unix_local_root: UnixRemote3.unix_local
            },
            UnixRemote3.unix_remote_root: {
                UnixRemote3.not_connected: UnixRemote3.unix_remote,
                UnixRemote3.unix_local: UnixRemote3.unix_remote,
                UnixRemote3.unix_local_root: UnixRemote3.unix_remote,
            }
        }
        return state_hops

    def _configure_state_machine(self, sm_params):
        """
        Configure device State Machine.
        :param sm_params: dict with parameters of state machine for device.
        :return: None
        """
        super(UnixRemote3, self)._configure_state_machine(sm_params)
        self._overwrite_prompts()

    def _overwrite_prompts(self):
        """
        Overwrite prompts for some states to easily configure the SM.
        """
        try:
            if self._use_proxy_pc:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote][UnixRemote3.proxy_pc][
                    "command_params"]["expected_prompt"] = \
                    self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_local][UnixRemote3.proxy_pc][
                    "command_params"]["expected_prompt"]
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote_root][UnixRemote3.unix_remote][
                    "command_params"]["expected_prompt"] = \
                    self._configurations[UnixRemote3.connection_hops][UnixRemote3.proxy_pc][UnixRemote3.unix_remote][
                        "command_params"]["expected_prompt"]
            else:
                self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_remote_root][UnixRemote3.unix_remote][
                    "command_params"]["expected_prompt"] = \
                    self._configurations[UnixRemote3.connection_hops][UnixRemote3.unix_local][UnixRemote3.unix_remote][
                        "command_params"]["expected_prompt"]
        except KeyError as ke:
            raise DeviceFailure(
                device=self.__class__.__name__,
                message=f"Wrong configuration. Cannot get prompts. {ke} {repr(ke)}"
            )

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages contain cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = super(UnixRemote3, self)._get_packages_for_state(state, observer)

        if not available:
            if state == UnixRemote3.unix_remote or state == UnixRemote3.unix_remote_root:
                available = {UnixRemote3.cmds: ['moler.cmd.unix'],
                             UnixRemote3.events: ['moler.events.shared', 'moler.events.unix']}
            if available:
                return available[observer]

        return available
