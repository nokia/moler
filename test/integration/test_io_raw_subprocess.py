# -*- coding: utf-8 -*-
"""
Testing external-IO subprocess connection

- open/close
- send/receive (naming may differ)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import importlib
import sys
import pytest


def test_can_open_connection(subprocess_connection_class):
    """
    We open subprocess connection to another python process:
    - confirming "open success" by catching python prompt
    - OS independent test since using python not OS-shell (bash/cmd)
    - full path to python we get from sys.executable
    - not so "atomic" since uses connection's "read" to verify open
    """
    pass


# --------------------------- resources ---------------------------


@pytest.fixture(params=['Subprocess', 'ThreadedSubprocess'])
def subprocess_connection_class(request):
    class_name = request.param
    module = importlib.import_module('moler.io.raw.subprocess')
    connection_class = getattr(module, class_name)
    return connection_class
