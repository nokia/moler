# -*- coding: utf-8 -*-
"""
Package for implementing different commands based on Moler Command.
"""

__author__ = 'Grzegorz Latuszek, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2023, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com'

from re import search, match
from moler.exceptions import WrongUsage


class RegexHelper:
    """
    Class to help with working with regular expressions.
    """
    def __init__(self):
        """
        Initializes internal variables.
        """
        self._match = None

    def search(self, pattern, string, flags=0):
        """
        Searches for passed pattern in passed string.

        :param pattern: Pattern to find. Regular expression.
        :param string: String to scan through to find the pattern.
        :param flags: Flags for search.
        :return: Match object.
        """
        self._match = search(pattern, string, flags)
        return self._match

    def search_compiled(self, compiled, string, raise_if_compiled_is_none=False):
        """
        Searches for passed pattern in passed string.

        :param compiled: Compiled regular expression pattern to find.
        :param string: String to scan through to find the pattern.
        :param raise_if_compiled_is_none: set True to raise a WrongUsage if compiled is None. If False then return None.
        :return: Match object.
        """
        if compiled is None:
            if raise_if_compiled_is_none:
                exp = WrongUsage(f"{self} parameter compiled passed to search_compiled is None. Expected not None. String is '{string}'.")
                raise exp
            else:
                return None

        self._match = compiled.search(string)
        return self._match

    def match(self, pattern, string, flags=0):
        """
        Matches for passed pattern in passed string.

        :param pattern: Pattern to find. Regular expression.
        :param string: String to scan through to find the pattern.
        :param flags: Flags for search.
        :return: Match object.
        """
        self._match = match(pattern, string, flags)
        return self._match

    def match_compiled(self, compiled, string, raise_if_compiled_is_none=False):
        """
        Matches for passed pattern in passed string.

        :param compiled: Compiled regular expression pattern to find.
        :param string: String to scan through to find the pattern.
        :param raise_if_compiled_is_none: set True to raise a WrongUsage if compiled is None. If False then return None.
        :return: Match object.
        """
        if compiled is None:
            if raise_if_compiled_is_none:
                exp = WrongUsage(f"{self} parameter compiled passed to match_compiled is None. Expected not None. String is '{string}'.")
                raise exp
            else:
                return None
        self._match = compiled.match(string)
        return self._match

    def get_match(self):
        """
        Returns match object.

        :return: Match object.
        """
        return self._match

    def group(self, number):
        """
        Returns group from match object.

        :param number: Number or name of match object.
        :return: Match object.
        """
        if self._match is None:
            exp = WrongUsage(f"{self}. Nothing was matched before calling group in RegexHelper.")
            raise exp
        return self._match.group(number)

    def groups(self):
        """
        Returns groups from match object.

        :return: Groups from match object.
        """
        if self._match is None:
            exp = WrongUsage(f"{self}. Nothing was matched before calling groups in RegexHelper.")
            raise exp
        return self._match.groups()

    def groupdict(self):
        """
        Returns groupdict from match object.

        :return: Groupdict from match object.
        """
        if self._match is None:
            exp = WrongUsage(f"{self}. Nothing was matched before calling groupdict in RegexHelper")
            raise exp
        return self._match.groupdict()
