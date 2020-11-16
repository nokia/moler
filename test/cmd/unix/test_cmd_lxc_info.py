# -*- coding: utf-8 -*-
"""
LxcInfo command test module.

:copyright: Nokia Networks
:author: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
:maintainer: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
"""

__author__ = 'Piotr Frydrych, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'piotr.frydrych@nokia.com'


from moler.cmd.unix.lxc_info import LxcInfo
from moler.exceptions import CommandFailure
import pytest


def test_lxc_info_raise_command_error(buffer_connection, command_output_and_expected_result):
    data, expected_result = command_output_and_expected_result
    buffer_connection.remote_inject_response(data)
    cmd = LxcInfo(name="0xe049", connection=buffer_connection.moler_connection, options="-z")
    with pytest.raises(CommandFailure):
        cmd()


def test_lxc_info_raise_container_name_error(buffer_connection, container_name_error_and_expected_result):
    data, expected_result = container_name_error_and_expected_result
    buffer_connection.remote_inject_response(data)
    cmd = LxcInfo(name="0xe0499", connection=buffer_connection.moler_connection)
    with pytest.raises(CommandFailure):
        cmd()


@pytest.fixture()
def command_output_and_expected_result():
    data = """
root@fct-0a:~ >lxc-info -n 0xe049 -z
lxc-info: invalid option -- 'z'
Usage: lxc-info --name=NAME

lxc-info display some information about a container with the identifier NAME

Options :
  -n, --name=NAME       NAME of the container
  -c, --config=KEY      show configuration variable KEY from running container
  -i, --ips             shows the IP addresses
  -p, --pid             shows the process id of the init container
  -S, --stats           shows usage stats
  -H, --no-humanize     shows stats as raw numbers, not humanized
  -s, --state           shows the state of the container
  --rcfile=FILE         Load configuration file FILE

Common options :
  -o, --logfile=FILE               Output log to FILE instead of stderr
  -l, --logpriority=LEVEL          Set log priority to LEVEL
  -q, --quiet                      Don't produce any output
  -P, --lxcpath=PATH               Use specified container path
  -?, --help                       Give this help list
      --usage                      Give a short usage message
      --version                    Print the version number

Mandatory or optional arguments to long options are also mandatory or optional
for any corresponding short options.

See the lxc-info man page for further information.

root@fct-0a:~ >"""

    result = {}

    return data, result


@pytest.fixture()
def container_name_error_and_expected_result():
    data = """lxc-info -n 0xe0499
0xe0499 doesn't exist
root@server:~ >"""

    result = {}

    return data, result
