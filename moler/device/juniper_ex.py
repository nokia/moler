# -*- coding: utf-8 -*-
"""
JuniperEX module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.device.junipergeneric import JuniperGeneric
from moler.helpers import call_base_class_method_with_same_name, mark_to_call_base_class_method_with_same_name


@call_base_class_method_with_same_name
class JuniperEX(JuniperGeneric):
    """Juniperex device class."""

    pass
