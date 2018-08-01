# -*- coding: utf-8 -*-
"""
Testing of chgrp command.
"""
__author__ = 'Adrianna Pienkowska'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'


from moler.exceptions import CommandFailure
from moler.cmd.unix.chgrp import Chgrp
import pytest


def test_chgrp_returns_proper_command_string(buffer_connection):
    chgrp_cmd = Chgrp(connection=buffer_connection.moler_connection, files=["new"], group="test")
    assert "chgrp test new" == chgrp_cmd.command_string
