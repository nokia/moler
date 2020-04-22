__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import pytest

from moler.util.devices_SM import iterate_over_device_states, get_device


def test_adb_remote_device(device_connection, adb_remote_output):
    adb_remote = get_device(name="ADB_REMOTE", connection=device_connection, device_output=adb_remote_output,
                            test_file_path=__file__)

    iterate_over_device_states(device=adb_remote)


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
