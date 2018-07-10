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
class Unix(TextualDevice):
    unix = "UNIX"

    def __init__(self, io_connection=None, io_type=None, variant=None):
        """
        Create Unix device communicating over io_connection

        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: External-IO connection connection type
        :param variant: External-IO connection variant
        """
        super(Unix, self).__init__(io_connection=io_connection, io_type=io_type, variant=variant)

        self._prompts_events = []
        self._configurations = dict()
        self._collect_cmds_for_state_machine()
        self._collect_events_for_state_machine()
        self._run_prompts_observers()

    def _prepare_transitions(self):
        super(Unix, self)._prepare_transitions()

        transitions = {
            Unix.unix: {
                TextualDevice.connected: {
                    "action": [
                        "_exit_from_remote_host"
                    ],
                }
            },
            TextualDevice.connected: {
                Unix.unix: {
                    "action": [
                        "_connect_to_remote_host"
                    ],
                }
            },
        }

        self._add_transitions(transitions=transitions)

    def _prepare_state_prompts(self):
        super(Unix, self)._prepare_state_prompts()

        state_prompts = {
            Unix.unix: r'root@debdev:~#',
            TextualDevice.connected: r'bash-\d+\.*\d*',
        }

        self._state_prompts.update(state_prompts)

    def _prepare_state_hops(self):
        super(Unix, self)._prepare_state_hops()

        state_hops = {
            TextualDevice.not_connected: {
                Unix.unix: TextualDevice.connected,
            },
            Unix.unix: {
                TextualDevice.not_connected: TextualDevice.connected
            }
        }

        self._state_hops.update(state_hops)

    def _get_packages_for_state(self, state, observer):
        if state == Unix.connected:
            available = {Unix.cmds: ['moler.cmd.unix'],
                         Unix.events: ['moler.events.unix']}
            return available[observer]
        elif state == Unix.unix:
            available = {Unix.cmds: ['moler.cmd.unix'],
                         Unix.events: ['moler.events.unix']}
            return available[observer]
        return []

    def _connect_to_remote_host(self, source_state, dest_state):
        configurations = self.get_configurations(dest_state)
        connection_type = configurations.pop("connection_type")

        cmd = self.get_cmd(cmd_name=connection_type, **configurations)
        cmd()

    def _exit_from_remote_host(self, current_state=None, dest_state=None):
        exit = self.get_cmd(cmd_name='exit', prompt=r'^bash-\d+\.*\d*')
        exit()

    def _prompt_callback(self, event, **kwargs):
        self._set_state(kwargs["state"])

    def get_configurations(self, state=None):
        if state is None:
            return self._configurations
        else:
            return self._configurations[state]

    def set_configurations(self, configurations):
        self._configurations = configurations

    def _run_prompts_observers(self):
        for state in self._state_prompts.keys():
            prompt_event = self.get_event(event_name="wait4prompt",
                                          prompt=self._state_prompts[state],
                                          till_occurs_times=-1)

            prompt_event.subscribe(callback=self._prompt_callback,
                                   callback_params={"state": state})

            prompt_event.start()
            self._prompts_events.append(prompt_event)
