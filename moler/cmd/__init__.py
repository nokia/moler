# -*- coding: utf-8 -*-
"""
Package for implementing different commands based on Moler Command.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

from re import search, match


class RegexHelper(object):

    def __init__(self):
        self._match = None

    def search(self, pattern, string, flags=0):
        self._match = search(pattern, string, flags)
        return self._match

    def search_compiled(self, compiled, string):
        self._match = compiled.search(string)
        return self._match

    def match(self, pattern, string, flags=0):
        self._match = match(pattern, string, flags)
        return self._match

    def match_compiled(self, compiled, string):
        self._match = compiled.match(string)
        return self._match

    def get_match(self):
        return self._match

    def group(self, number):
        return self._match.group(number)

    def groupdict(self):
        return self._match.groupdict()
