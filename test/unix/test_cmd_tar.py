# -*- coding: utf-8 -*-
"""
Testing of tar command.
"""
__author__ = 'Yang Snackwell'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'snackwell.yang@nokia-sbell.com'


def test_tar_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.tar import Tar
    tar_cmd = Tar(buffer_connection, options="xzvf", file="test.tar.gz")
    assert "tar xzvf test.tar.gz" == tar_cmd.command_string
