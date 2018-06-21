# -*- coding: utf-8 -*-

__author__ = 'Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com, marcin.usielski@nokia.com'

from moler.device.unix import Unix
from moler.device.device import Device
import time


def test_the_unix_device():
    unix = Unix(io_type='terminal', variant='threaded')

    # Workaround when goto_state is not available
    start_time = time.time()
    while unix.get_state() != Device.connected:
        if time.time() - start_time > 7:  # No infinite loop
            break
        time.sleep(0.1)

    assert(unix.get_state() == Device.connected)
    cmd = unix.get_cmd('ls', options="-l")
    r = cmd()
    assert(r is not None)

    cmd = unix.get_cmd('whoami')
    r = cmd()
    assert(r is not None)
