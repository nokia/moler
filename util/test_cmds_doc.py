# -*- coding: utf-8 -*-
"""
Perform command autotest for selected command(s).
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import argparse
import importlib
import pprint

import os.path
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from moler.command import Command
import moler

pp = pprint.PrettyPrinter(indent=4)


# ----------------------------------- input parameters parsing ----------------


def get_options():
    # parser = argparse.ArgumentParser(description='Command(s) autotest')
    #
    # # required
    # parser.add_argument("--cmd_filename", required=False,
    #                     help="python module implementing given command")
    #
    # options = parser.parse_args()
    # if options.cmd_filename:
    #     module_path = options.cmd_filename
    #     if not os.path.exists(module_path):
    #         print("\n{} path doesn't exist!\n".format(module_path))
    #         parser.print_help()
    #         exit()

    options = "moler/cmd"
    return options

# -----------------------------------------------------------------------------


def buffer_connection():
    """External-io based on memory FIFO-buffer"""
    from moler.io.raw.memory import ThreadedFifoBuffer
    from moler.connection import ObservableConnection

    class RemoteConnection(ThreadedFifoBuffer):
        def remote_inject_response(self, input_strings, delay=0.0):
            """
            Simulate remote endpoint that sends response.
            Response is given as strings.
            """
            in_bytes = [data.encode("utf-8") for data in input_strings]
            self.inject_response(in_bytes, delay)

    moler_conn = ObservableConnection(encoder=lambda data: data.encode("utf-8"),
                                      decoder=lambda data: data.decode("utf-8"))
    ext_io_in_memory = RemoteConnection(moler_connection=moler_conn,
                                        echo=False)  # we don't want echo on it
    return ext_io_in_memory


def walk_moler_python_files(path):
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            if filename.endswith('__init__.py'):
                continue
            if filename.endswith('.py'):
                rel_path = os.path.join(dirpath, filename)
                abs_path = os.path.abspath(rel_path)
                in_moler_path = os.path.relpath(abs_path, repo_path)
                yield in_moler_path


def walk_moler_commands(path):
    for fname in walk_moler_python_files(path=path):
        pkg_name = fname.replace(".py", "")
        parts = pkg_name.split(os.sep)
        pkg_name = ".".join(parts)
        moler_module = importlib.import_module(pkg_name)
        for name, cls in moler_module.__dict__.items():
            if not isinstance(cls, type):
                continue
            if not issubclass(cls, moler.command.Command):
                continue
            module_of_class = cls.__dict__['__module__']
            # take only Commands
            # take only the ones defined in given file (not imported ones)
            if (cls != moler.command.Command) and (module_of_class == pkg_name):
                yield moler_module, cls


def walk_moler_nonabstract_commands(path):
    for moler_module, moler_class in walk_moler_commands(path):
        # We don't require COMMAND_OUTPUT/COMMAND_RESULT for base classes
        # however, they should be abstract to block their instantiation
        try:
            cmd_instance = moler_class()
        except TypeError as err:
            if "Can't instantiate abstract class" in str(err):
                continue  # ABSTRACT BASE-CLASS COMMAND - skip it
            pass  # other error of class instantiation, maybe missing args
        except Exception as err:
            pass  # other error of class instantiation, maybe missing args
        yield moler_module, moler_class


def retrieve_command_documentation(moler_module):
    test_data = {}
    for attr, value in moler_module.__dict__.items():
        for info in ['COMMAND_OUTPUT', 'COMMAND_KWARGS', 'COMMAND_RESULT']:
            if attr.startswith(info):
                variant = attr[len(info):]
                if variant not in test_data:
                    test_data[variant] = {}
                test_data[variant][info] = value
    return test_data


def validate_documentation_existence(moler_module, test_data):
    """Check if module has at least one variant of output documented"""
    if len(test_data.keys()) == 0:
        expected_info = 'COMMAND_OUTPUT/COMMAND_KWARGS/COMMAND_RESULT'
        error_msg = "{} is missing documentation: {}".format(moler_module, expected_info)
        return error_msg
    return ""


def validate_documentation_consistency(moler_module, test_data, variant):
    errors = []
    for attr in ['COMMAND_OUTPUT', 'COMMAND_KWARGS', 'COMMAND_RESULT']:
        if attr in test_data[variant]:
            if 'COMMAND_OUTPUT' not in test_data[variant]:
                error_msg = "{} has {} but no {}".format(moler_module,
                                                         attr + variant,
                                                         'COMMAND_OUTPUT' + variant)
                errors.append(error_msg)
            if 'COMMAND_KWARGS' not in test_data[variant]:
                error_msg = "{} has {} but no {}".format(moler_module,
                                                         attr + variant,
                                                         'COMMAND_KWARGS' + variant)
                errors.append(error_msg)
            if 'COMMAND_RESULT' not in test_data[variant]:
                error_msg = "{} has {} but no {}".format(moler_module,
                                                         attr + variant,
                                                         'COMMAND_RESULT' + variant)
                errors.append(error_msg)
    return errors


def get_doc_variant(test_data, variant):
    cmd_output = test_data[variant]['COMMAND_OUTPUT']
    # COMMAND_KWARGS is optional? missing == {}
    # or we should be direct "zen of Python"
    if 'COMMAND_KWARGS' in test_data[variant]:
        cmd_kwargs = test_data[variant]['COMMAND_KWARGS']
    else:
        cmd_kwargs = {}
    cmd_result = test_data[variant]['COMMAND_RESULT']
    return cmd_output, cmd_kwargs, cmd_result


def create_command(moler_class, moler_connection, cmd_kwargs):
    """Can we construct instance with given params?"""
    arguments = ", ".join(["{}={}".format(param, value) for (param, value) in cmd_kwargs.items()])
    constructor_str = "{}({})".format(moler_class.__name__, arguments)
    try:
        moler_cmd = moler_class(connection=moler_connection, **cmd_kwargs)
        return moler_cmd, constructor_str
    except Exception as err:
        error_msg = "Can't create command instance via {} : {}".format(constructor_str, str(err))
        raise Exception(error_msg)


def run_command_parsing_test(moler_cmd, creation_str, buffer_io,
                             cmd_output, cmd_result, variant):
    with buffer_io:  # open it (autoclose by context-mngr)
        buffer_io.remote_inject_response([cmd_output])
        result = moler_cmd()
        if result != cmd_result:
            expected_result = pprint.pformat(cmd_result, indent=4)
            real_result = pprint.pformat(result, indent=4)
            error_msg = "Command {} {} (see {}{}):\n{}\n{}:\n{}".format(creation_str,
                                                                        'expected to return',
                                                                        'COMMAND_RESULT',
                                                                        variant,
                                                                        expected_result,
                                                                        'but returned',
                                                                        real_result)
            return error_msg
    return ""


def test_documentation_exists():
    options = get_options()
    wrong_commands = {}
    errors_found = []

    for moler_module, moler_class in walk_moler_nonabstract_commands(path=options):
        print("processing: {}, {} ".format(moler_module, moler_class))

        test_data = retrieve_command_documentation(moler_module)

        error_msg = validate_documentation_existence(moler_module, test_data)
        if error_msg:
            wrong_commands[moler_class.__name__] = 1
            errors_found.append(error_msg)
            continue

        for variant in test_data:
            error_msgs = validate_documentation_consistency(moler_module, test_data, variant)
            if error_msgs:
                wrong_commands[moler_class.__name__] = 1
                errors_found.extend(error_msgs)
                continue

            cmd_output, cmd_kwargs, cmd_result = get_doc_variant(test_data, variant)

            buffer_io = buffer_connection()
            try:
                moler_cmd, creation_str = create_command(moler_class,
                                                         buffer_io.moler_connection,
                                                         cmd_kwargs)
            except Exception as err:
                wrong_commands[moler_class.__name__] = 1
                errors_found.append(str(err))
                continue

            error_msg = run_command_parsing_test(moler_cmd, creation_str,
                                                 buffer_io,
                                                 cmd_output, cmd_result,
                                                 variant)
            if error_msg:
                wrong_commands[moler_class.__name__] = 1
                errors_found.append(error_msg)

    if errors_found:
        print("\n".join(errors_found))
        msg = "Following commands have incorrect documentation:"
        err_msg = "{}\n    {}".format(msg, "\n    ".join(wrong_commands.keys()))
        sys.exit(err_msg)
    print("All processed commands have correct documentation")


if __name__ == '__main__':
    test_documentation_exists()
