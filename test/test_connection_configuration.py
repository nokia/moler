# -*- coding: utf-8 -*-
"""
Testing possibilities to configure connections
"""
import pytest

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_get_connection_without_variant_selection_raises_KeyError():
    from moler.connection import get_connection

    with pytest.raises(KeyError) as err:
        get_connection(io_type='tcp', host='localhost', port=2345)
    assert "No variant selected (directly or via configuration) for 'tcp' connection" in str(err)


def test_can_select_connection_variant_from_buildin_connections():
    from moler.connection import get_connection
    from moler.config.connections import set_default_variant

    set_default_variant(io_type='tcp', variant='threaded')
    conn = get_connection(io_type='tcp', host='localhost', port=2345)
    assert conn.__module__ == 'moler.io.raw.tcp'
    assert conn.__class__.__name__ == 'ThreadedTcp'


def test_cannot_select_nonexisting_connection_variant():
    """Non-existing means not registered inside ConnectionFactory"""
    from moler.connection import get_connection
    from moler.config.connections import set_default_variant

    set_default_variant(io_type='tcp', variant='yedi_magic')
    with pytest.raises(KeyError) as err:
        get_connection(io_type='tcp', host='localhost', port=2345)
    assert "'yedi_magic' variant of 'tcp' connection is not registered inside ConnectionFactory" in str(err)


def test_can_select_connection_variant_from_plugin_connections(builtin_connection_factories):
    from moler.connection import ConnectionFactory, get_connection
    from moler.config.connections import set_default_variant

    class DummyTcpConnection(object):
        def __init__(self, host, port):
            pass

    ConnectionFactory.register_construction(io_type='tcp', variant='dummy',
                                            constructor=DummyTcpConnection)
    set_default_variant(io_type='tcp', variant='dummy')
    conn = get_connection(io_type='tcp', host='localhost', port=2345)
    assert conn.__class__.__name__ == 'DummyTcpConnection'


# --------------------------- resources ---------------------------


@pytest.yield_fixture
def builtin_connection_factories():
    import moler.connection  # installs builtin ones
    yield
    # restore since tests may overwrite builtins
    moler.connection._register_builtin_connections()
