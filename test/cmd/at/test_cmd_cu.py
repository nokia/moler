
Skip to content
Pull requests
Issues
Marketplace
Explore
@AdamKlekowski
nokia /
moler

12
47

    17

Code
Issues 5
Pull requests 2
Actions
Wiki
Security

    Insights

moler/test/cmd/unix/test_cmd_cd.py /
@marcin-usielski
marcin-usielski fix tests for exception
Latest commit 729f6c9 on 8 Jul 2020
History
2 contributors
@marcin-usielski
@Ernold11
91 lines (78 sloc) 3.35 KB
# -*- coding: utf-8 -*-
"""
Testing of cu command.
"""
__author__ = 'Adam Klekowski'
__copyright__ = 'Copyright (C) 2018-2020, Nokia'
__email__ = 'adam.klekowski@nokia.com'

import pytest
from moler.util.moler_test import MolerTest
from moler.exceptions import CommandFailure

