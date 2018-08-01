# -*- coding: utf-8 -*-
"""
Testing possibilities to configure devices
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import os

import pytest


def test_get_device_may_not_use_both__name_and_device_class():
    from moler.device.device import DeviceFactory

    with pytest.raises(AssertionError) as err:
        DeviceFactory.get_device(name='UNIX', device_class='moler.device.unixlocal', connection_desc={},
                                 connection_hops={})
    assert "Use either 'name' or 'device_class' parameter (not both)" in str(err)


def test_get_device_must_use_either_name_or_device_class():
    from moler.device.device import DeviceFactory

    with pytest.raises(AssertionError) as err:
        DeviceFactory.get_device(connection_desc={}, connection_hops={})
    assert "Provide either 'name' or 'device_class' parameter (none given)" in str(err)


def test_can_select_connection_by_name(device_config):
    from moler.device.device import DeviceFactory

    device_config.define_device(
        name="UNIX",
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc={
            "io_type": "terminal",
            "variant": "threaded"
        },
        connection_hops={}
    )
    device = DeviceFactory.get_device(name='UNIX')
    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test(device_config):
    from moler.device.device import DeviceFactory

    device_config.define_device(
        name="UNIX",
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc=None,
        connection_hops={}
    )
    device = DeviceFactory.get_device(name='UNIX')
    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_cannot_select_device_by_nonexisting_name(device_config):
    """Non-existing means here not defined inside configuration"""
    from moler.device.device import DeviceFactory

    with pytest.raises(KeyError) as err:
        DeviceFactory.get_device(name='UNIX')
    assert "Device named 'UNIX' was not defined inside configuration" in str(err)


def test_can_select_connection_loaded_from_config_file(moler_config):
    from moler.device.device import DeviceFactory

    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    moler_config.load_config(path=conn_config, config_type='yaml')

    device = DeviceFactory.get_device(name='UNIX')
    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_connection_loaded_from_env_variable(moler_config, monkeypatch):
    from moler.device.device import DeviceFactory

    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    monkeypatch.setitem(os.environ, 'MOLER_CONFIG', conn_config)
    moler_config.load_config(from_env_var="MOLER_CONFIG", config_type='yaml')

    device = DeviceFactory.get_device(name='UNIX')
    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_load_config_checks_env_variable_existence(moler_config):
    with pytest.raises(KeyError) as err:
        moler_config.load_config(from_env_var="MOLER_CONFIG", config_type='yaml')

    assert "Environment variable 'MOLER_CONFIG' is not set" in str(err.value)


# --------------------------- resources ---------------------------

@pytest.yield_fixture
def moler_config():
    import moler.config as moler_cfg
    yield moler_cfg
    # restore since tests may change configuration
    moler_cfg.clear()


@pytest.yield_fixture
def device_config():
    import moler.config.devices as dev_cfg
    yield dev_cfg
    # restore since tests may change configuration
    dev_cfg.clear()
