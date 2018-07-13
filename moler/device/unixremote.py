# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging

from moler.device.unixlocal import UnixLocal


# TODO: name, logger/logger_name as param
class UnixRemote(UnixLocal):
    unix_remote = "UNIX_REMOTE"

    def __init__(self, io_connection=None, io_type=None, variant=None, sm_params=dict()):
        """
        Create Unix device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        """
        super(UnixRemote, self).__init__(io_connection=io_connection, io_type=io_type, variant=variant,
                                         sm_params=sm_params)
        self.logger = logging.getLogger('moler.unixlocal')
        self._collect_cmds_for_state_machine()
        self._collect_events_for_state_machine()

    def _get_default_sm_configuration(self):
        config = {
            "CONNECTION_HOPS": {
                "UNIX_LOCAL": {  # from
                    "UNIX_REMOTE": {  # to
                        "execute_command": "ssh",  # using command
                        "command_params": {  # with parameters
                            "host": "localhost",
                            "login": "root",
                            "expected_prompt": 'root@debdev:~#'
                        }
                    }
                },
                "UNIX_REMOTE": {  # from
                    "UNIX_LOCAL": {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^bash-\d+\.*\d*'
                        }
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
            UnixRemote.unix_remote: r'^root@debdev:~#',
        }

        self._state_prompts.update(state_prompts)
        super(UnixRemote, self)._prepare_state_prompts()

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
        connection_type = configurations.pop("execute_command")
        connection_type_parmas = configurations.pop("command_params")

        command_timeout = self.calc_timeout_for_command(timeout, connection_type_parmas)
        establish_connection = self.get_cmd(cmd_name=connection_type, **connection_type_parmas)
        establish_connection(timeout=command_timeout)

    def _disconnect_from_remote_host(self, source_state, dest_state, timeout=-1):
        configurations = self.get_configurations(source_state=source_state, dest_state=dest_state)
        # will be exit
        close_connection = configurations.pop("execute_command")
        close_connection_params = configurations.pop("command_params")

        command_timeout = self.calc_timeout_for_command(timeout, close_connection_params)
        end_connection = self.get_cmd(cmd_name=close_connection, **close_connection_params)
        end_connection(timeout=command_timeout)

    def get_configurations(self, source_state, dest_state):
        if source_state and dest_state:
            return self._configurations["CONNECTION_HOPS"][source_state][dest_state]
