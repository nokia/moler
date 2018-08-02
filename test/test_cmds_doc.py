from importlib import import_module
from os import listdir
from os.path import isfile, join, abspath, dirname

from mock import mock
from pytest import mark, raises

__author__ = 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.plichta@nokia.com'


cmd_dir_under_test = 'moler/cmd/at/'


# --------------- helper functions ---------------
def _list_in_path(listing_type):
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
    abs_test_path = join(repo_path, cmd_dir_under_test)
    file_list = []

    if listing_type == 'allfiles':
        file_list = [f for f in listdir(abs_test_path) if isfile(join(abs_test_path, f))]
    elif listing_type == 'fullpath':
        file_list = ['{}{}'.format(cmd_dir_under_test, f) for f in listdir(abs_test_path)
                     if isfile(join(abs_test_path, f)) and '__init__' not in f and '.pyc' not in f]
    elif listing_type == 'only_py':
        file_list = [f for f in listdir(abs_test_path)
                     if isfile(join(abs_test_path, f)) and '__init__' not in f and '.pyc' not in f]
    return file_list


def _load_obj(func_name):
    """
    Load instance form module.

    :param func_name: function name as string
    :return: object instance
    :rtype: type
    """
    return getattr(import_module('moler.util.cmds_doc'), func_name)
# --------------- helper functions ---------------


def test_documentation_exists():
    from moler.util.cmds_doc import check_if_documentation_exists
    assert check_if_documentation_exists("moler/cmd") is True


def test_buffer_connection_returns_threadconnection_with_moler_conn():
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.connection import ObservableConnection
    from moler.util.cmds_doc import _buffer_connection

    buff_conn = _buffer_connection()
    assert isinstance(buff_conn, ThreadedFifoBuffer) is True
    assert isinstance(buff_conn.moler_connection, ObservableConnection) is True


@mark.parametrize('func2test,method_param,expected', [
    ('_walk_moler_python_files', cmd_dir_under_test, True),
    ('_walk_moler_commands', cmd_dir_under_test, True),
    ('_walk_moler_nonabstract_commands', cmd_dir_under_test, True)])
def test_functions_are_generators(func2test, method_param, expected):
    from inspect import isgenerator, isgeneratorfunction

    func_obj = _load_obj(func_name=func2test)
    generator_obj = func_obj(method_param)

    assert isgeneratorfunction(func_obj) is expected
    assert isgenerator(generator_obj) is expected


def test_walk_moler_python_files_is_generator_return_all_files_in_dir():
    from moler.util.cmds_doc import _walk_moler_python_files

    file_list = _list_in_path(listing_type='fullpath')
    walker = _walk_moler_python_files(cmd_dir_under_test)

    list_from_generator = []
    for file in walker:
        list_from_generator.append(file)
    assert list_from_generator == file_list


def test_walk_moler_commands_is_generator_return_all_files_in_dir():
    from moler.util.cmds_doc import _walk_moler_commands
    from six.moves import zip

    file_list = _list_in_path(listing_type='only_py')
    walker = _walk_moler_commands(cmd_dir_under_test)

    list_from_generator = []
    for cmd, file in zip(walker, file_list):
        list_from_generator.append(cmd)
        assert file in str(cmd[0])
    assert len(list_from_generator) == len(file_list)


@mark.parametrize('func2test,method_param', [
    ('_walk_moler_python_files', cmd_dir_under_test),
    ('_walk_moler_commands', cmd_dir_under_test),
    ('_walk_moler_nonabstract_commands', cmd_dir_under_test)])
def test_genertors_return_files_without_dunder_init(func2test, method_param):
    func_obj = _load_obj(func_name=func2test)
    generator_obj = func_obj(method_param)
    file_list = _list_in_path(listing_type='allfiles')

    with raises(StopIteration):
        for _ in range(len(file_list)):
            next(generator_obj)


def test_walk_moler_nonabstract_commands_raise_exception_when_called(fake_cmd):
    from moler.util.cmds_doc import _walk_moler_nonabstract_commands

    with mock.patch('moler.util.cmds_doc._walk_moler_commands', return_value=(None, fake_cmd)):
        with raises(Exception):
            next(_walk_moler_nonabstract_commands(cmd_dir_under_test))


def test_retrieve_command_documentation_as_dict():
    from moler.util.cmds_doc import _retrieve_command_documentation

    fake_cmd_from_conftest = _retrieve_command_documentation(import_module('conftest'))
    assert isinstance(fake_cmd_from_conftest, dict)
    assert isinstance(fake_cmd_from_conftest['_ver_nice'], dict)
    assert isinstance(fake_cmd_from_conftest['_ver_nice']['COMMAND_OUTPUT'], str)
    assert isinstance(fake_cmd_from_conftest['_ver_nice']['COMMAND_KWARGS'], dict)
    assert isinstance(fake_cmd_from_conftest['_ver_nice']['COMMAND_RESULT'], dict)


def test_validate_documentation_existence():
    from moler.util.cmds_doc import _validate_documentation_existence
    fake_cmd = import_module('conftest')

    test_data = {'_ver_execute': {'COMMAND_OUTPUT': '', 'COMMAND_KWARGS': {}, 'COMMAND_RESULT': {}},
                 '_ver_test': {'COMMAND_OUTPUT': '', 'COMMAND_KWARGS': {}, 'COMMAND_RESULT': {}}}
    assert _validate_documentation_existence(fake_cmd, test_data) == ''

    missing = _validate_documentation_existence(fake_cmd, {})
    assert 'conftest' in missing
    assert 'is missing documentation: COMMAND_OUTPUT/COMMAND_KWARGS/COMMAND_RESULT' in missing


def test_validate_documentation_consistency():
    from moler.util.cmds_doc import _validate_documentation_consistency
    fake_cmd = import_module('conftest')

    test_data = {'_ver_test1': {'COMMAND_KWARGS': {}, 'COMMAND_RESULT': {}},
                 '_ver_test2': {'COMMAND_OUTPUT': '', 'COMMAND_RESULT': {}},
                 '_ver_test3': {'COMMAND_OUTPUT': '', 'COMMAND_KWARGS': {}}}
    result1 = _validate_documentation_consistency(fake_cmd, test_data, '_ver_test1')
    result2 = _validate_documentation_consistency(fake_cmd, test_data, '_ver_test2')
    result3 = _validate_documentation_consistency(fake_cmd, test_data, '_ver_test3')

    assert isinstance(result1, list)
    assert isinstance(result2, list)
    assert isinstance(result3, list)
    assert "<module 'conftest' from" in result1[0] and "<module 'conftest' from" in result1[0]
    assert "<module 'conftest' from" in result2[0] and "<module 'conftest' from" in result2[0]
    assert "<module 'conftest' from" in result3[0] and "<module 'conftest' from" in result3[0]
    assert "test/conftest.py'> has COMMAND_KWARGS_ver_test1 but no COMMAND_OUTPUT_ver_test1" in result1[0]
    assert "test/conftest.py'> has COMMAND_RESULT_ver_test1 but no COMMAND_OUTPUT_ver_test1" in result1[1]
    assert "test/conftest.py'> has COMMAND_OUTPUT_ver_test2 but no COMMAND_KWARGS_ver_test2" in result2[0]
    assert "test/conftest.py'> has COMMAND_RESULT_ver_test2 but no COMMAND_KWARGS_ver_test2" in result2[1]
    assert "test/conftest.py'> has COMMAND_OUTPUT_ver_test3 but no COMMAND_RESULT_ver_test3" in result3[0]
    assert "test/conftest.py'> has COMMAND_KWARGS_ver_test3 but no COMMAND_RESULT_ver_test3" in result3[1]


def test_get_doc_variant():
    from moler.util.cmds_doc import _get_doc_variant

    test_data = {'_ver_test1': {'COMMAND_OUTPUT': 'out1', 'COMMAND_KWARGS': {1: 1}, 'COMMAND_RESULT': {1: 1}},
                 '_ver_test2': {'COMMAND_OUTPUT': 'out2', 'COMMAND_RESULT': {2: 2}}}
    result1 = _get_doc_variant(test_data, '_ver_test1')
    result2 = _get_doc_variant(test_data, '_ver_test2')

    assert result1 == ('out1', {1: 1}, {1: 1})
    assert result2 == ('out2', {}, {2: 2})
