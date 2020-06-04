# -*- coding: utf-8 -*-
"""
Moler's device has 2 main responsibilities:
- be the factory that returns commands of that device
- be the state machine that controls which commands may run in given state
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging

from moler.device.textualdevice import TextualDevice
# from moler.device.proxy_pc import ProxyPc  # TODO: allow jumping towards ADB_REMOTE via proxy-pc
from moler.device.unixlocal import UnixLocal
from moler.device.unixremote2 import UnixRemote2, UNIX_REMOTE, UNIX_REMOTE_ROOT
from moler.cmd.adb.adb_shell import AdbShell
from moler.io.raw.sshshell import ThreadedSshShell
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name

# helper variables to improve readability of state machines
# f.ex. moler.device.textualdevice introduces state TextualDevice.not_connected = "NOT_CONNECTED"
NOT_CONNECTED = TextualDevice.not_connected
CONNECTION_HOPS = TextualDevice.connection_hops
UNIX_LOCAL = UnixLocal.unix_local
UNIX_LOCAL_ROOT = UnixLocal.unix_local_root
ADB_SHELL = "ADB_SHELL"
ADB_SHELL_ROOT = "ADB_SHELL_ROOT"


@call_base_class_method_with_same_name
class AdbRemote2(UnixRemote2):
    r"""
    AdbRemote device class.

    Example of device in yaml configuration file:

    -without PROXY_PC and io "terminal":
      ADB_1:
       DEVICE_CLASS: moler.device.adbremote2.AdbRemote2
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
             execute_command: adb_shell # default value
             command_params:
               device_serial_number: 'f57e6b7d'

    -without PROXY_PC and remote-access-io like "sshshell":
      ADB_1:
       DEVICE_CLASS: moler.device.adbremote2.AdbRemote2
       CONNECTION_DESC:
         io_type: sshshell
         host: host_ip
         username: login
         password: password
       CONNECTION_HOPS:
         UNIX_REMOTE:
           ADB_SHELL:
             execute_command: adb_shell # default value
             command_params:
               device_serial_number: 'f57e6b7d'
    """

    def __init__(self, sm_params, name=None, io_connection=None, io_type=None, variant=None, io_constructor_kwargs=None,
                 initial_state=None):
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
        """
        initial_state = initial_state if initial_state is not None else ADB_SHELL
        super(AdbRemote2, self).__init__(name=name, io_connection=io_connection,
                                         io_type=io_type, variant=variant,
                                         io_constructor_kwargs=io_constructor_kwargs,
                                         sm_params=sm_params, initial_state=initial_state)

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_without_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        config = {
            CONNECTION_HOPS: {
                UNIX_REMOTE: {  # from
                    ADB_SHELL: {  # to
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
                ADB_SHELL: {  # from
                    UNIX_REMOTE: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'remote_user_prompt',  # overwritten in _configure_state_machine()
                            "target_newline": "\n",
                            "allowed_newline_after_prompt": True,
                        },
                        "required_command_params": [
                        ]
                    },
                    ADB_SHELL_ROOT: {  # to
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
                ADB_SHELL_ROOT: {  # from
                    ADB_SHELL: {  # to
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

    @mark_to_call_base_class_method_with_same_name
    def _prepare_transitions_without_proxy_pc(self):
        """
        Prepare transitions to change states without proxy_pc state.
        :return: transitions without proxy_pc state.
        """
        transitions = {
            UNIX_REMOTE: {
                ADB_SHELL: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            ADB_SHELL: {
                UNIX_REMOTE: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                ADB_SHELL_ROOT: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            ADB_SHELL_ROOT: {
                ADB_SHELL: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
            },
        }
        return transitions

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_prompts_without_proxy_pc(self):
        """
        Prepare textual prompt for each state for State Machine without proxy_pc state.
        :return: textual prompt for each state without proxy_pc state.
        """
        hops_config = self._configurations[CONNECTION_HOPS]
        cfg_ux2adb = hops_config[UNIX_REMOTE][ADB_SHELL]
        cfg_adb2adbroot = hops_config[ADB_SHELL][ADB_SHELL_ROOT]
        adb_shell_cmd_params = cfg_ux2adb["command_params"]
        adb_shell_prompt = self._get_adb_shell_prompt(adb_shell_cmd_params)
        adb_shell_root_prompt = cfg_adb2adbroot["command_params"]["expected_prompt"]
        if adb_shell_root_prompt is None:
            if adb_shell_prompt.endswith("$"):
                adb_shell_root_prompt = adb_shell_prompt[:-1] + "#"
            else:
                consequence = "Won't be able to detect {} state".format(ADB_SHELL_ROOT)
                fix = "Please provide configuration with 'expected_prompt' for {} state".format(ADB_SHELL_ROOT)
                self._log(logging.WARNING, "Unknown prompt for {} state. {}. {}.".format(ADB_SHELL_ROOT,
                                                                                         consequence, fix))
                adb_shell_root_prompt = "Unknown_adb_root_prompt"

        state_prompts = {
            ADB_SHELL: adb_shell_prompt,
            ADB_SHELL_ROOT: adb_shell_root_prompt,
        }
        return state_prompts

    @property
    def _serial_number(self):
        """
        Retrieve serial_number based on required parameter of state machine.

        :return: serial_number.
        """
        hops_config = self._configurations[CONNECTION_HOPS]
        cfg_ux2adb = hops_config[UNIX_REMOTE][ADB_SHELL]
        serial_number = cfg_ux2adb["command_params"]["serial_number"]
        return serial_number

    def _get_adb_shell_prompt(self, adb_shell_cmd_params):
        adb_shell_prompt = None
        if 'expected_prompt' in adb_shell_cmd_params:
            adb_shell_prompt = adb_shell_cmd_params["expected_prompt"]
        if not adb_shell_prompt:
            # adb_shell@f57e6b77 $
            adb_shell_prompt = AdbShell.re_generated_prompt.format(self._serial_number)
        return adb_shell_prompt

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        hops_config = self._configurations[CONNECTION_HOPS]
        cfg_ux2adb = hops_config[UNIX_REMOTE][ADB_SHELL]
        cfg_adb2adbroot = hops_config[ADB_SHELL][ADB_SHELL_ROOT]
        adb_shell_newline = cfg_ux2adb["command_params"]["target_newline"]
        adb_shell_root_newline = cfg_adb2adbroot["command_params"]["target_newline"]
        if adb_shell_root_newline is None:
            adb_shell_root_newline = adb_shell_newline  # we are on same machine just changing to root

        newline_chars = {
            ADB_SHELL: adb_shell_newline,
            ADB_SHELL_ROOT: adb_shell_root_newline,
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_without_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine without proxy_pc state.
        :return: non direct transitions for each state without proxy_pc state.
        """
        if self._use_local_unix_state:
            state_hops = {
                NOT_CONNECTED: {
                    UNIX_LOCAL_ROOT: UNIX_LOCAL,
                    UNIX_REMOTE: UNIX_LOCAL,
                    UNIX_REMOTE_ROOT: UNIX_LOCAL,
                    ADB_SHELL: UNIX_LOCAL,
                    ADB_SHELL_ROOT: UNIX_LOCAL,
                },
                UNIX_LOCAL: {
                    UNIX_REMOTE_ROOT: UNIX_REMOTE,
                    ADB_SHELL: UNIX_REMOTE,
                    ADB_SHELL_ROOT: UNIX_REMOTE,
                },
                UNIX_LOCAL_ROOT: {
                    NOT_CONNECTED: UNIX_LOCAL,
                    UNIX_REMOTE: UNIX_LOCAL,
                    UNIX_REMOTE_ROOT: UNIX_LOCAL,
                    ADB_SHELL: UNIX_LOCAL,
                    ADB_SHELL_ROOT: UNIX_LOCAL,
                },
                UNIX_REMOTE: {
                    NOT_CONNECTED: UNIX_LOCAL,
                    UNIX_LOCAL_ROOT: UNIX_LOCAL,
                    ADB_SHELL_ROOT: ADB_SHELL,
                },
                UNIX_REMOTE_ROOT: {
                    NOT_CONNECTED: UNIX_REMOTE,
                    UNIX_LOCAL: UNIX_REMOTE,
                    UNIX_LOCAL_ROOT: UNIX_REMOTE,
                    ADB_SHELL: UNIX_REMOTE,
                    ADB_SHELL_ROOT: UNIX_REMOTE,
                },
                ADB_SHELL: {
                    NOT_CONNECTED: UNIX_REMOTE,
                    UNIX_LOCAL: UNIX_REMOTE,
                    UNIX_LOCAL_ROOT: UNIX_REMOTE,
                    UNIX_REMOTE_ROOT: UNIX_REMOTE,
                },
                ADB_SHELL_ROOT: {
                    NOT_CONNECTED: ADB_SHELL,
                    UNIX_LOCAL: ADB_SHELL,
                    UNIX_LOCAL_ROOT: ADB_SHELL,
                    UNIX_REMOTE: ADB_SHELL,
                    UNIX_REMOTE_ROOT: ADB_SHELL,
                },
            }
        else:
            state_hops = {
                NOT_CONNECTED: {
                    UNIX_REMOTE_ROOT: UNIX_REMOTE,
                    ADB_SHELL: UNIX_REMOTE,
                    ADB_SHELL_ROOT: UNIX_REMOTE,
                },
                UNIX_REMOTE: {
                    ADB_SHELL_ROOT: ADB_SHELL,
                },
                UNIX_REMOTE_ROOT: {
                    NOT_CONNECTED: UNIX_REMOTE,
                    ADB_SHELL: UNIX_REMOTE,
                    ADB_SHELL_ROOT: UNIX_REMOTE,
                },
                ADB_SHELL: {
                    NOT_CONNECTED: UNIX_REMOTE,
                    UNIX_REMOTE_ROOT: UNIX_REMOTE,
                },
                ADB_SHELL_ROOT: {
                    NOT_CONNECTED: ADB_SHELL,
                    UNIX_REMOTE: ADB_SHELL,
                    UNIX_REMOTE_ROOT: ADB_SHELL,
                },
            }
        return state_hops

    def _configure_state_machine(self, sm_params):
        """
        Configure device State Machine.
        :param sm_params: dict with parameters of state machine for device.
        :return: Nothing.
        """
        super(AdbRemote2, self)._configure_state_machine(sm_params)
        self._update_depending_on_adbshell_prompt()

    def _update_depending_on_ux_prompt(self):
        self._update_ux_root2ux()
        self._update_adbshell2ux()

    def _update_depending_on_adbshell_prompt(self):
        self._update_adbshellroot2adbshell()

    def _update_adbshell2ux(self):
        hops_cfg = self._configurations[CONNECTION_HOPS]
        if UNIX_REMOTE in self._state_prompts:
            ux_remote_prompt = self._state_prompts[UNIX_REMOTE]
            hops_cfg[ADB_SHELL][UNIX_REMOTE]["command_params"]["expected_prompt"] = ux_remote_prompt

    def _update_adbshellroot2adbshell(self):
        hops_cfg = self._configurations[CONNECTION_HOPS]
        if ADB_SHELL in self._state_prompts:
            adb_shell_prompt = self._state_prompts[ADB_SHELL]
            hops_cfg[ADB_SHELL_ROOT][ADB_SHELL]["command_params"]["expected_prompt"] = adb_shell_prompt

            cfg_adb2adbroot = hops_cfg[ADB_SHELL][ADB_SHELL_ROOT]
            adb_shell_root_prompt = cfg_adb2adbroot["command_params"]["expected_prompt"]
            if adb_shell_root_prompt is None:
                if adb_shell_prompt.endswith("$"):
                    adb_shell_root_prompt = adb_shell_prompt[:-1] + "#"
                    cfg_adb2adbroot["command_params"]["expected_prompt"] = adb_shell_root_prompt

    def _get_packages_for_state(self, state, observer):
        """
        Get available packages containing cmds and events for each state.
        :param state: device state.
        :param observer: observer type, available: cmd, events
        :return: available cmds or events for specific device state.
        """
        available = super(AdbRemote2, self)._get_packages_for_state(state, observer)

        if not available:
            if (state == ADB_SHELL) or (state == ADB_SHELL_ROOT):
                available = {TextualDevice.cmds: ['moler.cmd.unix'],
                             TextualDevice.events: ['moler.events.shared']}
            if available:
                return available[observer]
        elif state == UNIX_REMOTE:  # this is unix extended with adb commands
            if observer == TextualDevice.cmds:
                available.append('moler.cmd.adb')

        return available
