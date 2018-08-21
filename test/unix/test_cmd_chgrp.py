# -*- coding: utf-8 -*-
"""
Testing of chgrp command.
"""
__author__ = 'Adrianna Pienkowska '
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com'


from moler.exceptions import CommandFailure
from moler.cmd.unix.chgrp import Chgrp
import pytest


def test_chgrp_returns_proper_command_string(buffer_connection):
    chgrp_cmd = Chgrp(connection=buffer_connection.moler_connection, files=["new"], group="test")
    assert "chgrp test new" == chgrp_cmd.command_string


def test_chgrp_raise_error(buffer_connection):
    chgrp_cmd = Chgrp(connection=buffer_connection.moler_connection, options='-abc', files=["new"], group="test")
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    assert "chgrp -abc test new" == chgrp_cmd.command_string
    with pytest.raises(CommandFailure):
        chgrp_cmd()


@pytest.fixture
def command_output_and_expected_result():
    output = """xyz@debian:~$ chgrp -abc test new
chgrp: invalid option -- 'a'
Try 'chgrp --help' for more information.
xyz@debian:~$"""
    result = dict()
    return output, result
