from os import listdir
from os.path import isfile, join, abspath, dirname

from pytest import mark, raises

__author__ = 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.plichta@nokia.com'


# --------------- helper functions ---------------
test_path = 'moler/cmd/at/'


def ffile(listing_type):
    """
    Quick and dirty function to return list of strings depends on parameter:
    - allfiles - list all file without path
    - fullpath  - list only py files with path
    - only_py  - list only py file without path

    :param listing_type:
    :return: list of files
    :rtype: list(str)
    """
    repo_path = abspath(join(dirname(__file__), '..'))
    abs_test_path = join(repo_path, test_path)
    file_list = []

    if listing_type == 'allfiles':
        file_list = [f for f in listdir(abs_test_path) if isfile(join(abs_test_path, f))]
    elif listing_type == 'fullpath':
        file_list = ['{}{}'.format(test_path, f) for f in listdir(abs_test_path)
                     if isfile(join(abs_test_path, f)) and '__init__' not in f and '.pyc' not in f]
    elif listing_type == 'only_py':
        file_list = [f for f in listdir(abs_test_path)
                     if isfile(join(abs_test_path, f)) and '__init__' not in f and '.pyc' not in f]
    return file_list
# --------------- helper functions ---------------


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
    from inspect import isgenerator, isgeneratorfunction

    file_list = ffile(listing_type='fullpath')
    walker = _walk_moler_python_files(test_path)

    assert isgeneratorfunction(_walk_moler_python_files) is True
    assert isgenerator(walker) is True

    gen_list = []
    for f in walker:
        gen_list.append(f)
    assert gen_list == file_list


def test_walk_moler_commands_is_generator_return_all_files_in_dir():
    from moler.util.cmds_doc import _walk_moler_commands
    from inspect import isgenerator, isgeneratorfunction
    from six.moves import zip

    file_list = ffile(listing_type='only_py')
    walker = _walk_moler_commands(test_path)

    assert isgeneratorfunction(_walk_moler_commands) is True
    assert isgenerator(walker) is True

    gen_list = []
    for cmd, file in zip(walker, file_list):
        gen_list.append(cmd)
        assert file in str(cmd[0])
    assert len(gen_list) == len(file_list)


def test_walk_moler_python_files_return_files_without_dunder_init():
    from moler.util.cmds_doc import _walk_moler_python_files

    file_list = ffile(listing_type='allfiles')
    walker = _walk_moler_python_files(test_path)

    with raises(StopIteration):
        for _ in range(len(file_list)):
            next(walker)


def test_walk_moler_commands_return_files_without_dunder_init():
    from moler.util.cmds_doc import _walk_moler_commands

    file_list = ffile(listing_type='allfiles')
    walker = _walk_moler_commands(test_path)

    with raises(StopIteration):
        for _ in range(len(file_list)):
            next(walker)
