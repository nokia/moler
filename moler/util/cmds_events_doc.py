# -*- coding: utf-8 -*-
"""
Perform command autotest for selected command(s).
"""

__author__ = 'Grzegorz Latuszek', 'Michal Ernst', 'Michal Plichta'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com', 'michal.ernst@nokia.com', 'michal.plichta@nokia.com'

import collections
import sys
from argparse import ArgumentParser
from datetime import datetime
from importlib import import_module
from os import walk, sep
from os.path import abspath, join, relpath, exists, split, dirname
from pprint import pformat

from moler.command import Command
from moler.event import Event
from moler.helpers import compare_objects


def _buffer_connection():
    """External-io based on memory FIFO-buffer"""
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.threaded_moler_connection import ThreadedMolerConnection

    class RemoteConnection(ThreadedFifoBuffer):
        def remote_inject_response(self, input_strings, delay=0.0):
            """
            Simulate remote endpoint that sends response.
            Response is given as strings.
            """
            try:
                in_bytes = [data.encode("utf-8") for data in input_strings]
            except UnicodeDecodeError:
                in_bytes = [data.decode("utf-8").encode("utf-8") for data in input_strings]
            self.inject_response(in_bytes, delay)

        def remote_inject(self, input_strings, delay=0.0):
            """
            Simulate remote endpoint that sends response.
            Response is given as strings.
            """
            try:
                in_bytes = [data.encode("utf-8") for data in input_strings]
            except UnicodeDecodeError:
                in_bytes = [data.decode("utf-8").encode("utf-8") for data in input_strings]
            self.inject(in_bytes, delay)

    moler_conn = ThreadedMolerConnection(encoder=lambda data: data.encode("utf-8"),
                                         decoder=lambda data: data.decode("utf-8"))
    ext_io_in_memory = RemoteConnection(moler_connection=moler_conn,
                                        echo=False)  # we don't want echo on it
    return ext_io_in_memory


def _walk_moler_python_files(path, *args):
    """
    Walk thru directory with commands and search for python source code (except __init__.py)
    Yield relative filepath to parameter path

    :param path: relative path do directory with commands
    :type path:
    :rtype: str
    """
    repo_path = abspath(join(path, '..', '..'))

    observer = "event" if "events" in split(path) else "command"
    print("Processing {}s test from path: '{}'".format(observer, path))

    for (dirpath, _, filenames) in walk(path):
        for filename in filenames:
            if filename.endswith('__init__.py'):
                continue
            if filename.endswith('.py'):
                abs_path = join(dirpath, filename)
                in_moler_path = relpath(abs_path, repo_path)
                yield in_moler_path


def _walk_moler_commands(path, base_class):
    for fname in _walk_moler_python_files(path=path):
        pkg_name = fname.replace(".py", "")
        parts = pkg_name.split(sep)
        pkg_name = ".".join(parts)
        moler_module = import_module(pkg_name)
        for _, cls in moler_module.__dict__.items():
            if not isinstance(cls, type):
                continue
            if not issubclass(cls, base_class):
                continue
            module_of_class = cls.__dict__['__module__']
            # take only Commands
            # take only the ones defined in given file (not imported ones)
            if (cls != base_class) and (module_of_class == pkg_name):
                yield moler_module, cls


def _walk_moler_nonabstract_commands(path, base_class):
    """
    We don't require COMMAND_OUTPUT/COMMAND_RESULT for base classes
    however, they should be abstract to block their instantiation.

    :param path: path to python module
    :type path: str
    """
    for moler_module, moler_class in _walk_moler_commands(path, base_class):
        try:
            _ = moler_class()
        except TypeError as err:
            if "Can't instantiate abstract class" in str(err):
                continue  # ABSTRACT BASE-CLASS COMMAND - skip it
        except Exception as err:
            print(str(err))
            pass  # other error of class instantiation, maybe missing args
        yield moler_module, moler_class


def _retrieve_command_documentation(moler_module, observer_type):
    test_data = {}
    for attr, value in moler_module.__dict__.items():
        for info in ['{}_OUTPUT'.format(observer_type),
                     '{}_KWARGS'.format(observer_type),
                     '{}_RESULT'.format(observer_type)]:
            if attr.startswith(info):
                variant = attr[len(info):]
                if variant not in test_data:
                    test_data[variant] = {}
                test_data[variant][info] = value
    return test_data


def _validate_documentation_existence(moler_module, test_data, observer_type):
    """Check if module has at least one variant of output documented"""
    if len(test_data.keys()) == 0:
        expected_info = '{}_OUTPUT/{}_KWARGS/{}_RESULT'.format(observer_type, observer_type, observer_type)
        error_msg = "{} is missing documentation: {}".format(moler_module, expected_info)
        return error_msg
    return ""


def _validate_documentation_consistency(moler_module, test_data, variant, observer_type):
    errors = []
    for attr in ['{}_OUTPUT'.format(observer_type), '{}_KWARGS'.format(observer_type),
                 '{}_RESULT'.format(observer_type)]:
        if attr in test_data[variant]:
            if '{}_OUTPUT'.format(observer_type) not in test_data[variant]:
                error_msg = "{} has {} but no {}_OUTPUT{}".format(moler_module, attr + variant, observer_type, variant)
                errors.append(error_msg)
            if '{}_KWARGS'.format(observer_type) not in test_data[variant]:
                error_msg = "{} has {} but no {}_KWARGS{}".format(moler_module, attr + variant, observer_type, variant)
                errors.append(error_msg)
            if '{}_RESULT'.format(observer_type) not in test_data[variant]:
                error_msg = "{} has {} but no {}_RESULT{}".format(moler_module, attr + variant, observer_type, variant)
                errors.append(error_msg)
    return errors


def _get_doc_variant(test_data, variant, observer_type):
    cmd_output = test_data[variant]['{}_OUTPUT'.format(observer_type)]
    # COMMAND_KWARGS is optional? missing == {}
    # or we should be direct "zen of Python"
    if '{}_KWARGS'.format(observer_type) in test_data[variant]:
        cmd_kwargs = test_data[variant]['{}_KWARGS'.format(observer_type)]
    else:
        cmd_kwargs = {}
    cmd_result = test_data[variant]['{}_RESULT'.format(observer_type)]
    return cmd_output, cmd_kwargs, cmd_result


def _create_command(moler_class, moler_connection, cmd_kwargs):
    """Can we construct instance with given params?"""
    arguments = ", ".join(["{}={}".format(param, value) for (param, value) in cmd_kwargs.items()])
    constructor_str = "{}({})".format(moler_class.__name__, arguments)
    try:
        moler_cmd = moler_class(connection=moler_connection, **cmd_kwargs)
        return moler_cmd, constructor_str
    except Exception as err:
        error_msg = "Can't create command instance via {} : {}".format(constructor_str, str(err))
        raise Exception(error_msg)


def _reformat_str_to_unicode(cmd_result):
    if (isinstance(cmd_result, dict)):
        for key, value in cmd_result.items():
            if (key in cmd_result and isinstance(cmd_result[key], dict) and isinstance(cmd_result[key],
                                                                                       collections.Mapping)):
                _reformat_str_to_unicode(cmd_result[key])
            else:
                if isinstance(cmd_result[key], str):
                    cmd_result[key] = cmd_result[key].decode('utf-8')
                    print(cmd_result[key])

    return cmd_result


def _convert_str_to_unicode(input):
    if isinstance(input, dict):
        return {_convert_str_to_unicode(key): _convert_str_to_unicode(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [_convert_str_to_unicode(element) for element in input]
    elif isinstance(input, str):
        return input.decode('utf-8')
    else:
        return input


def _run_command_parsing_test(moler_cmd, creation_str, buffer_io, cmd_output, cmd_result, variant, base_class,
                              observer_type):
    with buffer_io:  # open it (autoclose by context-mngr)
        exclude_types = None

        if base_class is Event:
            moler_cmd.start()
            buffer_io.remote_inject([cmd_output])
            result = moler_cmd.await_done(7)
            exclude_types = {datetime}
        elif base_class is Command:
            buffer_io.remote_inject_response([cmd_output])
            result = moler_cmd()

        if sys.version_info < (3, 0):
            # workaround for python2.7 - convert str to unicode
            cmd_result = _convert_str_to_unicode(cmd_result)
            result = _convert_str_to_unicode(result)

        diff = compare_objects(cmd_result, result, significant_digits=6, exclude_types=exclude_types)
        if diff:
            expected_result = pformat(cmd_result, indent=4)
            real_result = pformat(result, indent=4)
            diff = pformat(diff, indent=4)
            error_msg = "{} {} {} (see {}{}):\n{}\n{}:\n{}\n{}\n{}".format(observer_type, creation_str,
                                                                           'expected to return',
                                                                           '{}_RESULT'.format(observer_type), variant,
                                                                           expected_result,
                                                                           'but returned', real_result,
                                                                           'difference:', diff)
            return error_msg
    return ""


def check_cmd_or_event(path2cmds):
    if "events" in split(path2cmds):
        observer_type = "EVENT"
        base_class = Event
    else:
        observer_type = "COMMAND"
        base_class = Command

    return observer_type, base_class


def check_if_documentation_exists(path2cmds):
    """
    Check if documentation exists and has proper structure.

    :param path2cmds: relative path to comands directory
    :type path2cmds: str
    :return: True if all checks passed
    :rtype: bool
    """
    observer_type, base_class = check_cmd_or_event(path2cmds)
    wrong_commands = {}
    errors_found = []
    print()
    number_of_command_found = 0
    for moler_module, moler_class in _walk_moler_nonabstract_commands(path=path2cmds, base_class=base_class):
        number_of_command_found += 1
        print("processing: {}".format(moler_class))

        test_data = _retrieve_command_documentation(moler_module, observer_type)

        error_msg = _validate_documentation_existence(moler_module, test_data, observer_type)
        if error_msg:
            wrong_commands[moler_class.__name__] = 1
            errors_found.append(error_msg)
            continue

        for variant in test_data:
            error_msgs = _validate_documentation_consistency(moler_module, test_data, variant, observer_type)
            if error_msgs:
                wrong_commands[moler_class.__name__] = 1
                errors_found.extend(error_msgs)
                continue

            cmd_output, cmd_kwargs, cmd_result = _get_doc_variant(test_data, variant, observer_type)

            buffer_io = _buffer_connection()
            try:
                moler_cmd, creation_str = _create_command(moler_class,
                                                          buffer_io.moler_connection,
                                                          cmd_kwargs)
            except Exception as err:
                wrong_commands[moler_class.__name__] = 1
                errors_found.append(str(err))
                continue

            error_msg = _run_command_parsing_test(moler_cmd, creation_str,
                                                  buffer_io,
                                                  cmd_output, cmd_result,
                                                  variant,
                                                  base_class,
                                                  observer_type)
            if error_msg:
                wrong_commands[moler_class.__name__] = 1
                errors_found.append(error_msg)

    if errors_found:
        print("\n".join(errors_found))
        msg = "Following {} have incorrect documentation:".format(observer_type.lower())
        err_msg = "{}\n    {}".format(msg, "\n    ".join(wrong_commands.keys()))
        print(err_msg)
        return False
    if number_of_command_found == 0:
        err_msg = "No tests run! Not found any {} to test in path: '{}'!".format(observer_type.lower(), path2cmds)
        print(err_msg)
        return False
    print("All of {} processed {}s have correct documentation".format(number_of_command_found, observer_type.lower()))
    return True


if __name__ == '__main__':
    parser = ArgumentParser(description="Moler's Command(s) autotest")
    parser.add_argument('-c', '--cmd_filename', required=True, help='python module implementing given command')
    options = parser.parse_args()

    if not exists(options.cmd_filename):
        print('\n{} path doesn\'t exist!\n'.format(options.cmd_filename))
        parser.print_help()
        exit()
    else:
        check_if_documentation_exists(path2cmds=options.cmd_filename)
