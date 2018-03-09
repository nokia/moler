# -*- coding: utf-8 -*-
"""
Testing external-IO TCP connection

- open/close
- send/receive (naming may differ)
"""

import pytest

__author__ = 'Dariusz Rosinski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_ps(ps_class):
    ps = ps_class()
    ps.get_pids()



@pytest.fixture()
def ps_class():
    from moler.cmd.unix.ps import Ps
    return Ps