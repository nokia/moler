# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.device.unixlocal import UnixLocal


# TODO: name, logger/logger_name as param
class UnixRemote(UnixLocal):
    unix_remote = "UNIX_REMOTE"

    def __init__(self, name=None, io_connection=None, io_type=None, variant=None, sm_params=dict()):
        """
        Create Unix device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        """
        sm_params = sm_params.copy()
        super(UnixRemote, self).__init__(name=name, io_connection=io_connection, io_type=io_type, variant=variant,
                                         sm_params=sm_params)

    def _get_default_sm_configuration(self):
        config = {
            UnixRemote.connection_hops: {
                UnixRemote.unix_local: {  # from
                    UnixRemote.unix_remote: {  # to
                        "execute_command": "ssh",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\r\n"
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
                            "target_newline": "\r\n"
                        },
                        "required_command_params": [
                        ]
                    }
                }
            }
        }
        return config

    def _prepare_transitions(self):
        transitions = {
            UnixRemote.unix_remote: {
                UnixLocal.unix_local: {
                    "action": [
                        "_disconnect_from_remote_host"
                    ],
                }
            },
            UnixLocal.unix_local: {
                UnixRemote.unix_remote: {
                    "action": [
                        "_connect_to_remote_host"
                    ],
                }
            },
        }

        self._add_transitions(transitions=transitions)
        super(UnixRemote, self)._prepare_transitions()

    def _prepare_state_prompts(self):
        state_prompts = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.unix_remote][
                    "command_params"]["expected_prompt"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_local][
                    "command_params"]["expected_prompt"],
        }

        self._state_prompts.update(state_prompts)
        super(UnixRemote, self)._prepare_state_prompts()

    def _prepare_newline_chars(self):
        newline_chars = {
            UnixRemote.unix_remote:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_local][UnixRemote.unix_remote][
                    "command_params"]["target_newline"],
            UnixRemote.unix_local:
                self._configurations[UnixRemote.connection_hops][UnixRemote.unix_remote][UnixRemote.unix_local][
                    "command_params"]["target_newline"],
        }
        self._newline_chars.update(newline_chars)
        super(UnixRemote, self)._prepare_newline_chars()

    def _prepare_state_hops(self):
        state_hops = {
            UnixLocal.not_connected: {
                UnixRemote.unix_remote: UnixLocal.unix_local,
            },
            UnixRemote.unix_remote: {
                UnixLocal.not_connected: UnixLocal.unix_local
            }
        }
        self._state_hops.update(state_hops)
        super(UnixRemote, self)._prepare_state_hops()

    def _get_packages_for_state(self, state, observer):
        if state == UnixLocal.unix_local:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
            return available[observer]
        elif state == UnixRemote.unix_remote:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
            return available[observer]
        return []

    def _connect_to_remote_host(self, source_state, dest_state, timeout=-1):
        configurations = self.get_configurations(source_state=source_state, dest_state=dest_state)
        # will be telnet or ssh
        connection_type = configurations["execute_command"]
        connection_type_parmas = configurations["command_params"]

        command_timeout = self.calc_timeout_for_command(timeout, connection_type_parmas)
        establish_connection = self.get_cmd(cmd_name=connection_type, cmd_params=connection_type_parmas)
        establish_connection(timeout=command_timeout)

    def _disconnect_from_remote_host(self, source_state, dest_state, timeout=-1):
        configurations = self.get_configurations(source_state=source_state, dest_state=dest_state)
        # will be exit
        close_connection = configurations["execute_command"]
        close_connection_params = configurations["command_params"]

        command_timeout = self.calc_timeout_for_command(timeout, close_connection_params)
        end_connection = self.get_cmd(cmd_name=close_connection, cmd_params=close_connection_params)
        end_connection(timeout=command_timeout)
