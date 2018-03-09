# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Configure logging for Moler's needs
"""
import os
import logging

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

logging_path = os.getcwd()  # Logging path that is used as a prefix for log file paths
active_loggers = []  # TODO: use set()      # Active loggers created by Moler

TRACE = 1     # highest possible debug level, may produce tons of logs, should be used for lib dev & troubleshooting
RAW_DATA = 4  # should be used for logging data of external sources, like connection's data send/received


debug_level = None  # means: inactive


def configure_debug_level():
    """
    Configure debug_level based on environment variable MOLER_DEBUG_LEVEL

    We use additional env variable besides MOLER_CONFIG to allow for quick/temporary change
    since debug level is intended also for troubleshooting
    """
    global debug_level
    level_name = os.getenv('MOLER_DEBUG_LEVEL', 'not_found').upper()
    allowed = {'TRACE': TRACE, 'RAW_DATA': RAW_DATA, 'DEBUG': logging.DEBUG}
    if level_name in allowed:
        debug_level = allowed[level_name]
    else:
        # TODO: take it from MOLER_CONFIG
        pass


def debug_level_or_info_level():
    """
    If debugging is active we want to have details inside logs
    otherwise we want to keep them small
    """
    if debug_level is not None:
        level = debug_level
    else:
        level = logging.INFO
    return level


def setup_new_file_handler(logger_name, log_level, log_filename, formatter):
    """
    Sets up new file handler for given logger

    :param logger_name: name of logger to which filelogger is added
    :param log_level: logging level
    :param log_filename: path to log file
    :param formatter: formatter for file logger
    :return:  logging.FileHandler object
    """
    logger = logging.getLogger(logger_name)
    cfh = logging.FileHandler(log_filename, 'w')
    cfh.setLevel(log_level)
    cfh.setFormatter(formatter)
    logger.addHandler(cfh)
    return cfh


def create_logger(name,
                  log_file=None, log_level=TRACE,
                  log_format="%(asctime)s %(levelname)-10s: |%(message)s"):
    """
    Creates Logger with (optional) file writer

    :param name: Logger name
    :param log_file: Path to logfile. Final logfile location is logging_path + log_file
    :param log_level: only log records with equal and greater level will be accepted for storage in log
    :param log_format: layout of log file, default is "%(asctime)s %(levelname)-10s: |%(message)s"
    :return: None
    """
    logger = logging.getLogger(name)
    if name not in active_loggers:
        logger.setLevel(log_level)
        if log_file:  # if present means: "please add this file as logs storage for my logger"
            logfile_full_path = os.path.join(logging_path, log_file)
            _prepare_logs_folder(logfile_full_path)
            setup_new_file_handler(logger_name=name,
                                   log_level=log_level,
                                   log_filename=logfile_full_path,
                                   formatter=logging.Formatter(log_format))
            active_loggers.append(name)
    return logger


def configure_runner_logger(runner_name):
    """Configure logger with file storing runner's log"""
    create_logger(name='moler.runner.{}'.format(runner_name),
                  log_file='moler.runner.{}.log'.format(runner_name),
                  log_level=debug_level_or_info_level(),
                  # log_format="%(asctime)s %(levelname)-10s %(threadName)-30s: |%(message)s"
                  log_format="%(asctime)s %(levelname)-10s %(name)-30s |%(message)s"
                  # log_format="%(asctime)s %(levelname)-10s %(subarea)-30s: |%(message)s"
                  )


def _prepare_logs_folder(logfile_full_path):
    """
    Checks that log folder exist and creates it if needed

    :param logfile_full_path: path to log folder
    :return: Nome
    """
    logdir = os.path.dirname(logfile_full_path)
    if not os.path.exists(logdir):
        os.makedirs(logdir)


# actions during import:
logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(RAW_DATA, "RAW_DATA")
configure_debug_level()
