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


def test_walk_moler_python_files_is_generator_return_all_files_in_dir():
    from moler.util.cmds_doc import _walk_moler_python_files
    from inspect import isgenerator
    from os import listdir
    from os.path import isfile, join, abspath, dirname

    test_path = 'moler/cmd/at/'
    repo_path = abspath(join(dirname(__file__), '..'))
    abs_test_path = join(repo_path, test_path)
    file_list = ['{}{}'.format(test_path, f) for f in listdir(abs_test_path)
                 if isfile(join(abs_test_path, f)) and '__init__' not in f]

    walker = _walk_moler_python_files(test_path)
    assert isgenerator(walker) is True

    gen_list = []
    for f in walker:
        gen_list.append(f)
    assert gen_list == file_list
