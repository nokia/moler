# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

from moler.device.textualdevice import TextualDevice

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'


# TODO: name, logger/logger_name as param
class UnixLocal(TextualDevice):
    unix_local = "UNIX_LOCAL"

    def __init__(self, sm_params=dict(), name=None, io_connection=None, io_type=None, variant=None):
        sm_params = sm_params.copy()
        super(UnixLocal, self).__init__(sm_params=sm_params, name=name, io_connection=io_connection, io_type=io_type,
                                        variant=variant)

    def _prepare_transitions(self):
        super(UnixLocal, self)._prepare_transitions()

        transitions = {
            UnixLocal.unix_local: {
                UnixLocal.not_connected: {
                    "action": [
                        "_open_connection"
                    ],
                },
            },
            UnixLocal.not_connected: {
                UnixLocal.unix_local: {
                    "action": [
                        "_close_connection"
                    ],
                },
            }
        }
        self._add_transitions(transitions=transitions)

    def _prepare_state_prompts(self):
        super(UnixLocal, self)._prepare_state_prompts()

        state_prompts = {
            UnixLocal.unix_local: r'^moler_bash#',
        }
        self._update_dict(self._state_prompts, state_prompts)

    def _prepare_state_hops(self):
        # both state are directly connected, no hops needed
        super(UnixLocal, self)._prepare_state_hops()

    def _get_packages_for_state(self, state, observer):
        if state == UnixLocal.unix_local:
            available = {UnixLocal.cmds: ['moler.cmd.unix'],
                         UnixLocal.events: ['moler.events.unix']}
            return available[observer]
        return []

    def on_connection_made(self, connection):
        self._set_state(UnixLocal.unix_local)

    def on_connection_lost(self, connection):
        self._set_state(UnixLocal.not_connected)
