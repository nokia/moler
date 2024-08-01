# -*- coding: utf-8 -*-

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2024, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import pytest
import tempfile
import os
import six
import getpass
import platform
from moler.device.unixlocal import UnixLocal
from moler.event_awaiter import EventAwaiter


def test_many_commands_wait(unix_terminal):
    unix = unix_terminal
    cmd_ip_link = unix.get_cmd(cmd_name="ip_link", cmd_params={'action': 'show'})
    cmd_ip_addr = unix.get_cmd(cmd_name="ip_link", cmd_params={'action': 'show'})
    cmd_env = unix.get_cmd(cmd_name="env")
    cmd_ip_link.start()
    cmd_ip_addr.start()
    cmd_env.start()
    assert True is EventAwaiter.wait_for_all(timeout=10, events=[cmd_ip_link, cmd_ip_addr, cmd_env])
    env_ret = cmd_env.result()
    assert cmd_ip_addr.result() is not None
    assert cmd_ip_link.result() is not None
    assert "PWD" in env_ret


def test_ip_link(unix_terminal):
    unix = unix_terminal
    cmd_ip = unix.get_cmd(cmd_name="ip_link", cmd_params={'action': 'show'})
    ret = cmd_ip()
    assert ret is not None


def test_ip_neigh(unix_terminal):
    unix = unix_terminal
    cmd_ip = unix.get_cmd(cmd_name="ip_neigh", cmd_params={'options': 'show'})
    ret = cmd_ip()
    assert ret is not None


def test_enter(unix_terminal):
    unix = unix_terminal
    cmd_enter = unix.get_cmd(cmd_name="enter")
    cmd_enter()


def test_env(unix_terminal):
    unix = unix_terminal
    cmd_env = unix.get_cmd(cmd_name="env")
    ret = cmd_env()
    assert "PWD" in ret


def test_echo(unix_terminal):
    unix = unix_terminal
    text = "simple"
    cmd_echo = unix.get_cmd(cmd_name="echo", cmd_params={'text': text})
    ret = cmd_echo()
    assert text in ret['RESULT']


def test_dmesg(unix_terminal):
    unix = unix_terminal
    cmd_dmesg = unix.get_cmd(cmd_name="dmesg")
    ret = cmd_dmesg()
    assert 'LINES' in ret


def test_date(unix_terminal):
    unix = unix_terminal
    cmd_date = unix.get_cmd(cmd_name="date")
    ret = cmd_date()
    assert 'ZONE' in ret
    assert 'TIME' in ret


def test_uname(unix_terminal):
    unix = unix_terminal
    cmd_uname = unix.get_cmd(cmd_name="uname", cmd_params={"options": "-a"})
    ret = cmd_uname()
    found = False
    system_name = platform.system()
    for line in ret["RESULT"]:
        if system_name in line:
            found = True
    assert found


def test_whoami(unix_terminal):
    unix = unix_terminal
    cmd_whoami = unix.get_cmd(cmd_name="whoami")
    ret = cmd_whoami()
    assert getpass.getuser() == ret['USER']


def test_7z(unix_terminal):
    unix = unix_terminal
    cmd_7z = unix.get_cmd(cmd_name="7z", cmd_params={"options": "a", "archive_file": "arch.7z", "files": ["a", "b"],})
    assert cmd_7z is not None


def test_cp_md5sum_cat_mv_rm_ls(unix_terminal):
    unix = unix_terminal
    f = tempfile.NamedTemporaryFile(delete=False)
    file_content = "content"
    md5sum = "f75b8179e4bbe7e2b4a074dcef62de95"
    data = six.b(file_content + "\n")
    f.write(data)
    src = f.name
    f.close()
    tmp_dir = os.path.dirname(src)
    src_file = os.path.basename(src)
    dst_file = "dst.moler.file"
    dst = os.path.join(tmp_dir, dst_file)

    cmd_cat = unix.get_cmd(cmd_name="cat", cmd_params={"path": src})
    ret = cmd_cat()
    assert file_content in ret['LINES']

    cmd_md5sum = unix.get_cmd(cmd_name="md5sum", cmd_params={"path": src})
    ret = cmd_md5sum()
    assert ret["SUM"] == md5sum

    cmd_cp = unix.get_cmd(cmd_name="cp", cmd_params={"src": src, "dst": dst})
    cmd_cp()
    cmd_ls = unix.get_cmd(cmd_name="ls", cmd_params={"options": f"-l {tmp_dir}"})
    ret = cmd_ls()
    assert src_file in ret['files']
    assert dst_file in ret['files']

    cmd_rm = unix.get_cmd(cmd_name="rm", cmd_params={"file": dst})
    cmd_rm()
    cmd_ls = unix.get_cmd(cmd_name="ls", cmd_params={"options": '-l ' + tmp_dir})
    ret = cmd_ls()
    assert src_file in ret['files']
    assert dst_file not in ret['files']

    cmd_mv = unix.get_cmd(cmd_name="mv", cmd_params={"src": src, "dst": dst})
    cmd_mv()
    cmd_ls = unix.get_cmd(cmd_name="ls", cmd_params={"options": '-l ' + tmp_dir})
    ret = cmd_ls()
    assert src_file not in ret['files']
    assert dst_file in ret['files']

    cmd_rm = unix.get_cmd(cmd_name="rm", cmd_params={"file": dst})
    cmd_rm()
    cmd_ls = unix.get_cmd(cmd_name="ls", cmd_params={"options": '-l ' + tmp_dir})
    ret = cmd_ls()
    assert src_file not in ret['files']
    assert dst_file not in ret['files']


@pytest.fixture
def unix_terminal():
    unix = UnixLocal(io_type='terminal', variant='threaded')
    unix.establish_connection()
    yield unix
