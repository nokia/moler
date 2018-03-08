"""
:copyright: Nokia Networks
:author: Marcin Usielski
:contact: marcin.usielski@nokia.com
:maintainer:
:contact:
"""

import re


class RegexHelper(object):
    instance = None

    def __init__(self):
        self.match = None

    def search(self, pattern, string, flags=0):
        self.match = re.search(pattern, string, flags)
        return self.match

    def search_compiled(self, compiled, string):
        self.match = compiled.search(string)
        return self.match

    def match(self, pattern, string, flags=0):
        self.match = re.match(pattern, string, flags)
        return self.match

    def match_compiled(self, compiled, string):
        self.match = compiled.match(string)
        return self.match

    def get_match(self):
        return self.match

    def group(self, number):
        return self.match.group(number)

    @staticmethod
    def get_regex_helper():
        if RegexHelper.instance is None:
            RegexHelper.instance = RegexHelper()
        return RegexHelper.instance

