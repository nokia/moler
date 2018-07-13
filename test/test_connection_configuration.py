# -*- coding: utf-8 -*-
"""
Testing possibilities to configure connections
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import os
import pytest


def test_get_connection_without_variant_selection_raises_KeyError():
    from moler.connection import get_connection

    with pytest.raises(KeyError) as err:
        get_connection(io_type='tcp', host='localhost', port=2345)
    assert "No variant selected (directly or via configuration) for 'tcp' connection" in str(err)


def test_can_select_connection_variant_from_buildin_connections(connections_config):
    from moler.connection import get_connection

    connections_config.set_default_variant(io_type='tcp', variant='threaded')
    conn = get_connection(io_type='tcp', host='localhost', port=2345)
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'


def test_cannot_select_nonexisting_connection_variant(connections_config):
    """Non-existing means not registered inside ConnectionFactory"""
    from moler.connection import get_connection

    connections_config.set_default_variant(io_type='tcp', variant='yedi_magic')
    with pytest.raises(KeyError) as err:
        get_connection(io_type='tcp', host='localhost', port=2345)
    assert "'yedi_magic' variant of 'tcp' connection is not registered inside ConnectionFactory" in str(err)


def test_can_select_connection_variant_from_plugin_connections(builtin_connection_factories,
                                                               connections_config):
    from moler.connection import ConnectionFactory, get_connection

    class DummyTcpConnection(object):
        def __init__(self, host, port):
            pass

    ConnectionFactory.register_construction(io_type='tcp', variant='dummy',
                                            constructor=DummyTcpConnection)
    connections_config.set_default_variant(io_type='tcp', variant='dummy')
    conn = get_connection(io_type='tcp', host='localhost', port=2345)
    assert conn.__class__.__name__ == 'DummyTcpConnection'


def test_get_connection_may_not_use_both__name_and_io_type():
    from moler.connection import get_connection

    with pytest.raises(AssertionError) as err:
        get_connection(name='www_server_1',
                       io_type='tcp', host='localhost', port=2345)
    assert "Use either 'name' or 'io_type' parameter (not both)" in str(err)


def test_get_connection_must_use_either_name_or_io_type():
    from moler.connection import get_connection

    with pytest.raises(AssertionError) as err:
        get_connection(host='localhost', port=2345)
    assert "Provide either 'name' or 'io_type' parameter (none given)" in str(err)


def test_can_select_connection_by_name(connections_config):
    from moler.connection import get_connection

    connections_config.define_connection(name="www_server_1",
                                         io_type='tcp',
                                         host='localhost', port=2345)
    connections_config.set_default_variant(io_type='tcp', variant='threaded')
    conn = get_connection(name='www_server_1')
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'
    assert conn.host == 'localhost'
    assert conn.port == 2345


def test_cannot_select_connection_by_nonexisting_name(connections_config):
    """Non-existing means here not defined inside configuration"""
    from moler.connection import get_connection

    connections_config.set_default_variant(io_type='tcp', variant='threaded')
    with pytest.raises(KeyError) as err:
        get_connection(name='www_server_1')
    assert "Connection named 'www_server_1' was not defined inside configuration" in str(err)


def test_can_select_connection_loaded_from_config_file(moler_config):
    from moler.connection import get_connection

    conn_config = os.path.join(os.path.dirname(__file__), "resources", "www_servers_connections.yml")
    moler_config.load_config(path=conn_config, config_type='yaml')

    conn = get_connection(name='www_server_1')
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'
    assert conn.host == 'localhost'
    assert conn.port == 2345


def test_can_select_connection_loaded_from_env_variable(moler_config, monkeypatch):
    from moler.connection import get_connection

    conn_config = os.path.join(os.path.dirname(__file__), "resources", "www_servers_connections.yml")
    monkeypatch.setitem(os.environ, 'MOLER_CONFIG', conn_config)
    moler_config.load_config(from_env_var="MOLER_CONFIG", config_type='yaml')

    conn = get_connection(name='www_server_1')
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'
    assert conn.host == 'localhost'
    assert conn.port == 2345


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
def connections_config():
    import moler.config.connections as conn_cfg
    yield conn_cfg
    # restore since tests may change configuration
    conn_cfg.clear()


@pytest.yield_fixture
def builtin_connection_factories():
    import moler.connection  # installs builtin ones
    yield
    # restore since tests may overwrite builtins
    moler.connection._register_builtin_connections()
