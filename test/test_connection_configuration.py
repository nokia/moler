# -*- coding: utf-8 -*-
"""
Testing possibilities to configure connections
"""

__author__ = 'Grzegorz Latuszek, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, michal.ernst@nokia.com'

import os
import pytest


def test_get_connection_without_variant_selection_raises_KeyError():
    from moler.connection_factory import get_connection

    with pytest.raises(KeyError) as err:
        get_connection(io_type='tcp', host='localhost', port=2345)
    assert "No variant selected (directly or via configuration) for 'tcp' connection" in str(err.value)


def test_can_select_connection_variant_from_buildin_connections(connections_config):
    from moler.connection_factory import get_connection

    connections_config.set_default_variant(io_type='tcp', variant='threaded')
    conn = get_connection(io_type='tcp', host='localhost', port=2345)
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'


def test_cannot_select_nonexisting_connection_variant(connections_config):
    """Non-existing means not registered inside ConnectionFactory"""
    from moler.connection_factory import get_connection

    connections_config.set_default_variant(io_type='tcp', variant='yedi_magic')
    with pytest.raises(KeyError) as err:
        get_connection(io_type='tcp', host='localhost', port=2345)
    assert "'yedi_magic' variant of 'tcp' connection is not registered inside ConnectionFactory" in str(err.value)


def test_can_select_connection_variant_from_plugin_connections(builtin_connection_factories,
                                                               connections_config):
    from moler.connection_factory import ConnectionFactory, get_connection

    class DummyTcpConnection(object):
        def __init__(self, host, port):
            pass

    ConnectionFactory.register_construction(io_type='tcp', variant='dummy',
                                            constructor=DummyTcpConnection)
    connections_config.set_default_variant(io_type='tcp', variant='dummy')
    conn = get_connection(io_type='tcp', host='localhost', port=2345)
    assert conn.__class__.__name__ == 'DummyTcpConnection'


def test_get_connection_may_not_use_both__name_and_io_type():
    from moler.connection_factory import get_connection

    with pytest.raises(AssertionError) as err:
        get_connection(name='www_server_1',
                       io_type='tcp', host='localhost', port=2345)
    assert "Use either 'name' or 'io_type' parameter (not both)" in str(err.value)


def test_get_connection_must_use_either_name_or_io_type():
    from moler.connection_factory import get_connection

    with pytest.raises(AssertionError) as err:
        get_connection(host='localhost', port=2345)
    assert "Provide either 'name' or 'io_type' parameter (none given)" in str(err.value)


def test_can_select_connection_by_name(connections_config):
    from moler.connection_factory import get_connection

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
    from moler.connection_factory import get_connection

    connections_config.set_default_variant(io_type='tcp', variant='threaded')
    with pytest.raises(KeyError) as err:
        get_connection(name='www_server_1')
    assert "Connection named 'www_server_1' was not defined inside configuration" in str(err.value)


def test_can_select_connection_loaded_from_config_file(moler_config):
    from moler.connection_factory import get_connection

    conn_config = os.path.join(os.path.dirname(__file__), "resources", "www_servers_connections.yml")
    moler_config.load_config(config=conn_config, config_type='yaml')

    conn = get_connection(name='www_server_1')
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'
    assert conn.host == 'localhost'
    assert conn.port == 2345


@pytest.mark.parametrize('params', [{'from_env_var': "MOLER_CONFIG", 'config_type': "yaml"},  # test backward compatibility
                                    {'from_env_var': "MOLER_CONFIG"}])
def test_can_select_connection_loaded_from_env_variable(moler_config, monkeypatch, params):
    from moler.connection_factory import get_connection

    conn_config = os.path.join(os.path.dirname(__file__), "resources", "www_servers_connections.yml")
    monkeypatch.setitem(os.environ, 'MOLER_CONFIG', conn_config)
    moler_config.load_config(**params)

    conn = get_connection(name='www_server_1')
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'
    assert conn.host == 'localhost'
    assert conn.port == 2345


@pytest.mark.parametrize('params', [{'config': {'NAMED_CONNECTIONS': {'www_server_1': {'io_type': 'tcp', 'host': 'localhost', 'port': 2344}},
                                                'IO_TYPES': {'default_variant': {'tcp': 'threaded'}}},
                                     'config_type': "dict"},  # test backward compatibility
                                    {'config': {'NAMED_CONNECTIONS': {'www_server_1': {'io_type': 'tcp', 'host': 'localhost', 'port': 2344}},
                                                'IO_TYPES': {'default_variant': {'tcp': 'threaded'}}}}])
def test_can_select_connection_loaded_from_dict_as_keyword_args(moler_config, params):
    from moler.connection_factory import get_connection

    moler_config.load_config(**params)

    conn = get_connection(name='www_server_1')
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'
    assert conn.host == 'localhost'
    assert conn.port == 2344


@pytest.mark.parametrize('args', [({'NAMED_CONNECTIONS': {'www_server_1': {'io_type': 'tcp', 'host': 'localhost', 'port': 2344}},
                                    'IO_TYPES': {'default_variant': {'tcp': 'threaded'}}},
                                   None, 'dict'),  # test backward compatibility
                                  ({'NAMED_CONNECTIONS': {'www_server_1': {'io_type': 'tcp', 'host': 'localhost', 'port': 2344}},
                                    'IO_TYPES': {'default_variant': {'tcp': 'threaded'}}},)])
def test_can_select_connection_loaded_from_dict_as_positional_args(moler_config, args):
    from moler.connection_factory import get_connection

    moler_config.load_config(*args)

    conn = get_connection(name='www_server_1')
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'
    assert conn.host == 'localhost'
    assert conn.port == 2344


def test_load_config_checks_env_variable_existence(moler_config):
    with pytest.raises(KeyError) as err:
        moler_config.load_config(from_env_var="MOLER_CONFIG", config_type='yaml')

    assert "Environment variable 'MOLER_CONFIG' is not set" in str(err.value)


# --------------------------- resources ---------------------------

@pytest.yield_fixture
def moler_config():
    import moler.config as moler_cfg
    moler_cfg.loaded_config = "NOT_LOADED_YET"
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
    import moler.config.connections as connection_cfg
    yield
    # restore since tests may overwrite builtins
    connection_cfg.register_builtin_connections(moler.connection_factory.ConnectionFactory,
                                                moler.threaded_moler_connection.ThreadedMolerConnection)
