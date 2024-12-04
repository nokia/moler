# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

from moler.device.textualdevice import TextualDevice
from moler.helpers import copy_dict

__author__ = "Grzegorz Latuszek, Marcin Usielski, Michal Ernst"
__copyright__ = "Copyright (C) 2018-2024, Nokia"
__email__ = (
    "grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com"
)


# TODO: name, logger/logger_name as param
class UnixLocal(TextualDevice):
    r"""
    UnixLocal device class.


    ::


        Example of device in yaml configuration file:
        UNIX_1:
            DEVICE_CLASS: moler.device.unixlocal.UnixLocal

        UNIX_2:
            DEVICE_CLASS: moler.device.unixlocal.UnixLocal
            'CONNECTION_HOPS': {
                        'UNIX_LOCAL': {
                            'UNIX_LOCAL_ROOT': {
                                "command_params": {
                                    "password": "root_password",
                                    "expected_prompt": r'local_root_prompt',
                                }
                            }
                        }
                    }


    """

    unix_local = "UNIX_LOCAL"
    unix_local_root = "UNIX_LOCAL_ROOT"

    def __init__(
        self,
        sm_params=None,
        name=None,
        io_connection=None,
        io_type=None,
        variant=None,
        io_constructor_kwargs=None,
        initial_state=None,
        lazy_cmds_events=False,
    ):
        """
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
        self.pause_prompts_event_on_state_change: bool = False  # Set True to pause the prompt event when _execute_command_to_change_state is being called
        initial_state = initial_state if initial_state is not None else UnixLocal.unix_local

        super(UnixLocal, self).__init__(
            sm_params=sm_params,
            name=name,
            io_connection=io_connection,
            io_type=io_type,
            io_constructor_kwargs=io_constructor_kwargs,
            variant=variant,
            initial_state=initial_state,
            lazy_cmds_events=lazy_cmds_events,
        )

    def _get_default_sm_configuration(self):
        """
        Create State Machine default configuration.
        :return: default sm configuration.
        """
        config = super(UnixLocal, self)._get_default_sm_configuration()
        default_config = {
            UnixLocal.connection_hops: {
                UnixLocal.unix_local: {  # from
                    UnixLocal.unix_local_root: {  # to
                        "execute_command": "su",  # using command
                        "command_params": {  # with parameters
                            "password": "root_password",
                            "expected_prompt": r"local_root_prompt",  # TODO: this should be required or r'^moler_bash$'
                            "target_newline": "\n",
                        },
                        "required_command_params": [],
                    }
                },
                UnixLocal.unix_local_root: {  # from
                    UnixLocal.unix_local: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n",
                            "expected_prompt": r"^moler_bash#",  # r'^moler_bash$'  $ is for user-prompt, # for root-prompt
                        },
                        "required_command_params": [],
                    }
                },
            }
        }
        self._update_dict(config, default_config)
        return config

    def _prepare_transitions(self):
        """
        Prepare transitions to change states.
        :return: None
        """
        super(UnixLocal, self)._prepare_transitions()

        transitions = {
            UnixLocal.unix_local: {
                UnixLocal.not_connected: {
                    "action": ["_close_connection"],
                },
                UnixLocal.unix_local_root: {
                    "action": ["_execute_command_to_change_state"]
                },
            },
            UnixLocal.not_connected: {
                UnixLocal.unix_local: {
                    "action": ["_open_connection"],
                }
            },
            UnixLocal.unix_local_root: {
                UnixLocal.unix_local: {"action": ["_execute_command_to_change_state"]}
            },
        }
        self._add_transitions(transitions=transitions)

    def _prepare_state_prompts(self):
        """
        Prepare textual prompt for each state.
        :return: None
        """
        super(UnixLocal, self)._prepare_state_prompts()

        state_prompts = {
            UnixLocal.unix_local: self._configurations[UnixLocal.connection_hops][
                UnixLocal.unix_local_root
            ][UnixLocal.unix_local]["command_params"]["expected_prompt"],
            UnixLocal.unix_local_root: self._configurations[UnixLocal.connection_hops][
                UnixLocal.unix_local
            ][UnixLocal.unix_local_root]["command_params"]["expected_prompt"],
        }
        self._update_dict(self._state_prompts, state_prompts)

    def _prepare_newline_chars(self):
        """
        Prepare newline char for each state.
        :return: None
        """
        super(UnixLocal, self)._prepare_newline_chars()

        newline_chars = {
            UnixLocal.unix_local: self._configurations[UnixLocal.connection_hops][
                UnixLocal.unix_local_root
            ][UnixLocal.unix_local]["command_params"]["target_newline"],
            UnixLocal.unix_local_root: self._configurations[UnixLocal.connection_hops][
                UnixLocal.unix_local
            ][UnixLocal.unix_local_root]["command_params"]["target_newline"],
        }

        self._update_dict(self._newline_chars, newline_chars)

    def _prepare_state_hops(self):
        """
        Prepare hops for non direct transitions between states.
        :return: None
        """
        state_hops = {
            UnixLocal.not_connected: {
                UnixLocal.unix_local_root: UnixLocal.unix_local,
            },
            UnixLocal.unix_local_root: {
                UnixLocal.not_connected: UnixLocal.unix_local,
            },
        }
        return state_hops

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages contain cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = []
        if state == UnixLocal.unix_local or state == UnixLocal.unix_local_root:
            available = {
                UnixLocal.cmds: ["moler.cmd.unix"],
                UnixLocal.events: ["moler.events.shared", "moler.events.unix"],
            }
            return available[observer]
        return available

    def on_connection_made(self, connection):
        """
        Execute action when connection made.
        :param connection: device connection.
        :return: None
        """
        self._set_state(UnixLocal.unix_local)

    def on_connection_lost(self, connection):
        """
        Execute action when connection lost.
        :param connection: device connection.
        :return: None
        """
        self._set_state(UnixLocal.not_connected)

    def _execute_command_to_change_state(self, source_state, dest_state, timeout=-1):
        """
        Execute action to change state.
        :param source_state: device source state.
        :param dest_state: device destination state.
        :param timeout: transition timeout.
        :return: None
        """
        configurations = self.get_configurations(
            source_state=source_state, dest_state=dest_state
        )

        command_name = configurations["execute_command"]
        command_params = configurations["command_params"]
        command_timeout = self.calc_timeout_for_command(timeout, command_params)
        command_params_without_timeout = self._parameters_without_timeout(
            parameters=command_params
        )
        command = self.get_cmd(
            cmd_name=command_name, cmd_params=command_params_without_timeout
        )
        if self.pause_prompts_event_on_state_change is True and self._prompts_event is not None:
            self._prompts_event.pause()
        try:
            command(timeout=command_timeout)
        finally:
            if self._prompts_event is not None:
                self._prompts_event.resume()

    @classmethod
    def _parameters_without_timeout(cls, parameters):
        """
        Remove timeout from observable parameters.
        :param parameters: observable parameters.
        :return: new parameters without timeout.
        """
        if "timeout" in parameters:
            parameters = copy_dict(src=parameters, deep_copy=True)
            del parameters["timeout"]
        return parameters
