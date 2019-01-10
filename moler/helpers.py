# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Grzegorz Latuszek, Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, michal.ernst@nokia.com, marcin.usielski@nokia.com'

import importlib
import re
import copy
import logging


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


def create_object_from_name(full_class_name, constructor_params):
    name_splitted = full_class_name.split('.')
    module_name = ".".join(name_splitted[:-1])
    class_name = name_splitted[-1]

    imported_module = importlib.import_module(module_name)
    class_imported = getattr(imported_module, class_name)
    obj = class_imported(constructor_params)
    return obj


def update_dict(target_dict, expand_dict):
    for key, value in expand_dict.items():
        if (key in target_dict and isinstance(target_dict[key], dict) and isinstance(expand_dict[key],
                                                                                     collections.Mapping)):
            update_dict(target_dict[key], expand_dict[key])
        else:
            target_dict[key] = expand_dict[key]


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
