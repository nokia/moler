# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2024, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import logging

from moler.device.unixremote3 import UnixRemote3
from moler.cmd.adb.adb_shell import AdbShell
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name


@call_base_class_method_with_same_name
class AdbRemote3(UnixRemote3):
    r"""
    AdbRemote device class.


    ::


        Example of device in yaml configuration file:
        -without PROXY_PC:
            ADB_1:
            DEVICE_CLASS: moler.device.adbremote3.AdbRemote3
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
                        ADB_SHELL:
                            execute_command: adb_shell # default value; default command is:  adb shell
                            command_params:
                            serial_number: 'f57e6b7d'  #  to create:  adb -s f57e6b7d shell
                            expected_prompt: 'shell@adbhost: $'
                    ADB_SHELL:
                        UNIX_REMOTE:
                            execute_command: exit # default value
    """

    adb_shell = "ADB_SHELL"
    adb_shell_root = "ADB_SHELL_ROOT"

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, io_constructor_kwargs=None,
                 initial_state=None, lazy_cmds_events=False):
        """
        Create ADB device communicating over io_connection
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
        initial_state = initial_state if initial_state is not None else AdbRemote3.adb_shell
        super(AdbRemote3, self).__init__(name=name, io_connection=io_connection,
                                         io_type=io_type, variant=variant,
                                         io_constructor_kwargs=io_constructor_kwargs,
                                         sm_params=sm_params, initial_state=initial_state,
                                         lazy_cmds_events=lazy_cmds_events)

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_with_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        config = {
            AdbRemote3.connection_hops: {
                AdbRemote3.unix_remote: {  # from
                    AdbRemote3.adb_shell: {  # to
                        "execute_command": "adb_shell",
                        "command_params": {  # with parameters
                            "target_newline": "\n",
                            "prompt_from_serial_number": True,
                        },
                        "required_command_params": [
                            "serial_number",
                        ]
                    },
                },
                AdbRemote3.adb_shell: {  # from
                    AdbRemote3.unix_remote: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'remote_user_prompt',  # overwritten in _configure_state_machine()
                            "target_newline": "\n",
                            "allowed_newline_after_prompt": True,
                        },
                        "required_command_params": [
                        ]
                    },
                    AdbRemote3.adb_shell_root: {  # to
                        "execute_command": "su",  # using command
                        "command_params": {  # with parameters
                            "password": "provide_root_password_in_cfg",  # if su requires passwd and not given in cfg
                            "expected_prompt": None,  # overwritten in _prepare_state_prompts...()
                            "target_newline": None,  # overwritten in _prepare_newline_chars_...()
                        },
                        "required_command_params": [
                        ]
                    },
                },
                AdbRemote3.adb_shell_root: {  # from
                    AdbRemote3.adb_shell: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'adb_prompt',  # overwritten in _configure_state_machine()
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                        ]
                    },
                },
            }
        }
        return config

    def _overwrite_prompts(self):
        """
        Overwrite prompts for some states to easily configure the SM.
        """
        super(AdbRemote3, self)._overwrite_prompts()
        hops_config = self._configurations[AdbRemote3.connection_hops]
        cfg_ux2adb = hops_config[AdbRemote3.unix_remote][AdbRemote3.adb_shell]
        cfg_adb2adbroot = hops_config[AdbRemote3.adb_shell][AdbRemote3.adb_shell_root]
        adb_shell_cmd_params = cfg_ux2adb["command_params"]
        adb_shell_prompt = self._get_adb_shell_prompt(adb_shell_cmd_params)
        adb_shell_root_prompt = cfg_adb2adbroot["command_params"]["expected_prompt"]
        if adb_shell_root_prompt is None:
            if adb_shell_prompt.endswith("$"):
                adb_shell_root_prompt = f"{adb_shell_prompt[:-1]}#"
            else:
                consequence = f"Won't be able to detect {AdbRemote3.adb_shell_root} state"
                fix = f"Please provide configuration with 'expected_prompt' for {AdbRemote3.adb_shell_root} state"
                self._log(logging.WARNING, f"Unknown prompt for {AdbRemote3.adb_shell_root} state. {consequence}. {fix}.")
                adb_shell_root_prompt = "Unknown_adb_root_prompt"

        if self._use_proxy_pc:
            cfg_uxloc2ux = hops_config[AdbRemote3.proxy_pc][AdbRemote3.unix_remote]
        else:
            cfg_uxloc2ux = hops_config[AdbRemote3.unix_local][AdbRemote3.unix_remote]
        cfg_adb2ux = hops_config[AdbRemote3.adb_shell][AdbRemote3.unix_remote]
        remote_ux_prompt = cfg_uxloc2ux["command_params"]["expected_prompt"]
        cfg_adb2ux["command_params"]["expected_prompt"] = remote_ux_prompt

        # copy prompt for ADB_SHELL_ROOT/exit from UNIX_REMOTE/adb shell
        cfg_adbroot2adb = hops_config[AdbRemote3.adb_shell_root][AdbRemote3.adb_shell]
        cfg_adbroot2adb["command_params"]["expected_prompt"] = adb_shell_prompt
        cfg_adb2adbroot["command_params"]["expected_prompt"] = adb_shell_root_prompt

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_without_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        hops_config = self._configurations[AdbRemote3.connection_hops]
        cfg_ux2adb = hops_config[AdbRemote3.unix_remote][AdbRemote3.adb_shell]
        cfg_adb2adbroot = hops_config[AdbRemote3.adb_shell][AdbRemote3.adb_shell_root]
        adb_shell_cmd_params = cfg_ux2adb["command_params"]
        adb_shell_prompt = self._get_adb_shell_prompt(adb_shell_cmd_params)
        adb_shell_root_prompt = cfg_adb2adbroot["command_params"]["expected_prompt"]
        if adb_shell_root_prompt is None:
            if adb_shell_prompt.endswith("$"):
                adb_shell_root_prompt = f"{adb_shell_prompt[:-1]}#"
            else:
                consequence = f"Won't be able to detect {AdbRemote3.adb_shell_root} state"
                fix = f"Please provide configuration with 'expected_prompt' for {AdbRemote3.adb_shell_root} state"
                self._log(logging.WARNING, f"Unknown prompt for {AdbRemote3.adb_shell_root} state. {consequence}. {fix}.")
                adb_shell_root_prompt = "Unknown_adb_root_prompt"

        state_prompts = {
            AdbRemote3.adb_shell: adb_shell_prompt,
            AdbRemote3.adb_shell_root: adb_shell_root_prompt,
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_with_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        hops_config = self._configurations[AdbRemote3.connection_hops]
        cfg_ux2adb = hops_config[AdbRemote3.unix_remote][AdbRemote3.adb_shell]
        cfg_adb2adbroot = hops_config[AdbRemote3.adb_shell][AdbRemote3.adb_shell_root]
        adb_shell_cmd_params = cfg_ux2adb["command_params"]
        adb_shell_prompt = self._get_adb_shell_prompt(adb_shell_cmd_params)
        adb_shell_root_prompt = cfg_adb2adbroot["command_params"]["expected_prompt"]
        if adb_shell_root_prompt is None:
            if adb_shell_prompt.endswith("$"):
                adb_shell_root_prompt = f"{adb_shell_prompt[:-1]}#"
            else:
                consequence = f"Won't be able to detect {AdbRemote3.adb_shell_root} state"
                fix = f"Please provide configuration with 'expected_prompt' for {AdbRemote3.adb_shell_root} state"
                self._log(logging.WARNING, f"Unknown prompt for {AdbRemote3.adb_shell_root} state. {consequence}. {fix}.")
                adb_shell_root_prompt = "Unknown_adb_root_prompt"

        state_prompts = {
            AdbRemote3.adb_shell: adb_shell_prompt,
            AdbRemote3.adb_shell_root: adb_shell_root_prompt,
        }
        return state_prompts

    @property
    def _serial_number(self):
        """
        Retrieve serial_number based on required parameter of state machine.

        :return: serial_number.
        """
        hops_config = self._configurations[AdbRemote3.connection_hops]
        cfg_ux2adb = hops_config[AdbRemote3.unix_remote][AdbRemote3.adb_shell]
        serial_number = cfg_ux2adb["command_params"]["serial_number"]
        return serial_number

    def _get_adb_shell_prompt(self, adb_shell_cmd_params):
        adb_shell_prompt = None
        if 'expected_prompt' in adb_shell_cmd_params:
            adb_shell_prompt = adb_shell_cmd_params["expected_prompt"]
        if not adb_shell_prompt:
            # adb_shell@f57e6b77 $
            adb_shell_prompt = AdbShell.re_generated_prompt.format(self._serial_number)  # pylint-disable-line: consider-using-f-string
        return adb_shell_prompt

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        hops_config = self._configurations[AdbRemote3.connection_hops]
        cfg_ux2adb = hops_config[AdbRemote3.unix_remote][AdbRemote3.adb_shell]
        cfg_adb2adbroot = hops_config[AdbRemote3.adb_shell][AdbRemote3.adb_shell_root]
        adb_shell_newline = cfg_ux2adb["command_params"]["target_newline"]
        adb_shell_root_newline = cfg_adb2adbroot["command_params"]["target_newline"]
        if adb_shell_root_newline is None:
            adb_shell_root_newline = adb_shell_newline  # we are on same machine just changing to root

        newline_chars = {
            AdbRemote3.adb_shell: adb_shell_newline,
            AdbRemote3.adb_shell_root: adb_shell_root_newline,
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_with_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        hops_config = self._configurations[AdbRemote3.connection_hops]
        cfg_ux2adb = hops_config[AdbRemote3.unix_remote][AdbRemote3.adb_shell]
        cfg_adb2adbroot = hops_config[AdbRemote3.adb_shell][AdbRemote3.adb_shell_root]
        adb_shell_newline = cfg_ux2adb["command_params"]["target_newline"]
        adb_shell_root_newline = cfg_adb2adbroot["command_params"]["target_newline"]
        if adb_shell_root_newline is None:
            adb_shell_root_newline = adb_shell_newline  # we are on same machine just changing to root

        newline_chars = {
            AdbRemote3.adb_shell: adb_shell_newline,
            AdbRemote3.adb_shell_root: adb_shell_root_newline,
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_with_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine without proxy_pc state.
        :return: non direct transitions for each state without proxy_pc state.
        """
        state_hops = {
            AdbRemote3.not_connected: {
                AdbRemote3.unix_local_root: AdbRemote3.unix_local,
                AdbRemote3.proxy_pc: AdbRemote3.unix_local,
                AdbRemote3.unix_remote: AdbRemote3.unix_local,
                AdbRemote3.unix_remote_root: AdbRemote3.unix_local,
                AdbRemote3.adb_shell: AdbRemote3.unix_local,
                AdbRemote3.adb_shell_root: AdbRemote3.unix_local,
            },
            AdbRemote3.unix_local: {
                AdbRemote3.unix_remote_root: AdbRemote3.proxy_pc,
                AdbRemote3.adb_shell: AdbRemote3.proxy_pc,
                AdbRemote3.adb_shell_root: AdbRemote3.proxy_pc,
            },
            AdbRemote3.unix_local_root: {
                AdbRemote3.not_connected: AdbRemote3.unix_local,
                AdbRemote3.proxy_pc: AdbRemote3.unix_local,
                AdbRemote3.unix_remote: AdbRemote3.unix_local,
                AdbRemote3.unix_remote_root: AdbRemote3.unix_local,
                AdbRemote3.adb_shell: AdbRemote3.unix_local,
                AdbRemote3.adb_shell_root: AdbRemote3.unix_local,
            },
            AdbRemote3.unix_remote: {
                AdbRemote3.unix_local: AdbRemote3.proxy_pc,
                AdbRemote3.unix_local_root: AdbRemote3.proxy_pc,
                AdbRemote3.adb_shell_root: AdbRemote3.adb_shell,
            },
            AdbRemote3.unix_remote_root: {
                AdbRemote3.not_connected: AdbRemote3.unix_remote,
                AdbRemote3.proxy_pc: AdbRemote3.unix_remote,
                AdbRemote3.unix_local: AdbRemote3.unix_remote,
                AdbRemote3.unix_local_root: AdbRemote3.unix_remote,
                AdbRemote3.adb_shell: AdbRemote3.unix_remote,
                AdbRemote3.adb_shell_root: AdbRemote3.unix_remote,
            },
            AdbRemote3.adb_shell: {
                AdbRemote3.not_connected: AdbRemote3.unix_remote,
                AdbRemote3.proxy_pc: AdbRemote3.unix_remote,
                AdbRemote3.unix_local: AdbRemote3.unix_remote,
                AdbRemote3.unix_local_root: AdbRemote3.unix_remote,
                AdbRemote3.unix_remote_root: AdbRemote3.unix_remote,
            },
            AdbRemote3.adb_shell_root: {
                AdbRemote3.not_connected: AdbRemote3.adb_shell,
                AdbRemote3.proxy_pc: AdbRemote3.adb_shell,
                AdbRemote3.unix_local: AdbRemote3.adb_shell,
                AdbRemote3.unix_local_root: AdbRemote3.adb_shell,
                AdbRemote3.unix_remote: AdbRemote3.adb_shell,
                AdbRemote3.unix_remote_root: AdbRemote3.adb_shell,
            },
            AdbRemote3.proxy_pc: {
                AdbRemote3.adb_shell: AdbRemote3.unix_remote,
                AdbRemote3.adb_shell_root: AdbRemote3.unix_remote,
            }
        }
        return state_hops

    def _configure_state_machine(self, sm_params):
        """
        Configure device State Machine.
        :param sm_params: dict with parameters of state machine for device.
        :return: None
        """
        super(AdbRemote3, self)._configure_state_machine(sm_params)

        hops_config = self._configurations[AdbRemote3.connection_hops]

        # copy prompt for ADB_SHELL/exit from UNIX_LOCAL/ssh
        if self._use_proxy_pc:
            cfg_uxloc2ux = hops_config[AdbRemote3.proxy_pc][AdbRemote3.unix_remote]
        else:
            cfg_uxloc2ux = hops_config[AdbRemote3.unix_local][AdbRemote3.unix_remote]
        cfg_adb2ux = hops_config[AdbRemote3.adb_shell][AdbRemote3.unix_remote]
        remote_ux_prompt = cfg_uxloc2ux["command_params"]["expected_prompt"]
        cfg_adb2ux["command_params"]["expected_prompt"] = remote_ux_prompt

        # copy prompt for ADB_SHELL_ROOT/exit from UNIX_REMOTE/adb shell
        cfg_ux2adb = hops_config[AdbRemote3.unix_remote][AdbRemote3.adb_shell]
        cfg_adbroot2adb = hops_config[AdbRemote3.adb_shell_root][AdbRemote3.adb_shell]
        adb_shell_prompt = self._get_adb_shell_prompt(cfg_ux2adb["command_params"])
        cfg_adbroot2adb["command_params"]["expected_prompt"] = adb_shell_prompt

        cfg_adb2adbroot = hops_config[AdbRemote3.adb_shell][AdbRemote3.adb_shell_root]
        adb_shell_root_prompt = cfg_adb2adbroot["command_params"]["expected_prompt"]
        if adb_shell_root_prompt is None:
            if adb_shell_prompt.endswith("$"):
                adb_shell_root_prompt = f"{adb_shell_prompt[:-1]}#"
                cfg_adb2adbroot["command_params"]["expected_prompt"] = adb_shell_root_prompt

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages containing cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = super(AdbRemote3, self)._get_packages_for_state(state, observer)

        if not available:
            if (state == AdbRemote3.adb_shell) or (state == AdbRemote3.adb_shell_root):
                available = {AdbRemote3.cmds: ['moler.cmd.unix'],
                             AdbRemote3.events: ['moler.events.shared']}
            if available:
                return available[observer]
        elif state == AdbRemote3.unix_remote:  # this is unix extended with adb commands
            if observer == AdbRemote3.cmds:
                available.append('moler.cmd.adb')

        return available

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_with_proxy_pc(self):
        """
        Prepare transitions to change states without proxy_pc state.
        :return: transitions without proxy_pc state.
        """
        transitions = {
            AdbRemote3.unix_remote: {
                AdbRemote3.adb_shell: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            AdbRemote3.adb_shell: {
                AdbRemote3.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                AdbRemote3.adb_shell_root: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            AdbRemote3.adb_shell_root: {
                AdbRemote3.adb_shell: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
        }
        return transitions
