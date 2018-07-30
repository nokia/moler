from pytest import mark, raises

__author__ = 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.plichta@nokia.com'


@mark.parametrize("path2cmds", ["moler/cmd"])
def test_documentation_exists(path2cmds):
    from moler.util.cmds_doc import check_if_documentation_exists
    assert check_if_documentation_exists(path2cmds) is True


def test_buffer_connection_returns_threadconnection_with_moler_conn():
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.connection import ObservableConnection
    from moler.util.cmds_doc import _buffer_connection

    buff_conn = _buffer_connection()
    assert isinstance(buff_conn, ThreadedFifoBuffer) is True
    assert isinstance(buff_conn.moler_connection, ObservableConnection) is True
