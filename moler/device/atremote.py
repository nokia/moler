# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2025, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

from moler.device.unixremote import UnixRemote
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name
from moler.cmd.at.genericat import GenericAtCommand


@call_base_class_method_with_same_name
class AtRemote(UnixRemote):
    r"""
    AtRemote device class.


    ::


        Example of device in yaml configuration file:
        -without PROXY_PC:
        AT_1:
        DEVICE_CLASS: moler.device.atremote.AtRemote
        CONNECTION_HOPS:
            UNIX_LOCAL:
                UNIX_REMOTE:
                    execute_command: ssh # default value
                    command_params:
                    expected_prompt: unix_remote_prompt
                    host: host_ip
                    login: login
                    password: password
            UNIX_REMOTE:
                AT_REMOTE:
                execute_command: plink_serial # default value
                command_params:
                    serial_devname: 'COM5'
            AT_REMOTE:
                UNIX_REMOTE:
                execute_command: ctrl_c # default value
    """

    at_remote = "AT_REMOTE"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, io_constructor_kwargs=None,
                 initial_state=None, lazy_cmds_events=False):
        """
        Create AT device communicating over io_connection
        :param sm_params: dict with parameters of state machine for device
        :param name: name of device
        :param io_connection: External-IO connection having embedded moler-connection
        :param io_type: type of connection - tcp, udp, ssh, telnet, ..
        :param variant: connection implementation variant, ex. 'threaded', 'twisted', 'asyncio', ..
                        (if not given then default one is taken)
        :param io_constructor_kwargs: additional parameter into constructor of selected connection type
                        (if not given then default one is taken)
        :param initial_state: name of initial state. State machine tries to enter this state just after creation.
        :param lazy_cmds_events: set False to load all commands and events when device is initialized, set True to load
                        commands and events when they are required for the first time.
        """
        initial_state = initial_state if initial_state is not None else AtRemote.at_remote
        super(AtRemote, self).__init__(name=name, io_connection=io_connection,
                                       io_type=io_type, variant=variant,
                                       io_constructor_kwargs=io_constructor_kwargs,
                                       sm_params=sm_params, initial_state=initial_state,
                                       lazy_cmds_events=lazy_cmds_events)

    def _overwrite_prompts(self):
        super()._overwrite_prompts()
        # copy prompt for AT_REMOTE/ctrl_c from UNIX_REMOTE_ROOT/exit
        hops_config = self._configurations[AtRemote.connection_hops]
        remote_ux_root_exit_params = hops_config[AtRemote.unix_remote_root][AtRemote.unix_remote]["command_params"]
        remote_ux_prompt = remote_ux_root_exit_params["expected_prompt"]
        hops_config[AtRemote.at_remote][AtRemote.unix_remote]["command_params"]["expected_prompt"] = remote_ux_prompt

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        config = {
            AtRemote.connection_hops: {
                AtRemote.unix_remote: {  # from
                    AtRemote.at_remote: {  # to
                        "execute_command": "plink_serial",
                        "command_params": {  # with parameters
                            "target_newline": "\r\n"
                        },
                        "required_command_params": [
                            "serial_devname"
                        ]
                    },
                },
                AtRemote.at_remote: {  # from
                    AtRemote.unix_remote: {  # to
                        "execute_command": "ctrl_c",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": 'remote_prompt',  # overwritten in _configure_state_machine
                        },
                        "required_command_params": [
                        ]
                    },
                },
            }
        }
        return config

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_with_proxy_pc(self):
        """
        Prepare transitions to change states without proxy_pc state.
        :return: transitions without proxy_pc state.
        """
        transitions = {
            AtRemote.unix_remote: {
                AtRemote.at_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            AtRemote.at_remote: {
                AtRemote.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
        }
        return transitions

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_without_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        hops_config = self._configurations[AtRemote.connection_hops]
        serial_devname = hops_config[AtRemote.unix_remote][AtRemote.at_remote]["command_params"]["serial_devname"]
        proxy_prompt = f"{serial_devname}> port READY"
        at_cmds_prompt = GenericAtCommand._re_default_at_prompt.pattern  # pylint: disable=protected-access
        state_prompts = {
            AtRemote.at_remote: f"{proxy_prompt}|{at_cmds_prompt}"
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_with_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        hops_config = self._configurations[AtRemote.connection_hops]
        serial_devname = hops_config[AtRemote.unix_remote][AtRemote.at_remote]["command_params"]["serial_devname"]
        proxy_prompt = f"{serial_devname}> port READY"
        at_cmds_prompt = GenericAtCommand._re_default_at_prompt.pattern  # pylint: disable=protected-access
        state_prompts = {
            AtRemote.at_remote: f"{proxy_prompt}|{at_cmds_prompt}"
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        hops_config = self._configurations[AtRemote.connection_hops]
        hops_2_at_remote_config = hops_config[AtRemote.unix_remote][AtRemote.at_remote]
        newline_chars = {
            AtRemote.at_remote: hops_2_at_remote_config["command_params"]["target_newline"],
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_with_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        hops_config = self._configurations[AtRemote.connection_hops]
        hops_2_at_remote_config = hops_config[AtRemote.unix_remote][AtRemote.at_remote]
        newline_chars = {
            AtRemote.at_remote: hops_2_at_remote_config["command_params"]["target_newline"],
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine without proxy_pc state.
        :return: non direct transitions for each state without proxy_pc state.
        """
        state_hops = {
            AtRemote.not_connected: {
                AtRemote.unix_local_root: AtRemote.unix_local,
                AtRemote.proxy_pc: AtRemote.unix_local,
                AtRemote.unix_remote: AtRemote.unix_local,
                AtRemote.unix_remote_root: AtRemote.unix_local,
                AtRemote.at_remote: AtRemote.unix_local,
            },
            AtRemote.unix_local: {
                AtRemote.unix_remote_root: AtRemote.proxy_pc,
                AtRemote.at_remote: AtRemote.proxy_pc,
            },
            AtRemote.unix_local_root: {
                AtRemote.not_connected: AtRemote.unix_local,
                AtRemote.proxy_pc: AtRemote.unix_local,
                AtRemote.unix_remote: AtRemote.unix_local,
                AtRemote.unix_remote_root: AtRemote.unix_local,
                AtRemote.at_remote: AtRemote.unix_local,
            },
            AtRemote.unix_remote: {
                AtRemote.unix_local: AtRemote.proxy_pc,
                AtRemote.not_connected: AtRemote.proxy_pc,
                AtRemote.unix_local_root: AtRemote.proxy_pc,
            },
            AtRemote.unix_remote_root: {
                AtRemote.not_connected: AtRemote.unix_remote,
                AtRemote.proxy_pc: AtRemote.unix_remote,
                AtRemote.unix_local: AtRemote.unix_remote,
                AtRemote.unix_local_root: AtRemote.unix_remote,
                AtRemote.at_remote: AtRemote.unix_remote,
            },
            AtRemote.at_remote: {
                AtRemote.not_connected: AtRemote.unix_remote,
                AtRemote.proxy_pc: AtRemote.unix_remote,
                AtRemote.unix_local: AtRemote.unix_remote,
                AtRemote.unix_local_root: AtRemote.unix_remote,
                AtRemote.unix_remote_root: AtRemote.unix_remote,
            },
            AtRemote.proxy_pc: {
                AtRemote.unix_remote_root: AtRemote.unix_remote,
                AtRemote.at_remote: AtRemote.unix_remote,
                AtRemote.not_connected: AtRemote.unix_local,
                AtRemote.unix_local_root: AtRemote.unix_local,
            }
        }
        return state_hops

    def _configure_state_machine(self, sm_params):
        """
        Configure device State Machine.
        :param sm_params: dict with parameters of state machine for device.
        :return: None
        """
        super(AtRemote, self)._configure_state_machine(sm_params)

        # copy prompt for AT_REMOTE/ctrl_c from UNIX_REMOTE_ROOT/exit
        hops_config = self._configurations[AtRemote.connection_hops]
        remote_ux_root_exit_params = hops_config[AtRemote.unix_remote_root][AtRemote.unix_remote]["command_params"]
        remote_ux_prompt = remote_ux_root_exit_params["expected_prompt"]
        hops_config[AtRemote.at_remote][AtRemote.unix_remote]["command_params"]["expected_prompt"] = remote_ux_prompt

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages containing cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = super(AtRemote, self)._get_packages_for_state(state, observer)

        if not available:
            if state == AtRemote.at_remote:
                available = {AtRemote.cmds: ['moler.cmd.at', 'moler.cmd.unix.ctrl_c'],
                             AtRemote.events: ['moler.events.shared']}
            if available:
                return available[observer]
        elif state == AtRemote.unix_remote:  # this is unix extended with plink_serial command
            if observer == AtRemote.cmds:
                available.append('moler.cmd.at.plink_serial')
                available.append('moler.cmd.at.cu')

        return available
