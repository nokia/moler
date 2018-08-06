# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Grzegorz Latuszek, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, michal.ernst@nokia.com'

import re


class ClassProperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


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
