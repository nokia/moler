# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Grzegorz Latuszek, Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, michal.ernst@nokia.com, marcin.usielski@nokia.com'

import copy
import datetime
import importlib
import logging
import re
from functools import wraps
from types import FunctionType, MethodType

import deepdiff

if datetime.time not in deepdiff.diff.numbers:
    deepdiff.diff.numbers = deepdiff.diff.numbers + (datetime.time,)

try:
    import collections.abc as collections
except ImportError:
    import collections


class ClassProperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


def copy_list(src, deep_copy=False):
    """
    Copies list, if None then returns empty list
    :param src: List to copy
    :param deep_copy: if False then shallow copy, if True then deep copy
    :return: Copied list
    """
    if src is None:
        return list()
    if deep_copy:
        return copy.deepcopy(src)
    return list(src)


def copy_dict(src, deep_copy=False):
    """
    Copies dict, if None then returns empty dict
    :param src: List to copy
    :param deep_copy: if False then shallow copy, if True then deep copy
    :return: Copied dict
    """
    if src is None:
        return dict()
    if deep_copy:
        return copy.deepcopy(src)
    return dict(src)


def instance_id(instance):
    """
    Return id of instance in hex form.
    Helps in logs/debugs/development troubleshooting.
    """
    instance_id = hex(id(instance))[2:]  # remove leading 0x
    return instance_id


def camel_case_to_lower_case_underscore(string):
    """
    Split string by upper case letters.
    F.e. useful to convert camel case strings to underscore separated ones.
    @return words (list)
    """
    words = []
    from_char_position = 0
    for current_char_position, char in enumerate(string):
        if char.isupper() and from_char_position < current_char_position:
            words.append(string[from_char_position:current_char_position].lower())
            from_char_position = current_char_position
    words.append(string[from_char_position:].lower())
    return '_'.join(words)


_re_escape_codes = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")  # Regex to remove color codes from command output


def remove_escape_codes(line):
    """
    :param line: line from terminal
    :return: line without terminal escape codes
    """
    line = re.sub(_re_escape_codes, "", line)
    return line


_re_remove_xterm_window_title_hack = re.compile(r'\x1b\x5d0;.*\x07')  # Regex to remove xterm hack for set window title


def remove_xterm_window_title_hack(line):
    """
    :param line: line from terminal
    :return: line without xterm windows title hack
    """
    line = re.sub(_re_remove_xterm_window_title_hack, "", line)
    return line


_re_remove_terminal_last_cmd_status = re.compile(r'\x1b]777;notify;.*\x07')


def remove_terminal_last_cmd_status(line):
    """
        :param line: line from terminal
        :return: line without terminal last cmd status
        """
    line = re.sub(_re_remove_terminal_last_cmd_status, "", line)
    return line


def remove_all_known_special_chars(line):
    """
    :param line: line from terminal
    :return: line without all known special chars
    """
    line = remove_escape_codes(line)
    line = remove_xterm_window_title_hack(line)
    line = remove_terminal_last_cmd_status(line)
    return line


def create_object_from_name(full_class_name, constructor_params):
    name_splitted = full_class_name.split('.')
    module_name = ".".join(name_splitted[:-1])
    class_name = name_splitted[-1]

    imported_module = importlib.import_module(module_name)
    class_imported = getattr(imported_module, class_name)
    obj = class_imported(**constructor_params)
    return obj


def update_dict(target_dict, expand_dict):
    for key, value in expand_dict.items():
        if (key in target_dict and isinstance(target_dict[key], dict) and isinstance(expand_dict[key],
                                                                                     collections.Mapping)):
            update_dict(target_dict[key], expand_dict[key])
        else:
            target_dict[key] = expand_dict[key]


def compare_objects(first_object, second_object, ignore_order=False, report_repetition=False, significant_digits=None,
                    exclude_paths=None, exclude_types=None, verbose_level=2):
    """
    Return difference between two objects.
    :param first_object: first object to compare
    :param second_object: second object to compare
    :param ignore_order: ignore difference in order
    :param report_repetition: report when is repetition
    :param significant_digits: use to properly compare numbers(float arithmetic error)
    :param exclude_paths: path which be excluded from comparison
    :param exclude_types: types which be excluded from comparison
    :param verbose_level: higher verbose level shows you more details - default 0.
    :return: difference between two objects
    """
    if exclude_paths is None:
        exclude_paths = set()
    if exclude_types is None:
        exclude_types = set()

    diff = deepdiff.DeepDiff(first_object, second_object, ignore_order=ignore_order,
                             report_repetition=report_repetition, significant_digits=significant_digits,
                             exclude_paths=exclude_paths, exclude_types=exclude_types, verbose_level=verbose_level)
    return diff


def convert_to_number(value):
    """
    Convert value to Python number type.
    :param value: value to convert
    :return: converted value if possible, otherwise original
    """
    if value and is_digit(value):
        try:
            value = int(value)
        except ValueError:
            value = float(value)
    return value


def is_digit(value):
    """
    Check that value is digit.
    :param value: value to check
    :return: True if value is digit, otherwise False
    """
    try:
        float(value)
        return True
    except ValueError:
        return False


class ForwardingHandler(logging.Handler):
    """
    Take log record and pass it to target_logger
    """

    def __init__(self, target_logger_name):
        super(ForwardingHandler, self).__init__(level=1)
        self.target_logger_name = target_logger_name
        self.target_logger = logging.getLogger('moler')

    def emit(self, record):
        """
        Emit a record.

        Output the record to the target_logger, catering for rollover as described
        in doRollover().
        """
        record.name = self.target_logger_name

        if (record.levelno == logging.INFO) or (record.levelname == "INFO"):
            record.levelno = logging.DEBUG
            record.levelname = "DEBUG"

        self.target_logger.handle(record)


def call_base_class_method_with_same_name(obj):
    """
    Run base class method.

    :param obj: class object which methods will be decorated.
    :return: class object with decorated methods
    """
    if hasattr(obj, "__dict__"):
        if obj.__dict__.items():
            for attributeName in dir(obj):
                attribute = getattr(obj, attributeName)

                if "_decorate" in dir(attribute):
                    if isinstance(attribute, (FunctionType, MethodType)):
                        setattr(obj, attributeName, _wrapper(method=attribute, obj=obj))

    return obj


def mark_to_call_base_class_method_with_same_name(func):
    """
    Mark method which base class method with same name will be call.
    :param func: function to mark.
    :return: marked function
    """
    func._decorate = True
    return func


def _wrapper(method, obj):
    if hasattr(method, '_already_decorated') and method._already_decorated:
        return method

    @wraps(method)
    def wrapped(*args, **kwargs):
        base_method = getattr(obj.__bases__[0], method.__name__)
        base_result = base_method(*args, **kwargs)

        result = method(*args, **kwargs)
        update_dict(base_result, result)

        return base_result

    wrapped._already_decorated = True
    return wrapped


def non_printable_chars_to_hex(source):
    """
    Converts input string into hex for all non printable chars, printable chars remain unchanged.
    :param source: input string.
    :return: output string witch exchanged chars.
    """
    import string
    output = ""
    for char in source:
        if char not in string.printable or char in ['\n', '\r']:
            output += "\\x{:02x}".format(ord(char))
        else:
            output += char
    return output


def all_chars_to_hex(source):
    """
    Converts input string into hex for all chars.
    :param source: input string.
    :return: output string witch exchanged chars.
    """
    output = ""
    for char in source:
        output += "\\x{:02x}".format(ord(char))
    return output
