# -*- coding: utf-8 -*-
"""
Moler related configuration
"""
import os

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


def load_config(path=None, from_env_var=None, config_type='yaml'):
    """
    Load Moler's configuration from config file

    :param path: config filename directly provided (overwrites 'from_env_var' if both given)
    :param from_env_var: name of environment variable storing config filename
    :param config_type: 'yaml' (the only one supported now)
    :return: None
    """
    if (not path) and (not from_env_var):
        raise AssertionError("Provide either 'path' or 'from_env_var' parameter (none given)")
    if (not path):
        if from_env_var not in os.environ:
            raise KeyError("Environment variable '{}' is not set".format(from_env_var))
        path = os.environ[from_env_var]
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
