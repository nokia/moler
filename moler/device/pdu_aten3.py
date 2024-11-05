# -*- coding: utf-8 -*-
"""
PduAten device class.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import logging

from moler.device.proxy_pc3 import ProxyPc3
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name


@call_base_class_method_with_same_name
class PduAten3(ProxyPc3):
    r"""
    PDU Aten device class.


    ::


        Example of device in yaml configuration file:
        - with PROXY_PC:
        PDU_1:
            DEVICE_CLASS: moler.device.pdu_aten.PduAten
            CONNECTION_HOPS:
            PROXY_PC:
                PDU:
                execute_command: telnet # default value
                command_params:
                    host: 10.0.0.1
            PDU:
                PROXY_PC:
                execute_command: exit_telnet # default value
                command_params:
                    expected_prompt: proxy_pc.*>
            UNIX_LOCAL:
                PROXY_PC:
                execute_command: ssh # default value
                command_params:
                    expected_prompt: proxy_pc.*>
                    host: 10.0.0.2
                    login: user
                    password: password
        -without PROXY_PC:
            PDU_1:
                DEVICE_CLASS: moler.device.pdu_aten.PduAten
                CONNECTION_HOPS:
                UNIX_LOCAL:
                    PDU:
                    execute_command: telnet # default value
                    command_params:
                        host: 10.0.0.1
    """

    pdu = "PDU"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, io_constructor_kwargs=None,
                 initial_state=None, lazy_cmds_events=False):
        """
        Create PDU device communicating over io_connection.

        :param sm_params: params with machine state description.
        :param name: name of device.
        :param io_connection: External-IO connection having embedded moler-connection.
        :param io_type: External-IO connection type
        :param variant: External-IO connection variant
        :param io_constructor_kwargs: additional parameters for constructor of selected io_type
        :param initial_state: Initial state for device
        :param lazy_cmds_events: set False to load all commands and events when device is initialized, set True to load
                        commands and events when they are required for the first time.
        """
        sm_params = sm_params.copy()
        initial_state = initial_state if initial_state is not None else PduAten3.pdu
        super(PduAten3, self).__init__(sm_params=sm_params, name=name, io_connection=io_connection,
                                       io_type=io_type, variant=variant, io_constructor_kwargs=io_constructor_kwargs,
                                       initial_state=initial_state, lazy_cmds_events=lazy_cmds_events)
        self.logger = logging.getLogger('moler.pdu')

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration with proxy_pc state.
        :return: default sm configuration with proxy_pc state.
        """
        config = {
            PduAten3.connection_hops: {
                PduAten3.proxy_pc: {  # from
                    PduAten3.pdu: {  # to
                        "execute_command": "telnet",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'^>',
                            "set_timeout": None,
                            "target_newline": "\r\n",
                            "login": "teladmin",
                            "password": "telpwd",
                            "encrypt_password": True,
                            "send_enter_after_connection": False,
                            "cmds_before_establish_connection": ['unset binary'],
                        },
                        "required_command_params": [
                            "host",
                        ]
                    },
                },
                PduAten3.pdu: {  # from
                    PduAten3.proxy_pc: {  # to
                        "execute_command": "exit_telnet",  # using command
                        "command_params": {  # with parameters
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                            "expected_prompt"
                        ]
                    },
                },
            }
        }
        return config

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_with_proxy_pc(self):
        transitions = {
            PduAten3.pdu: {
                PduAten3.proxy_pc: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
            PduAten3.proxy_pc: {
                PduAten3.pdu: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
        }
        return transitions

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_with_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine with proxy_pc state.
        :return: textual prompt for each state with proxy_pc state.
        """
        state_prompts = {
            PduAten3.pdu:
                self._configurations[PduAten3.connection_hops][PduAten3.proxy_pc][PduAten3.pdu][
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
            PduAten3.pdu:
                self._configurations[PduAten3.connection_hops][PduAten3.unix_local][PduAten3.pdu][
                    "command_params"]["expected_prompt"],
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine with proxy_pc state.
        :return: non direct transitions for each state with proxy_pc state.
        """
        state_hops = {
            PduAten3.not_connected: {
                PduAten3.pdu: PduAten3.unix_local,
            },
            PduAten3.pdu: {
                PduAten3.not_connected: PduAten3.proxy_pc,
                PduAten3.unix_local: PduAten3.proxy_pc,
                PduAten3.unix_local_root: PduAten3.proxy_pc
            },
            PduAten3.unix_local: {
                PduAten3.pdu: PduAten3.proxy_pc,
            },
            PduAten3.unix_local_root: {
                PduAten3.not_connected: PduAten3.unix_local,
                PduAten3.pdu: PduAten3.unix_local,
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
        available = super(PduAten3, self)._get_packages_for_state(state, observer)

        if not available:
            if state == PduAten3.pdu:
                available = {PduAten3.cmds: ['moler.cmd.pdu_aten.pdu'],
                             PduAten3.events: ['moler.events.unix', 'moler.events.pdu_aten']}
            if available:
                return available[observer]

        return available

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_with_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine with proxy_pc state.
        :return: newline char for each state with proxy_pc state.
        """
        newline_chars = {
            PduAten3.pdu:
                self._configurations[PduAten3.connection_hops][PduAten3.proxy_pc][PduAten3.pdu][
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
            PduAten3.pdu:
                self._configurations[PduAten3.connection_hops][PduAten3.unix_local][PduAten3.pdu][
                    "command_params"]["target_newline"],
        }
        return newline_chars
