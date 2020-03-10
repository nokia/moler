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
from moler.device.unixremote import UnixRemote
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name


@call_base_class_method_with_same_name
class AdbRemote(UnixRemote):
    r"""
    AdbRemote device class.

    Example of device in yaml configuration file:
    -without PROXY_PC:
      ADB_1:
       DEVICE_CLASS: moler.device.adbremote.AdbRemote
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
            device_serial_number: 'f57e6b7d'  #  to create:  adb -s f57e6b7d shell
            expected_prompt: 'shell@adbhost: $'
      ADB_SHELL:
        UNIX_REMOTE:
          execute_command: exit # default value
    """

    adb_shell = "ADB_SHELL"
    adb_shell_root = "ADB_SHELL_ROOT"

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
        initial_state = initial_state if initial_state is not None else AdbRemote.adb_shell
        super(AdbRemote, self).__init__(name=name, io_connection=io_connection,
                                        io_type=io_type, variant=variant,
                                        io_constructor_kwargs=io_constructor_kwargs,
                                        sm_params=sm_params, initial_state=initial_state)

    @mark_to_call_base_class_method_with_same_name
    def _get_default_sm_configuration_without_proxy_pc(self):
        """
        Return State Machine default configuration without proxy_pc state.
        :return: default sm configuration without proxy_pc state.
        """
        config = {  # TODO: shell we use direct-string names of config dicts? change simplicity vs readability
            TextualDevice.connection_hops: {
                UnixRemote.unix_remote: {  # from
                    AdbRemote.adb_shell: {  # to
                        "execute_command": "adb_shell",
                        "command_params": {  # with parameters
                            "target_newline": "\n"
                        },
                        "required_command_params": [
                            "expected_prompt"  # TODO: if not required then we depend on default-unix-prompt regexp
                        ]
                    },
                },
                AdbRemote.adb_shell: {  # from
                    UnixRemote.unix_remote: {  # to
                        "execute_command": "exit",  # using command
                        "command_params": {  # with parameters
                            "expected_prompt": r'remote_user_prompt',  # overwritten in _configure_state_machine()
                            "target_newline": "\n",
                            "allowed_newline_after_prompt": True,
                        },
                        "required_command_params": [
                        ]
                    },
                    AdbRemote.adb_shell_root: {  # to
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
                AdbRemote.adb_shell_root: {  # from
                    AdbRemote.adb_shell: {  # to
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
            UnixRemote.unix_remote: {
                AdbRemote.adb_shell: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            AdbRemote.adb_shell: {
                UnixRemote.unix_remote: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                },
                AdbRemote.adb_shell_root: {
                    "action": [
                        "_execute_command_to_change_state"
                    ],
                }
            },
            AdbRemote.adb_shell_root: {
                AdbRemote.adb_shell: {
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
        hops_config = self._configurations[TextualDevice.connection_hops]
        cfg_ux2adb = hops_config[UnixRemote.unix_remote][AdbRemote.adb_shell]
        cfg_adb2adbroot = hops_config[AdbRemote.adb_shell][AdbRemote.adb_shell_root]
        adb_shell_prompt = cfg_ux2adb["command_params"]["expected_prompt"]
        adb_shell_root_prompt = cfg_adb2adbroot["command_params"]["expected_prompt"]
        if adb_shell_root_prompt is None:
            if adb_shell_prompt.endswith("$"):
                adb_shell_root_prompt = adb_shell_prompt[:-1] + "#"
            else:
                consequence = "Won't be able to detect {} state".format(AdbRemote.adb_shell_root)
                fix = "Please provide configuration with 'expected_prompt' for {} state".format(AdbRemote.adb_shell_root)
                self._log(logging.WARNING, "Unknown prompt for {} state. {}. {}.".format(AdbRemote.adb_shell_root,
                                                                                         consequence, fix))
                adb_shell_root_prompt = "Unknown_adb_root_prompt"

        state_prompts = {
            AdbRemote.adb_shell: adb_shell_prompt,
            AdbRemote.adb_shell_root: adb_shell_root_prompt,
        }
        return state_prompts

    @mark_to_call_base_class_method_with_same_name
    def _prepare_newline_chars_without_proxy_pc(self):
        """
        Prepare newline char for each state for State Machine without proxy_pc state.
        :return: newline char for each state without proxy_pc state.
        """
        hops_config = self._configurations[TextualDevice.connection_hops]
        cfg_ux2adb = hops_config[UnixRemote.unix_remote][AdbRemote.adb_shell]
        cfg_adb2adbroot = hops_config[AdbRemote.adb_shell][AdbRemote.adb_shell_root]
        adb_shell_newline = cfg_ux2adb["command_params"]["target_newline"]
        adb_shell_root_newline = cfg_adb2adbroot["command_params"]["target_newline"]
        if adb_shell_root_newline is None:
            adb_shell_root_newline = adb_shell_newline  # we are on same machine just changing to root

        newline_chars = {
            AdbRemote.adb_shell: adb_shell_newline,
            AdbRemote.adb_shell_root: adb_shell_root_newline,
        }
        return newline_chars

    @mark_to_call_base_class_method_with_same_name
    def _prepare_state_hops_without_proxy_pc(self):
        """
        Prepare non direct transitions for each state for State Machine without proxy_pc state.
        :return: non direct transitions for each state without proxy_pc state.
        """
        state_hops = {
            TextualDevice.not_connected: {
                UnixLocal.unix_local_root: UnixLocal.unix_local,
                UnixRemote.unix_remote: UnixLocal.unix_local,
                UnixRemote.unix_remote_root: UnixLocal.unix_local,
                AdbRemote.adb_shell: UnixLocal.unix_local,
                AdbRemote.adb_shell_root: UnixLocal.unix_local,
            },
            UnixLocal.unix_local: {
                UnixRemote.unix_remote_root: UnixRemote.unix_remote,
                AdbRemote.adb_shell: UnixRemote.unix_remote,
                AdbRemote.adb_shell_root: UnixRemote.unix_remote,
            },
            UnixLocal.unix_local_root: {
                TextualDevice.not_connected: UnixLocal.unix_local,
                UnixRemote.unix_remote: UnixLocal.unix_local,
                UnixRemote.unix_remote_root: UnixLocal.unix_local,
                AdbRemote.adb_shell: UnixLocal.unix_local,
                AdbRemote.adb_shell_root: UnixLocal.unix_local,
            },
            UnixRemote.unix_remote: {
                TextualDevice.not_connected: UnixLocal.unix_local,
                UnixLocal.unix_local_root: UnixLocal.unix_local,
                AdbRemote.adb_shell_root: AdbRemote.adb_shell,
            },
            UnixRemote.unix_remote_root: {
                TextualDevice.not_connected: UnixRemote.unix_remote,
                UnixLocal.unix_local: UnixRemote.unix_remote,
                UnixLocal.unix_local_root: UnixRemote.unix_remote,
                AdbRemote.adb_shell: UnixRemote.unix_remote,
                AdbRemote.adb_shell_root: UnixRemote.unix_remote,
            },
            AdbRemote.adb_shell: {
                TextualDevice.not_connected: UnixRemote.unix_remote,
                UnixLocal.unix_local: UnixRemote.unix_remote,
                UnixLocal.unix_local_root: UnixRemote.unix_remote,
                UnixRemote.unix_remote_root: UnixRemote.unix_remote,
            },
            AdbRemote.adb_shell_root: {
                TextualDevice.not_connected: AdbRemote.adb_shell,
                UnixLocal.unix_local: AdbRemote.adb_shell,
                UnixLocal.unix_local_root: AdbRemote.adb_shell,
                UnixRemote.unix_remote: AdbRemote.adb_shell,
                UnixRemote.unix_remote_root: AdbRemote.adb_shell,
            },
        }
        return state_hops

    def _configure_state_machine(self, sm_params):
        """
        Configure device State Machine.
        :param sm_params: dict with parameters of state machine for device.
        :return: Nothing.
        """
        super(AdbRemote, self)._configure_state_machine(sm_params)

        hops_config = self._configurations[TextualDevice.connection_hops]

        # copy prompt for ADB_SHELL/exit from UNIX_LOCAL/ssh
        cfg_uxloc2ux = hops_config[UnixLocal.unix_local][UnixRemote.unix_remote]
        cfg_adb2ux = hops_config[AdbRemote.adb_shell][UnixRemote.unix_remote]
        remote_ux_prompt = cfg_uxloc2ux["command_params"]["expected_prompt"]
        cfg_adb2ux["command_params"]["expected_prompt"] = remote_ux_prompt

        # copy prompt for ADB_SHELL_ROOT/exit from UNIX_REMOTE/adb shell
        cfg_ux2adb = hops_config[UnixRemote.unix_remote][AdbRemote.adb_shell]
        cfg_adbroot2adb = hops_config[AdbRemote.adb_shell_root][AdbRemote.adb_shell]
        adb_shell_prompt = cfg_ux2adb["command_params"]["expected_prompt"]
        cfg_adbroot2adb["command_params"]["expected_prompt"] = adb_shell_prompt

        cfg_adb2adbroot = hops_config[AdbRemote.adb_shell][AdbRemote.adb_shell_root]
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
        available = super(AdbRemote, self)._get_packages_for_state(state, observer)

        if not available:
            if (state == AdbRemote.adb_shell) or (state == AdbRemote.adb_shell_root):
                available = {TextualDevice.cmds: ['moler.cmd.unix'],
                             TextualDevice.events: ['moler.events.shared']}
            if available:
                return available[observer]
        elif state == UnixRemote.unix_remote:  # this is unix extended with adb commands
            if observer == TextualDevice.cmds:
                available.append('moler.cmd.adb')

        return available
