__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2020-2024, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device
from moler.device import DeviceFactory


adb_remotes = ['ADB_REMOTE',]  # 'ADB_REMOTE3']
adb_remotes_proxy_pc = ['ADB_REMOTE_PROXY_PC',]  # 'ADB_REMOTE_PROXY_PC3']

@pytest.mark.parametrize("device_name", adb_remotes)
def test_adb_remote_device(device_name, device_connection, adb_remote_output):
    adb_remote = get_device(name=device_name, connection=device_connection, device_output=adb_remote_output,
                            test_file_path=__file__)

    iterate_over_device_states(device=adb_remote)


@pytest.mark.parametrize("device_name", adb_remotes_proxy_pc)
def test_adb_remote_device_proxy_pc(device_name, device_connection, adb_remote_output_proxy_pc):
    adb_remote = get_device(name=device_name, connection=device_connection, device_output=adb_remote_output_proxy_pc,
                            test_file_path=__file__)

    iterate_over_device_states(device=adb_remote)

# @pytest.mark.parametrize("devices", [adb_remotes_proxy_pc])
# def test_unix_sm_identity(devices):
#     dev0 = DeviceFactory.get_device(name=devices[0])
#     dev1 = DeviceFactory.get_device(name=devices[1])

#     print(f"tests: {dev0.name},  {dev1.name}")

#     assert dev0._stored_transitions == dev1._stored_transitions
#     assert dev0._state_hops == dev1._state_hops
#     assert dev0._state_prompts == dev1._state_prompts
#     assert dev0._configurations == dev1._configurations
#     assert dev0._newline_chars == dev1._newline_chars


@pytest.fixture
def adb_remote_output():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l remote_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 remote_host': 'remote#',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "UNIX_REMOTE": {
            'exit': 'moler_bash#',
            'su': 'remote_root_prompt',
            'adb -s f57e6b77 shell': 'shell@adbhost:/ $',                    # adb shell is changing prompt so it triggers following 2 send-responses
            '': 'shell@adbhost:/ $',                                         # to allow for self.connection.sendline("")              in _send_prompt_set()
            'export PS1="adb_shell@f57e6b77 \\$ "': 'adb_shell@f57e6b77 $'   # to allow for self.connection.sendline(self.set_prompt) in _send_prompt_set()
        },
        "ADB_SHELL": {
            '': 'adb_shell@f57e6b77 $',
            'exit': 'remote#',
            'su': 'adb_shell@f57e6b77 #',
        },
        "ADB_SHELL_ROOT": {
            'exit': 'adb_shell@f57e6b77 $',
        },
        "UNIX_REMOTE_ROOT": {
            'exit': 'remote#',
        },
    }

    return output


@pytest.fixture
def adb_remote_output_proxy_pc():
    output = {
        "UNIX_LOCAL": {
            'TERM=xterm-mono ssh -l proxy_pc_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 proxy_pc_host': 'proxy_pc#',
            'su': 'local_root_prompt'
        },
        "UNIX_LOCAL_ROOT": {
            'exit': 'moler_bash#'
        },
        "UNIX_REMOTE": {
            'exit': 'proxy_pc#',
            'su': 'remote_root_prompt',
            'adb -s f57e6b77 shell': 'shell@adbhost:/ $',                    # adb shell is changing prompt so it triggers following 2 send-responses
            '': 'shell@adbhost:/ $',                                         # to allow for self.connection.sendline("")              in _send_prompt_set()
            'export PS1="adb_shell@f57e6b77 \\$ "': 'adb_shell@f57e6b77 $'   # to allow for self.connection.sendline(self.set_prompt) in _send_prompt_set()
        },
        "ADB_SHELL": {
            '': 'adb_shell@f57e6b77 $',
            'exit': 'remote#',
            'su': 'adb_shell@f57e6b77 #',
        },
        "ADB_SHELL_ROOT": {
            'exit': 'adb_shell@f57e6b77 $',
        },
        "UNIX_REMOTE_ROOT": {
            'exit': 'remote#',
        },
        "PROXY_PC": {
            'TERM=xterm-mono ssh -l remote_login -o ServerAliveInterval=7 -o ServerAliveCountMax=2 remote_host': 'remote#',
            'exit': 'moler_bash#'
        },
    }

    return output
