# -*- coding: utf-8 -*-
"""
Testing possibilities to configure devices
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import os
import pytest


def test_get_device_may_not_use_both__name_and_device_class(device_factory):
    with pytest.raises(AssertionError) as err:
        device_factory.get_device(name='UNIX', device_class='moler.device.unixlocal', connection_desc={},
                                  connection_hops={})
    assert "Use either 'name' or 'device_class' parameter (not both)" in str(err)


def test_get_device_must_use_either_name_or_device_class(device_factory):
    with pytest.raises(AssertionError) as err:
        device_factory.get_device(connection_desc={}, connection_hops={})
    assert "Provide either 'name' or 'device_class' parameter (none given)" in str(err)


def test_can_select_device_by_name(device_config, device_factory):
    device_config.define_device(
        name="UNIX",
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc={
            "io_type": "terminal",
            "variant": "threaded"
        },
        connection_hops={}
    )
    device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_device_by_description(device_factory):
    device = device_factory.get_device(
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc={
            "io_type": "terminal",
            "variant": "threaded"
        },
        connection_hops={}
    )

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_desc_device_by_default_connection_desc(device_factory):
    device = device_factory.get_device(
        device_class='moler.device.unixlocal.UnixLocal',
        connection_hops={}
    )

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_named_device_by_default_connection_desc(device_config, device_factory):
    device_config.define_device(
        name="UNIX",
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc=None,
        connection_hops={}
    )
    device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_cannot_select_named_device_without_connection(device_config, device_factory):
    device_config.define_device(
        name="UNIX",
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc=None,
        connection_hops={}
    )
    device_config.default_connection = None

    with pytest.raises(KeyError) as err:
        device_factory.get_device(name='UNIX')
    assert "No connection_desc selected (directly or via configuration)" in str(err)


def test_cannot_select_desc_device_without_connection(device_config, device_factory):
    device_config.default_connection = None

    with pytest.raises(KeyError) as err:
        device_factory.get_device(
            device_class='moler.device.unixlocal.UnixLocal',
            connection_hops={}
        )
    assert "No connection_desc selected (directly or via configuration)" in str(err)


def test_cannot_select_device_by_nonexisting_name(device_factory):
    """Non-existing means here not defined inside configuration"""
    with pytest.raises(KeyError) as err:
        device_factory.get_device(name='UNIX')
    assert "Device named 'UNIX' was not defined inside configuration" in str(err)


def test_can_select_device_loaded_from_config_file(moler_config, device_factory):
    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    moler_config.load_config(path=conn_config, config_type='yaml')

    device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_all_devices_loaded_from_config_file(moler_config, device_factory):
    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    moler_config.load_config(path=conn_config, config_type='yaml')

    device_factory.create_all_devices()

    device = device_factory._devices["UNIX"]

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_device_loaded_from_env_variable(moler_config, monkeypatch, device_factory):
    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    monkeypatch.setitem(os.environ, 'MOLER_CONFIG', conn_config)
    moler_config.load_config(from_env_var="MOLER_CONFIG", config_type='yaml')

    device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_load_config_checks_env_variable_existence(moler_config):
    with pytest.raises(KeyError) as err:
        moler_config.load_config(from_env_var="MOLER_CONFIG", config_type='yaml')

    assert "Environment variable 'MOLER_CONFIG' is not set" in str(err.value)


def test_return_created_device_when_call_another_time_for_same_named_device(moler_config, device_factory):
    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    moler_config.load_config(path=conn_config, config_type='yaml')

    device = device_factory.get_device(name='UNIX')
    same_device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'

    assert same_device.__module__ == 'moler.device.unixlocal'
    assert same_device.__class__.__name__ == 'UnixLocal'

    assert device == same_device


def test_return_new_device_when_call_another_time_same_desc_device(device_factory):
    device = device_factory.get_device(
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc={
            "io_type": "terminal",
            "variant": "threaded"
        },
        connection_hops={}
    )

    another_device = device_factory.get_device(
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc={
            "io_type": "terminal",
            "variant": "threaded"
        },
        connection_hops={}
    )

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'

    assert another_device.__module__ == 'moler.device.unixlocal'
    assert another_device.__class__.__name__ == 'UnixLocal'

    assert device != another_device


def test_cannot_load_config_from_when_path_or_from_env_var_not_provide(moler_config):
    with pytest.raises(AssertionError) as err:
        moler_config.load_config()

    assert "Provide either 'path' or 'from_env_var' parameter (none given)" in str(err.value)


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


@pytest.yield_fixture
def device_factory():
    from moler.device.device import DeviceFactory as dev_factory
    yield dev_factory
    # restore since tests may change configuration
    dev_factory._clear()
