# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import re
from moler.device.textualdevice import TextualDevice
from moler.device.unixlocal import UnixLocal
from moler.device.proxy_pc2 import ProxyPc2, PROXY_PC
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name


# helper variables to improve readability of state machines
# f.ex. moler.device.textualdevice introduces state TextualDevice.not_connected = "NOT_CONNECTED"
NOT_CONNECTED = TextualDevice.not_connected
CONNECTION_HOPS = TextualDevice.connection_hops
UNIX_LOCAL = UnixLocal.unix_local
UNIX_LOCAL_ROOT = UnixLocal.unix_local_root
UNIX_REMOTE = "UNIX_REMOTE"
UNIX_REMOTE_ROOT = "UNIX_REMOTE_ROOT"


@call_base_class_method_with_same_name
class UnixRemote2(ProxyPc2):
    r"""
    UnixRemote2 device class.

    Example of device in yaml configuration file:
    - with PROXY_PC and io "terminal":
      UNIX_1:
       DEVICE_CLASS: moler.device.unixremote2.UnixRemote2
       CONNECTION_HOPS:
         UNIX_LOCAL:
           PROXY_PC:
             execute_command: ssh # default value
             command_params:
               expected_prompt: proxy_pc_prompt
               host: host_ip
               login: login
               password: password
         PROXY_PC:
           UNIX_REMOTE:
             execute_command: ssh # default value
             command_params:
               expected_prompt: unix_remote_prompt
               host: host_ip
               login: login
               password: password

    - with PROXY_PC and remote-access-io like "sshshell":
      UNIX_1:
       DEVICE_CLASS: moler.device.unixremote2.UnixRemote2
       CONNECTION_DESC:
         io_type: sshshell
         host: host_ip
         login: login
         password: password
       CONNECTION_HOPS:
         PROXY_PC:
           UNIX_REMOTE:
             execute_command: ssh # default value
             command_params:
               expected_prompt: unix_remote_prompt
               host: host_ip
               login: login
               password: password

    -without PROXY_PC and io "terminal":
      UNIX_1:
       DEVICE_CLASS: moler.device.unixremote2.UnixRemote2
       CONNECTION_HOPS:
         UNIX_LOCAL:
           UNIX_REMOTE:
             execute_command: ssh # default value
             command_params:
               expected_prompt: unix_remote_prompt
               host: host_ip
               login: login
               password: password

    -without PROXY_PC and remote-access-io like "sshshell":
      UNIX_1:
       DEVICE_CLASS: moler.device.unixremote2.UnixRemote2
       CONNECTION_DESC:
         io_type: sshshell
         host: host_ip
         login: login
         password: password
       (no need for CONNECTION_HOPS since we jump directly from NOT_CONNECTED to UNIX_REMOTE using sshshell)
    """
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
        initial_state = initial_state if initial_state is not None else UNIX_REMOTE
        super(UnixRemote2, self).__init__(name=name, io_connection=io_connection,
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
            CONNECTION_HOPS: {
                PROXY_PC: {  # from
                    UNIX_REMOTE: {  # to
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
                UNIX_REMOTE: {  # from
                    PROXY_PC: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n"
                        },
                    },
                    UNIX_REMOTE_ROOT: {  # to
                        "execute_command": "su",  # using command
                        "command_params": {  # with parameters
                            "password": "root_password",  # TODO: detect missing if sbd goes to ux-root
                            "expected_prompt": r'provide_root_prompt_in_cfg',
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                },
                UNIX_REMOTE_ROOT: {  # from
                    UNIX_REMOTE: {  # to
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
        # if self._use_local_unix_state:
        #     config['CONNECTION_HOPS'][UNIX_REMOTE][PROXY_PC]["command_params"]["expected_prompt"]
        #     is copied from  [UNIX_LOCAL][PROXY_PC]["command_params"]["expected_prompt"]
        # or if we jump NOT_CONNECTED --open connection-> PROXY_PC then prompt will be detected
        return config

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_without_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        if self._use_local_unix_state:
            config = {
                CONNECTION_HOPS: {
                    UNIX_LOCAL: {  # from
                        UNIX_REMOTE: {  # to
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
                    UNIX_REMOTE: {  # from
                        UNIX_LOCAL: {  # to
                            "execute_command": "exit",  # using command
                            "command_params": {  # with parameters
                                "expected_prompt": r'^moler_bash#',
                                "target_newline": "\n"
                            },
                            "required_command_params": [
                            ]
                        },
                        UNIX_REMOTE_ROOT: {  # to
                            "execute_command": "su",  # using command
                            "command_params": {  # with parameters
                                "password": "root_password",
                                "expected_prompt": r'provide_root_prompt_in_cfg',
                                "target_newline": "\n"
                            },
                            "required_command_params": [
                            ]
                        },
                    },
                    UNIX_REMOTE_ROOT: {  # from
                        UNIX_REMOTE: {  # to
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
        else:
            config = {
                CONNECTION_HOPS: {
                    UNIX_REMOTE: {  # from
                        UNIX_REMOTE_ROOT: {  # to
                            "execute_command": "su",  # using command
                            "command_params": {  # with parameters
                                "password": "root_password",
                                "expected_prompt": r'provide_root_prompt_in_cfg',
                                "target_newline": "\n"
                            },
                            "required_command_params": [
                            ]
                        },
                    },
                    UNIX_REMOTE_ROOT: {  # from
                        UNIX_REMOTE: {  # to
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
            PROXY_PC: {
                UNIX_REMOTE: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UNIX_REMOTE: {
                PROXY_PC: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                UNIX_REMOTE_ROOT: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UNIX_REMOTE_ROOT: {
                UNIX_REMOTE: {
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
        if self._use_local_unix_state:
            transitions = {
                UNIX_LOCAL: {
                    UNIX_REMOTE: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    }
                },
                UNIX_REMOTE: {
                    UNIX_LOCAL: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    },
                    UNIX_REMOTE_ROOT: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    }
                },
                UNIX_REMOTE_ROOT: {
                    UNIX_REMOTE: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    }
                }
            }
        else:  # directly from NOT_CONNECTED to UNIX_REMOTE
            transitions = {
                NOT_CONNECTED: {
                    UNIX_REMOTE: {
                        "action": [
                            "_open_connection"
                        ],
                    }
                },
                UNIX_REMOTE: {
                    NOT_CONNECTED: {
                        "action": [
                            "_close_connection"
                        ],
                    },
                    UNIX_REMOTE_ROOT: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    }
                },
                UNIX_REMOTE_ROOT: {
                    UNIX_REMOTE: {
                        "action": [
                            "_execute_command_to_change_state"
                        ],
                    }
                }
            }
        return transitions

    def on_connection_made(self, connection):
        """
        Execute action when connection made.
        :param connection: device connection.
        :return: Nothing.
        """
        if self._use_local_unix_state:
            super(UnixRemote2, self).on_connection_made(connection)
        elif self._use_proxy_pc:
            self._set_state(PROXY_PC)
            self._detect_after_open_prompt(self._set_after_open_prompt)
        else:
            self._set_state(UNIX_REMOTE)
            self._detect_after_open_prompt(self._set_after_open_prompt)

    def _set_after_open_prompt(self, event):
        occurrence = event.get_last_occurrence()
        prompt = occurrence['groups'][0]
        state = self._get_current_state()
        with self._state_prompts_lock:
            self._state_prompts[state] = re.escape(prompt.rstrip())
            if state == UNIX_REMOTE:
                self._update_depending_on_ux_prompt()
            elif state == PROXY_PC:
                self._update_depending_on_proxy_prompt()

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_with_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine with proxy_pc state.
        :return: textual prompt for each state with proxy_pc state.
        """
        hops_cfg = self._configurations[CONNECTION_HOPS]
        state_prompts = {
            UNIX_REMOTE:
                hops_cfg[PROXY_PC][UNIX_REMOTE]["command_params"]["expected_prompt"],
            UNIX_REMOTE_ROOT:
                hops_cfg[UNIX_REMOTE][UNIX_REMOTE_ROOT]["command_params"]["expected_prompt"],
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_without_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        hops_cfg = self._configurations[CONNECTION_HOPS]
        if self._use_local_unix_state:
            state_prompts = {
                UNIX_REMOTE:
                    hops_cfg[UNIX_LOCAL][UNIX_REMOTE]["command_params"]["expected_prompt"],
                UNIX_REMOTE_ROOT:
                    hops_cfg[UNIX_REMOTE][UNIX_REMOTE_ROOT]["command_params"]["expected_prompt"],
                UNIX_LOCAL:
                    hops_cfg[UNIX_REMOTE][UNIX_LOCAL]["command_params"]["expected_prompt"],
            }
        else:  # directly from NOT_CONNECTED to UNIX_REMOTE via open connection
            state_prompts = {
                # UNIX_REMOTE: detect prompt after establishing connection: _detect_after_open_prompt()
                UNIX_REMOTE_ROOT:
                    hops_cfg[UNIX_REMOTE][UNIX_REMOTE_ROOT]["command_params"]["expected_prompt"],
            }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_with_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine with proxy_pc state.
        :return: newline char for each state with proxy_pc state.
        """
        hops_cfg = self._configurations[CONNECTION_HOPS]
        newline_chars = {
            UNIX_REMOTE:
                hops_cfg[PROXY_PC][UNIX_REMOTE]["command_params"]["target_newline"],
            UNIX_REMOTE_ROOT:
                hops_cfg[UNIX_REMOTE][UNIX_REMOTE_ROOT]["command_params"]["target_newline"],
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        hops_cfg = self._configurations[CONNECTION_HOPS]
        if self._use_local_unix_state:
            newline_chars = {
                UNIX_REMOTE:
                    hops_cfg[UNIX_LOCAL][UNIX_REMOTE]["command_params"]["target_newline"],
                UNIX_LOCAL:
                    hops_cfg[UNIX_REMOTE][UNIX_LOCAL]["command_params"]["target_newline"],
                UNIX_REMOTE_ROOT:
                    hops_cfg[UNIX_REMOTE][UNIX_REMOTE_ROOT]["command_params"]["target_newline"],
            }
        else:  # directly from NOT_CONNECTED to UNIX_REMOTE via open connection
            newline_chars = {
                # UNIX_REMOTE: TODO: hot to get it?
                UNIX_REMOTE_ROOT:
                    hops_cfg[UNIX_REMOTE][UNIX_REMOTE_ROOT]["command_params"]["target_newline"],
            }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine with proxy_pc state.
        :return: non direct transitions for each state with proxy_pc state.
        """
        if self._use_local_unix_state:
            state_hops = {
                NOT_CONNECTED: {
                    UNIX_REMOTE: UNIX_LOCAL,
                    PROXY_PC: UNIX_LOCAL,
                    UNIX_LOCAL_ROOT: UNIX_LOCAL,
                    UNIX_REMOTE_ROOT: UNIX_LOCAL
                },
                UNIX_LOCAL: {
                    UNIX_REMOTE: PROXY_PC,
                    UNIX_REMOTE_ROOT: PROXY_PC
                },
                UNIX_LOCAL_ROOT: {
                    UNIX_REMOTE: UNIX_LOCAL,
                    UNIX_REMOTE_ROOT: UNIX_LOCAL
                },
                PROXY_PC: {
                    NOT_CONNECTED: UNIX_LOCAL,
                    UNIX_LOCAL_ROOT: UNIX_LOCAL,
                    UNIX_REMOTE_ROOT: UNIX_REMOTE
                },
                UNIX_REMOTE: {
                    NOT_CONNECTED: PROXY_PC,
                    UNIX_LOCAL: PROXY_PC,
                    UNIX_LOCAL_ROOT: PROXY_PC
                },
                UNIX_REMOTE_ROOT: {
                    NOT_CONNECTED: UNIX_REMOTE,
                    UNIX_LOCAL: UNIX_REMOTE,
                    UNIX_LOCAL_ROOT: UNIX_REMOTE,
                    PROXY_PC: UNIX_REMOTE,
                }
            }
        else:
            state_hops = {
                NOT_CONNECTED: {
                    UNIX_REMOTE: PROXY_PC,
                    UNIX_REMOTE_ROOT: PROXY_PC
                },
                PROXY_PC: {
                    UNIX_REMOTE_ROOT: UNIX_REMOTE
                },
                UNIX_REMOTE: {
                    NOT_CONNECTED: PROXY_PC,
                },
                UNIX_REMOTE_ROOT: {
                    NOT_CONNECTED: UNIX_REMOTE,
                    PROXY_PC: UNIX_REMOTE,
                }
            }
        return state_hops

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_without_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine without proxy_pc state.
        :return: non direct transitions for each state without proxy_pc state.
        """
        if self._use_local_unix_state:
            state_hops = {
                NOT_CONNECTED: {
                    UNIX_REMOTE: UNIX_LOCAL,
                    UNIX_LOCAL_ROOT: UNIX_LOCAL,
                    UNIX_REMOTE_ROOT: UNIX_LOCAL,
                },
                UNIX_LOCAL: {
                    UNIX_REMOTE_ROOT: UNIX_REMOTE
                },
                UNIX_LOCAL_ROOT: {
                    UNIX_REMOTE: UNIX_LOCAL,
                    UNIX_REMOTE_ROOT: UNIX_LOCAL
                },
                UNIX_REMOTE: {
                    NOT_CONNECTED: UNIX_LOCAL,
                    UNIX_LOCAL_ROOT: UNIX_LOCAL
                },
                UNIX_REMOTE_ROOT: {
                    NOT_CONNECTED: UNIX_REMOTE,
                    UNIX_LOCAL: UNIX_REMOTE,
                    UNIX_LOCAL_ROOT: UNIX_REMOTE,
                }
            }
        else:
            state_hops = {
                NOT_CONNECTED: {
                    UNIX_REMOTE_ROOT: UNIX_REMOTE,
                },
                UNIX_REMOTE_ROOT: {
                    NOT_CONNECTED: UNIX_REMOTE,
                }
            }
        return state_hops

    def _configure_state_machine(self, sm_params):
        """
        Configure device State Machine.
        :param sm_params: dict with parameters of state machine for device.
        :return: Nothing.
        """
        super(UnixRemote2, self)._configure_state_machine(sm_params)
        self._update_depending_on_ux_prompt()
        self._update_depending_on_proxy_prompt()

    def _update_depending_on_ux_prompt(self):
        self._update_ux_root2ux()

    def _update_depending_on_proxy_prompt(self):
        self._update_ux2proxy()

    def _update_ux_root2ux(self):
        hops_cfg = self._configurations[CONNECTION_HOPS]
        if UNIX_REMOTE in self._state_prompts:
            ux_remote_prompt = self._state_prompts[UNIX_REMOTE]
            hops_cfg[UNIX_REMOTE_ROOT][UNIX_REMOTE]["command_params"]["expected_prompt"] = ux_remote_prompt

    def _update_ux2proxy(self):
        hops_cfg = self._configurations[CONNECTION_HOPS]
        if PROXY_PC in self._state_prompts:
            proxy_prompt = self._state_prompts[PROXY_PC]
            hops_cfg[UNIX_REMOTE][PROXY_PC]["command_params"]["expected_prompt"] = proxy_prompt

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages contain cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = super(UnixRemote2, self)._get_packages_for_state(state, observer)

        if not available:
            if (state == UNIX_REMOTE) or (state == UNIX_REMOTE_ROOT):
                available = {UnixRemote2.cmds: ['moler.cmd.unix'],
                             UnixRemote2.events: ['moler.events.shared', 'moler.events.unix']}
            if available:
                return available[observer]

        return available
