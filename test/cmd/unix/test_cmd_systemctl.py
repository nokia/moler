# -*- coding: utf-8 -*-
"""
Testing of systemctl command.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 22019, Nokia'
__email__ = 'michal.ernst@nokia.com'

import time
import pytest
from moler.cmd.unix.systemctl import Systemctl
import datetime


def test_systemctl_sending_space_and_q(buffer_connection):
    output1 = """systemctl
  UNIT                                                                                      LOAD   ACTIVE     SUB          DESCRIPTION
  basic.target                                                                              loaded active     active       Basic System
  cryptsetup.target                                                                         loaded active     active       Encrypted Volumes
  getty.target                                                                              loaded active     active       Login Prompts
lines 1-70"""
    output2 = """  anacron.timer                                                                             loaded active     waiting      Trigger anacron every hour
  apt-daily-upgrade.timer                                                                   loaded active     waiting      Daily apt upgrade and clean activities
  apt-daily.timer                                                                           loaded active     waiting      Daily apt download activities
  systemd-tmpfiles-clean.timer                                                              loaded active     waiting      Daily Cleanup of Temporary Directories
LOAD   = Reflects whether the unit definition was properly loaded.
ACTIVE = The high-level unit activation state, i.e. generalization of SUB.
SUB    = The low-level unit activation state, values depend on unit type.

141 loaded units listed. Pass --all to see loaded but inactive units, too.
To show all installed unit files use 'systemctl list-unit-files'.
lines 70-141/141 (END)"""
    output3 = "user@debdev:/home/ute#"

    systemctl = Systemctl(connection=buffer_connection.moler_connection)
    assert "systemctl" == systemctl.command_string
    systemctl.start()
    time.sleep(0.1)
    outputs = [output1, output2, output3]
    for output in outputs:
        buffer_connection.moler_connection.data_received(output.encode("utf-8"), datetime.datetime.now())
    systemctl.await_done()
    assert systemctl.done() is True
