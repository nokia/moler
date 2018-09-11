# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Configure logging for Moler's needs
"""
import copy

__author__ = 'Grzegorz Latuszek, Marcin Usielski, Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com, marcin.usielski@nokia.com, michal.ernst@nokia.com'

import logging
import os

logging_path = os.getcwd()  # Logging path that is used as a prefix for log file paths
active_loggers = []  # TODO: use set()      # Active loggers created by Moler
date_format = "%d %H:%M:%S"

# new logging levels
TRACE = 1  # highest possible debug level, may produce tons of logs, should be used for lib dev & troubleshooting
RAW_DATA = 4  # should be used for logging data of external sources, like connection's data send/received
# (above ERROR = 40, below CRITICAL = 50)
TEST_CASE = 45

debug_level = None  # means: inactive
trace_level = None  # means: inactive


def set_logging_path(path):
    global logging_path
    logging_path = path


def set_date_format(format):
    global date_format
    date_format = format


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
        # debug_level = allowed['TRACE']
        pass


def configure_trace_level():
    """
    Configure debug_level based on environment variable MOLER_DEBUG_LEVEL

    We use additional env variable besides MOLER_CONFIG to allow for quick/temporary change
    since debug level is intended also for troubleshooting
    """
    global trace_level
    trace_level = TRACE


def want_debug_details():
    """Check if we want to have debug details inside logs"""
    return debug_level is not None


def want_trace_details():
    """Check if we want to have trace details inside logs"""
    return trace_level is not None


def debug_level_or_info_level():
    """
    If debugging is active we want to have details inside logs
    otherwise we want to keep them small
    """
    if want_debug_details():
        level = debug_level
    else:
        level = logging.INFO
    return level


def setup_new_file_handler(logger_name, log_level, log_filename, formatter, filter=None):
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
    if filter:
        cfh.addFilter(filter)
    logger.addHandler(cfh)
    return cfh


def _add_new_file_handler(logger_name,
                          log_file, formatter, log_level=TRACE, filter=None):
    """
    Add file writer into Logger

    :param logger_name: Logger name
    :param log_file: Path to logfile. Final logfile location is logging_path + log_file
    :param log_level: only log records with equal and greater level will be accepted for storage in log
    :param formatter: formatter for file logger
    :return: None
    """
    logfile_full_path = os.path.join(logging_path, log_file)
    _prepare_logs_folder(logfile_full_path)
    setup_new_file_handler(logger_name=logger_name,
                           log_level=log_level,
                           log_filename=logfile_full_path,
                           formatter=formatter,
                           filter=filter)


def create_logger(name,
                  log_file=None, log_level=TRACE,
                  log_format="%(asctime)s %(levelname)-10s: |%(message)s",
                  datefmt=None):
    """
    Creates Logger with (optional) file writer

    :param name: Logger name
    :param log_file: Path to logfile. Final logfile location is logging_path + log_file
    :param log_level: only log records with equal and greater level will be accepted for storage in log
    :param log_format: layout of log file, default is "%(asctime)s %(levelname)-10s: |%(message)s"
    :param datefmt: format the creation time of the log record
    :return: None
    """
    logger = logging.getLogger(name)
    if name not in active_loggers:
        logger.setLevel(log_level)
        if log_file:  # if present means: "please add this file as logs storage for my logger"
            _add_new_file_handler(logger_name=name,
                                  log_file=log_file,
                                  log_level=log_level,
                                  formatter=logging.Formatter(fmt=log_format,
                                                              datefmt=datefmt))
        active_loggers.append(name)
    return logger


def configure_moler_main_logger():
    """Configure main logger of Moler"""
    # warning or above go to logfile
    logger = create_logger(name='moler', log_level=TRACE, datefmt=date_format)
    logger.propagate = True

    main_log_format = "%(asctime)s.%(msecs)03d %(levelname)-10s %(message)s"
    _add_new_file_handler(logger_name='moler',
                          log_file='moler.log',
                          log_level=logging.INFO,  # only hi-level info from library
                          formatter=MolerMainMultilineWithDirectionFormatter(fmt=main_log_format,
                                                                             datefmt=date_format))

    if want_trace_details():
        trace_log_format = "%(asctime)s.%(msecs)03d %(levelname)-10s %(name)-30s %(transfer_direction)s|%(message)s"
        _add_new_file_handler(logger_name='moler',
                              log_file='moler.debug.log',
                              log_level=trace_level,
                              # entries from different components go to single file, so we need to
                              # differentiate them by logger name: "%(name)s"
                              # do we need "%(threadName)-30s" ???
                              formatter=MultilineWithDirectionFormatter(fmt=trace_log_format,
                                                                        datefmt=date_format))
    elif want_debug_details():
        debug_log_format = "%(asctime)s.%(msecs)03d %(levelname)-10s %(name)-30s %(transfer_direction)s|%(message)s"
        _add_new_file_handler(logger_name='moler',
                              log_file='moler.debug.log',
                              log_level=debug_level,
                              # entries from different components go to single file, so we need to
                              # differentiate them by logger name: "%(name)s"
                              # do we need "%(threadName)-30s" ???
                              formatter=MultilineWithDirectionFormatter(fmt=debug_log_format,
                                                                        datefmt=date_format))

    logger.info("More logs in: {}".format(logging_path))


def configure_runner_logger(runner_name):
    """Configure logger with file storing runner's log"""
    create_logger(name='moler.runner.{}'.format(runner_name),
                  log_file='moler.runner.{}.log'.format(runner_name),
                  log_level=debug_level_or_info_level(),
                  log_format="%(asctime)s.%(msecs)03d %(levelname)-10s |%(message)s",
                  datefmt=date_format
                  # log_format="%(asctime)s %(levelname)-10s %(subarea)-30s: |%(message)s"
                  )


def configure_device_logger(connection_name, propagate=False):
    """Configure logger with file storing connection's log"""
    logger_name = 'moler.{}'.format(connection_name)
    logger = create_logger(name=logger_name, log_level=TRACE)
    logger.propagate = propagate
    conn_formatter = MultilineWithDirectionFormatter(fmt="%(asctime)s.%(msecs)03d %(transfer_direction)s|%(message)s",
                                                     datefmt=date_format)
    _add_new_file_handler(logger_name=logger_name,
                          log_file='{}.log'.format(logger_name),
                          log_level=logging.INFO,
                          formatter=conn_formatter)
    if want_debug_details():
        _add_new_file_handler(logger_name=logger_name,
                              log_file='{}.raw.log'.format(logger_name),
                              log_level=RAW_DATA,
                              formatter=conn_formatter,
                              filter=SpecificLevelFilter(RAW_DATA))

    if want_trace_details():
        _add_new_file_handler(logger_name=logger_name,
                              log_file='{}.trace.log'.format(logger_name),
                              log_level=TRACE,
                              formatter=conn_formatter,
                              filter=SpecificLevelFilter(TRACE))
    return logger


def _prepare_logs_folder(logfile_full_path):
    """
    Checks that log folder exist and creates it if needed

    :param logfile_full_path: path to log folder
    :return: Nome
    """
    logdir = os.path.dirname(logfile_full_path)
    if not os.path.exists(logdir):
        os.makedirs(logdir)


class TracedIn(object):
    """
    Decorator to allow for tracing method/function invocation
    It sends function name and parameters into logger given as decorator parameter
    sends with loglevel=TRACE
    Decorator is active only when environment variable MOLER_DEBUG_LEVEL = TRACE
    ex.:
    @TracedIn('moler')
    def method(self, arg1, arg2):
    """

    def __init__(self, logger_name):  # decorator parameter
        self.logger = logging.getLogger(logger_name)
        self.trace_active = (debug_level == TRACE)

    def __call__(self, decorated_method):
        if not self.trace_active:
            return decorated_method

        method_name = decorated_method.__name__

        def _traced_method(*args,
                           **kwargs):  # parameters of decorated_method
            args_list = [str(arg) for arg in args]
            kwargs_list = ['{}={}'.format(arg, kwargs[arg]) for arg in
                           kwargs]
            param_str = ', '.join(args_list + kwargs_list)
            ret = decorated_method(*args, **kwargs)
            self.logger.log(TRACE, '{}({}) returned: {}'.format(method_name,
                                                                param_str,
                                                                ret))
            return ret

        return _traced_method


class MultilineWithDirectionFormatter(logging.Formatter):
    """
    We want logs to have non-overlapping areas
    timestamp area TTTTTTTTTTT
    transfer direction area >  (shows send '>' or receive '<')
    log message area MMMMMMMMMM

    It should look like:
    TTTTTTTTTTTTTTT D MMMMMMMMMMMMMMM

    01 00:36:09.581 >|cat my_file.txt
    01 00:36:09.585 <|This is
                     |multiline
                     |content

    This formatter allows to use %(transfer_direction)s inside format
    """

    def __init__(self, fmt=None, datefmt=None):
        if fmt is None:
            fmt = "%(asctime)s.%(msecs)03d %(transfer_direction)s|%(message)s"
        else:  # message should be last part of format
            assert fmt.endswith("|%(message)s")
        super(MultilineWithDirectionFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record):
        if not hasattr(record, 'transfer_direction'):
            record.transfer_direction = ' '
        if not hasattr(record, 'log_name'):
            record.log_name = ""

        msg_lines = record.getMessage().splitlines(True)
        base_output = super(MultilineWithDirectionFormatter, self).format(record)
        out_lines = base_output.splitlines(True)
        output = out_lines[0]

        if len(msg_lines) >= 1:
            empty_prefix = self._calculate_empty_prefix(msg_lines[0], out_lines[0])
            for line in out_lines[1:]:
                output += "{}|{}".format(empty_prefix, line)

        # TODO: line completion for connection decoded data comming in chunks
        output = MolerMainMultilineWithDirectionFormatter._remove_duplicate_log_name(record, output)
        return output

    def _calculate_empty_prefix(self, message_first_line, output_first_line):
        prefix_len = output_first_line.rindex("|{}".format(message_first_line))
        empty_prefix = " " * prefix_len
        return empty_prefix

    @staticmethod
    def _remove_duplicate_log_name(record, output):
        if record.log_name and "|{}".format(record.log_name) in output:
            output = output.replace("|{:<20}".format(record.log_name), "")
        return output


class MolerMainMultilineWithDirectionFormatter(MultilineWithDirectionFormatter):
    def __init__(self, fmt, datefmt=None):
        if fmt is None:
            fmt = "%(asctime)s.%(msecs)03d %(transfer_direction)s|%(message)s"
        else:  # message should be last part of format
            assert fmt.endswith("%(message)s")
        super(MultilineWithDirectionFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record):
        if not hasattr(record, 'log_name'):
            record.log_name = record.name

        record.msg = "{:<20}|{}".format(record.log_name, record.msg)

        return super(MolerMainMultilineWithDirectionFormatter, self).format(record)

    def _calculate_empty_prefix(self, message_first_line, output_first_line):
        prefix_len = output_first_line.index("|")
        empty_prefix = " " * prefix_len
        return empty_prefix


class SpecificLevelFilter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno == self.__level


# actions during import:
logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(RAW_DATA, "RAW_DATA")
logging.addLevelName(TEST_CASE, "TEST_CASE")
configure_debug_level()
