# -*- coding: utf-8 -*-
"""
Moler related configuration
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import yaml
from contextlib import contextmanager

from . import connections as conn_cfg


@contextmanager
def read_configfile(path):
    """
    Context manager that reads content of configuration file into string

    :param path: location of configuration file
    :return: configuration file content as string
    """
    with open(path, 'r') as config_file:
        content = config_file.read()
        yield content


def read_yaml_configfile(path):
    """
    Read and convert YAML into dictionary

    :param path: location of yaml file
    :return: configuration as a python dictionary
    """
    with read_configfile(path) as content:
        return yaml.load(content)


def load_config(path, config_type='yaml'):
    """Load Moler's configuration from config file"""
    assert config_type == 'yaml'  # no other format supported yet
    config = read_yaml_configfile(path)
    # TODO: check schema
    if 'NAMED_CONNECTIONS' in config:
        for name, connection_specification in config['NAMED_CONNECTIONS'].items():
            io_type = connection_specification.pop("io_type")
            conn_cfg.define_connection(name, io_type, **connection_specification)
    if 'IO_TYPES' in config:
        if 'default_variant' in config['IO_TYPES']:
            defaults = config['IO_TYPES']['default_variant']
            for io_type, variant in defaults.items():
                conn_cfg.set_default_variant(io_type, variant)


def clear():
    """Cleanup Moler's configuration"""
    conn_cfg.clear()
