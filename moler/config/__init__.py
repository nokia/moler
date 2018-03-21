# -*- coding: utf-8 -*-
"""
Moler related configuration
"""
import yaml
from contextlib import contextmanager

from . import connections as conn_cfg

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


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
    for name, connection_specification in config.items():
        io_type = connection_specification.pop("io_type")
        conn_cfg.define_connection(name, io_type, **connection_specification)


def clear():
    """Cleanup Moler's configuration"""
    conn_cfg.clear()
