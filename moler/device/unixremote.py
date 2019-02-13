# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.device.unixlocal import UnixLocal


# TODO: name, logger/logger_name as param
class UnixRemote(UnixLocal):
    unix_remote = "UNIX_REMOTE"
    proxy_pc = "PROXY_PC"

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
        self.use_proxy_pc = self._is_proxy_pc_in_sm_params(sm_params, UnixRemote.proxy_pc)
        super(UnixRemote, self).__init__(name=name, io_connection=io_connection,
                                         io_type=io_type, variant=variant,
                                         io_constructor_kwargs=io_constructor_kwargs,
                                         sm_params=sm_params, initial_state=initial_state)

    def _get_default_sm_configuration(self):
        if self.use_proxy_pc:
            config = self._get_default_sm_configuration_with_proxy_pc()
        else:
            config = self._get_default_sm_configuration_without_proxy_pc()
        return config

    def _get_default_sm_configuration_with_proxy_pc(self):
        config = {
            UnixRemote.connection_hops: {
                UnixRemote.unix_local: {  # from
                    UnixRemote.proxy_pc: {  # to
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
                    UnixRemote.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n",
                            "expected_prompt": r'^moler_bash#',
                        },
                        "required_command_params": [
                        ]
                    }
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
                    }
                },
            }
        }
        return config

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
                    }
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
                    }
                }
            }
        }
        return config

    def _prepare_transitions(self):
        super(UnixRemote, self)._prepare_transitions()
        if self.use_proxy_pc:
            transitions = self._prepare_transition_with_proxy_pc()
        else:
            transitions = self._prepare_transition_without_proxy_pc()

        self._add_transitions(transitions=transitions)

    def _prepare_transition_with_proxy_pc(self):
        transitions = {
            UnixRemote.unix_local: {
                UnixRemote.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixRemote.proxy_pc: {
                UnixRemote.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
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
                }
            },
        }
        return transitions

    def _prepare_transition_without_proxy_pc(self):
        transitions = {
            UnixRemote.unix_remote: {
                UnixLocal.unix_local: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            UnixLocal.unix_local: {
                UnixRemote.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
        }
        return transitions

    def _prepare_state_prompts(self):
        super(UnixRemote, self)._prepare_state_prompts()

        if self.use_proxy_pc:
            state_prompts = self._prepare_state_prompts_with_proxy_pc()
        else:
            state_prompts = self._prepare_state_prompts_without_proxy_pc()

        self._update_dict(self._state_prompts, state_prompts)

    def _prepare_state_prompts_with_proxy_pc(self):
        state_prompts = {
            UnixRemote.proxy_pc:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.proxy_pc][
                    "command_params"]["expected_prompt"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.proxy_pc][UnixRemote.unix_local][
                    "command_params"]["expected_prompt"],
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.proxy_pc][UnixRemote.unix_remote][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    def _prepare_state_prompts_without_proxy_pc(self):
        state_prompts = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.unix_remote][
                    "command_params"]["expected_prompt"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_local][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    def _prepare_newline_chars(self):
        super(UnixRemote, self)._prepare_newline_chars()

        if self.use_proxy_pc:
            newline_chars = self._prepare_newline_chars_with_proxy_pc()
        else:
            newline_chars = self._prepare_newline_chars_without_proxy_pc()

        self._update_dict(self._newline_chars, newline_chars)

    def _prepare_newline_chars_with_proxy_pc(self):
        newline_chars = {
            UnixRemote.proxy_pc:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.proxy_pc][
                    "command_params"]["target_newline"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.proxy_pc][UnixRemote.unix_local][
                    "command_params"]["target_newline"],
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.proxy_pc][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    def _prepare_newline_chars_without_proxy_pc(self):
        newline_chars = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.unix_remote][
                    "command_params"]["target_newline"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_local][
                    "command_params"]["target_newline"],
        }
        return newline_chars

    def _prepare_state_hops(self):
        super(UnixRemote, self)._prepare_state_hops()

        if self.use_proxy_pc:
            state_hops = self._prepare_state_hops_with_proxy_pc()
        else:
            state_hops = self._prepare_state_hops_without_proxy_pc()

        self._update_dict(self._state_hops, state_hops)

    def _prepare_state_hops_with_proxy_pc(self):
        state_hops = {
            UnixLocal.not_connected: {
                UnixRemote.unix_remote: UnixRemote.unix_local,
                UnixRemote.proxy_pc: UnixRemote.unix_local,
            },
            UnixRemote.unix_remote: {
                UnixRemote.not_connected: UnixRemote.proxy_pc,
                UnixRemote.unix_local: UnixRemote.proxy_pc,
            },
            UnixRemote.proxy_pc: {
                UnixRemote.not_connected: UnixRemote.unix_local
            },
            UnixRemote.unix_local: {
                UnixRemote.unix_remote: UnixRemote.proxy_pc
            },
        }
        return state_hops

    def _prepare_state_hops_without_proxy_pc(self):
        state_hops = {
            UnixLocal.not_connected: {
                UnixRemote.unix_remote: UnixLocal.unix_local,
            },
            UnixRemote.unix_remote: {
                UnixLocal.not_connected: UnixLocal.unix_local
            }
        }
        return state_hops

    def _get_packages_for_state(self, state, observer):
        if state == UnixLocal.unix_local:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
            return available[observer]
        elif state == UnixRemote.unix_remote:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
            return available[observer]
        elif state == UnixRemote.proxy_pc:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
            return available[observer]
        return []

    def _execute_command_to_change_state(self, source_state, dest_state, timeout=-1):
        configurations = self.get_configurations(source_state=source_state, dest_state=dest_state)

        command_name = configurations["execute_command"]
        command_params = configurations["command_params"]

        command_timeout = self.calc_timeout_for_command(timeout, command_params)
        command = self.get_cmd(cmd_name=command_name, cmd_params=command_params)
        command(timeout=command_timeout)


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
           UNIX_REMOTE:
             execute_command: ssh # default value
             command_params:
               expected_prompt: unix_remote_prompt
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
