# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Connections related configuration
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


default_variant = {}


def set_default_variant(io_type, variant):
    """Set variant to use as default when requesting 'io_type' connection"""
    default_variant[io_type] = variant
