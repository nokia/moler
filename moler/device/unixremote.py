# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

from moler.device import TextualDevice


# TODO: name, logger/logger_name as param
class UnixRemote(TextualDevice):
    remote = "REMOTE"

    def __init__(self, io_connection=None, io_type=None, variant=None):
        """
        Create Unix device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        """
        super(UnixRemote, self).__init__(io_connection=io_connection, io_type=io_type, variant=variant)

        self._configurations = dict()
        self._collect_cmds_for_state_machine()
        self._collect_events_for_state_machine()

    def _prepare_transitions(self):
        transitions = {
            UnixRemote.remote: {
                TextualDevice.connected: {
                    "action": [
                        "_disconnect_from_remote_host"
                    ],
                }
            },
            TextualDevice.connected: {
                UnixRemote.remote: {
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
            UnixRemote.remote: r'^root@debdev:~#',
        }

        self._state_prompts.update(state_prompts)
        super(UnixRemote, self)._prepare_state_prompts()

    def _prepare_state_hops(self):
        state_hops = {
            TextualDevice.not_connected: {
                UnixRemote.remote: TextualDevice.connected,
            },
            UnixRemote.remote: {
                TextualDevice.not_connected: TextualDevice.connected
            }
        }
        self._state_hops.update(state_hops)
        super(UnixRemote, self)._prepare_state_hops()

    def _get_packages_for_state(self, state, observer):
        if state == TextualDevice.connected:
            available = {TextualDevice.cmds: ['moler.cmd.unix'],
                         TextualDevice.events: ['moler.events.unix']}
            return available[observer]
        elif state == UnixRemote.remote:
            available = {TextualDevice.cmds: ['moler.cmd.unix'],
                         TextualDevice.events: ['moler.events.unix']}
            return available[observer]
        return []

    def _connect_to_remote_host(self, source_state, dest_state, timeout=-1):
        configurations = self.get_configurations(source_state=source_state, dest_state=dest_state)
        # will be telnet or ssh
        connection_type = configurations.pop("execute_command")

        command_timeout = self.calc_timeout_for_command(timeout, configurations)
        establish_connection = self.get_cmd(cmd_name=connection_type, **configurations)
        establish_connection(timeout=command_timeout)

    def _disconnect_from_remote_host(self, source_state, dest_state, timeout=-1):
        configurations = self.get_configurations(source_state=source_state, dest_state=dest_state)
        # will be exit
        close_connection = configurations.pop("execute_command")

        command_timeout = self.calc_timeout_for_command(timeout, configurations)
        end_connection = self.get_cmd(cmd_name=close_connection, **configurations)
        end_connection(timeout=command_timeout)

    # TODO: Not official API
    def get_configurations(self, source_state, dest_state):
        if source_state and dest_state:
            return self._configurations[source_state][dest_state]
        else:
            return self._configurations

    def configure_state_machine(self, configurations):
        self._configurations = configurations
