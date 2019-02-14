# -*- coding: utf-8 -*-
"""
Testing possibilities to configure devices
"""
__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import os

import pytest

from moler.util.moler_test import MolerTest


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
        connection_hops={},
    )
    device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_device_by_name_with_initial_state_set(device_config, device_factory):
    device_config.define_device(
        name="UNIX",
        device_class='moler.device.unixlocal.UnixLocal',
        connection_desc={
            "io_type": "terminal",
            "variant": "threaded"
        },
        connection_hops={},
        initial_state="NOT_CONNECTED"
    )
    device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'
    assert device.current_state == "NOT_CONNECTED"


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
    moler_config.load_config(config=conn_config, config_type='yaml')

    device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'


def test_can_select_all_devices_loaded_from_config_file(moler_config, device_factory):
    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    moler_config.load_config(config=conn_config, config_type='yaml')

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
    moler_config.load_config(config=conn_config, config_type='yaml')

    device = device_factory.get_device(name='UNIX')
    same_device = device_factory.get_device(name='UNIX')

    assert device.__module__ == 'moler.device.unixlocal'
    assert device.__class__.__name__ == 'UnixLocal'

    assert same_device.__module__ == 'moler.device.unixlocal'
    assert same_device.__class__.__name__ == 'UnixLocal'

    assert device == same_device


def test_log_error_when_not_abs_path_for_configuation_path_was_used(moler_config):
    @MolerTest.raise_background_exceptions(check_steps_end=True)
    def log_error_when_not_abs_path_for_configuation_path_was_used(moler_config):
        conn_config = os.path.join("resources", "device_config.yml")

        moler_config.load_config(config=conn_config, config_type='yaml')

        MolerTest.steps_end()

    from moler.exceptions import MolerStatusException

    with pytest.raises(MolerStatusException) as err:
        log_error_when_not_abs_path_for_configuation_path_was_used(moler_config)

    assert "For configuration file path: 'resources/device_config.yml' was used but absolute path is needed!" in str(
        err.value)


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

    assert "Provide either 'config' or 'from_env_var' parameter (none given)" in str(err.value)


def test_can_select_device_loaded_from_config_dict(moler_config, device_factory):
    @MolerTest.raise_background_exceptions(check_steps_end=True)
    def can_select_device_loaded_from_config_dict(moler_config, device_factory):
        conn_config = {
            'LOGGER': {
                'PATH': '/tmp/',
                'RAW_LOG': True,
                'DATE_FORMAT': '%d %H:%M:%S'
            },
            'DEVICES': {
                'UNIX': {
                    'DEVICE_CLASS': 'moler.device.unixremote.UnixLocal',
                    'INITIAL_STATE': 'UNIX_LOCAL'
                }
            }
        }
        moler_config.load_config(config=conn_config, config_type='dict')

        device = device_factory.get_device(name='UNIX')

        assert device.__module__ == 'moler.device.unixlocal'
        assert device.__class__.__name__ == 'UnixLocal'

        MolerTest.steps_end()

    can_select_device_loaded_from_config_dict(moler_config, device_factory)


def test_can_load_configuration_when_already_loaded_from_same_dict(moler_config, device_factory):
    @MolerTest.raise_background_exceptions(check_steps_end=True)
    def can_load_configuration_when_already_loaded_from_same_dict(moler_config, device_factory):
        conn_config = {
            'LOGGER': {
                'PATH': '/tmp/',
                'RAW_LOG': True,
                'DATE_FORMAT': '%d %H:%M:%S'
            },
            'DEVICES': {
                'UNIX': {
                    'DEVICE_CLASS': 'moler.device.unixremote.UnixLocal',
                    'INITIAL_STATE': 'UNIX_LOCAL'
                }
            }
        }
        moler_config.load_config(config=conn_config, config_type='dict')
        moler_config.load_config(config=conn_config, config_type='dict')

        MolerTest.steps_end()

    can_load_configuration_when_already_loaded_from_same_dict(moler_config, device_factory)


def test_cannot_load_configuration_when_already_loaded_from_another_dict(moler_config):
    @MolerTest.raise_background_exceptions(check_steps_end=True)
    def cannot_load_configuration_when_already_loaded_from_another_dict(moler_config):
        conn_config = {
            'LOGGER': {
                'PATH': '/tmp/',
                'RAW_LOG': True,
                'DATE_FORMAT': '%d %H:%M:%S'
            },
            'DEVICES': {
                'UNIX': {
                    'DEVICE_CLASS': 'moler.device.unixlocal.UnixLocal',
                    'INITIAL_STATE': 'UNIX_LOCAL'
                }
            }
        }

        new_conn_config = {
            'LOGGER': {
                'PATH': '/tmp/',
                'RAW_LOG': True,
                'DATE_FORMAT': '%d %H:%M:%S'
            },
            'DEVICES': {
                'UNIX': {
                    'DEVICE_CLASS': 'moler.device.unixremote.UnixRemote',
                    'INITIAL_STATE': 'UNIX_REMOTE'
                }
            }
        }
        moler_config.load_config(config=conn_config, config_type='dict')
        moler_config.load_config(config=new_conn_config, config_type='dict')

        MolerTest.steps_end()

    from moler.exceptions import MolerStatusException

    with pytest.raises(MolerStatusException) as err:
        cannot_load_configuration_when_already_loaded_from_another_dict(moler_config)

    assert "Reload configuration under one Moler execution not supported!" in str(err.value)


def test_cannot_load_configuration_when_already_loaded_from_another_file(moler_config):
    conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
    conn_config2 = os.path.join(os.path.dirname(__file__), "resources", "device_config2.yml")

    @MolerTest.raise_background_exceptions(check_steps_end=True)
    def cannot_load_configuration_when_already_loaded_from_another_file(moler_config, conn_config, conn_config2):
        moler_config.load_config(config=conn_config, config_type='yaml')

        moler_config.load_config(config=conn_config2, config_type='yaml')

        MolerTest.steps_end()

    from moler.exceptions import MolerStatusException

    with pytest.raises(MolerStatusException) as err:
        cannot_load_configuration_when_already_loaded_from_another_file(moler_config, conn_config, conn_config2)

    assert "Try to load '{}' config when '{}' config already loaded.\n" \
           "Reload configuration under one Moler execution not supported!".format(conn_config2, conn_config) in str(
            err.value)


def test_can_load_configuration_when_already_loaded_from_same_file(moler_config, device_factory):
    @MolerTest.raise_background_exceptions(check_steps_end=True)
    def can_load_configuration_when_already_loaded_from_same_file(moler_config, device_factory):
        conn_config = os.path.join(os.path.dirname(__file__), "resources", "device_config.yml")
        moler_config.load_config(config=conn_config, config_type='yaml')
        moler_config.load_config(config=conn_config, config_type='yaml')

        MolerTest.steps_end()

    can_load_configuration_when_already_loaded_from_same_file(moler_config, device_factory)


# --------------------------- resources ---------------------------

@pytest.yield_fixture
def moler_config():
    import moler.config as moler_cfg
    # restore since tests may change configuration
    clear_all_cfg()
    yield moler_cfg
    # restore since tests may change configuration
    clear_all_cfg()


@pytest.yield_fixture
def device_config():
    import moler.config.devices as dev_cfg
    # restore since tests may change configuration
    clear_all_cfg()
    yield dev_cfg
    # restore since tests may change configuration
    clear_all_cfg()


@pytest.yield_fixture
def device_factory():
    from moler.device.device import DeviceFactory as dev_factory
    # restore since tests may change configuration
    clear_all_cfg()
    yield dev_factory
    # restore since tests may change configuration
    clear_all_cfg()


def clear_all_cfg():
    import moler.config as moler_cfg
    import moler.config.devices as dev_cfg
    from moler.device.device import DeviceFactory as dev_factory

    moler_cfg.clear()
    dev_cfg.clear()
    dev_factory._clear()
