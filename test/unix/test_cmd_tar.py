# -*- coding: utf-8 -*-
"""
Testing of tar command.
"""
__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'

import pytest


def test_tar_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.tar import Tar
    tar_cmd = Tar(buffer_connection, options="xzvf", file="test.tar.gz")
    assert "tar xzvf test.tar.gz" == tar_cmd.command_string


def test_tar_raise_exception_wrong_command_string(buffer_connection):
    from moler.cmd.unix.tar import Tar
    with pytest.raises(TypeError, match=r'.*missing \d+ required positional argument.*|__init__() takes at least \d+ arguments (\d+ given)'):
        Tar(buffer_connection, options="xzvf").command_string
