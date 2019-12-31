# -*- coding: utf-8 -*-
"""
Tests for utilities related to logging.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import mock


def test_extracting_caller_code_location():
    from moler.util.loghelper import find_caller

    frames_info = []

    def my_outer_fun():
        frames_info.append(find_caller())  # who called me and from which line
        my_iner_fun()

    def my_iner_fun():
        frames_info.append(find_caller())  # who called me and from which line
        frames_info.append(find_caller(levels_to_go_up=1))  # who called him and from which line

    my_outer_fun()

    called_from_filename = frames_info[0][0]
    assert called_from_filename.endswith("test_util_loghelper.py")
    assert called_from_filename == frames_info[1][0]
    assert called_from_filename == frames_info[2][0]

    (_, called_from_lineno, called_from_fun_name) = frames_info[0]
    assert called_from_fun_name == "test_extracting_caller_code_location"
    assert called_from_lineno == 26

    (_, called_from_lineno, called_from_fun_name) = frames_info[1]
    assert called_from_fun_name == "my_outer_fun"
    assert called_from_lineno == 20

    (_, called_from_lineno, called_from_fun_name) = frames_info[2]
    assert called_from_fun_name == "test_extracting_caller_code_location"
    assert called_from_lineno == 26


def test_logging_caller_code_location():
    import logging
    from moler.util.loghelper import warning_into_logger

    logger = logging.getLogger('moler')

    def my_deprecated_fun():
        warn_about_calling("you should not call deprecated functions")

    def warn_about_calling(msg):
        warning_into_logger(logger, msg, levels_to_go_up=2)

    logged_record = [None]

    def log_record_receiver(logger, log_record):
        logged_record[0] = log_record

    with mock.patch.object(logger.__class__, "handle", new=log_record_receiver):
        my_deprecated_fun()

    assert logged_record[0] is not None
    log_record = logged_record[0]
    assert log_record.levelname == "WARNING"
    assert log_record.msg == "you should not call deprecated functions"
    assert log_record.filename.endswith("test_util_loghelper.py")
    assert log_record.funcName == "test_logging_caller_code_location"
    assert log_record.lineno == 64


def test_correct_loglevel_of_helper_logging_functions():
    import logging
    from moler.util.loghelper import error_into_logger
    from moler.util.loghelper import warning_into_logger
    from moler.util.loghelper import info_into_logger
    from moler.util.loghelper import debug_into_logger

    logger = logging.getLogger('moler')

    def fun_using_helper_logging():
        error_into_logger(logger, msg="hi")
        warning_into_logger(logger, msg="hi")
        info_into_logger(logger, msg="hi")
        debug_into_logger(logger, msg="hi")

    logged_record = []

    def log_record_receiver(logger, log_record):
        logged_record.append(log_record)

    with mock.patch.object(logger.__class__, "handle", new=log_record_receiver):
        fun_using_helper_logging()

    assert logged_record[0].levelname == "ERROR"
    assert logged_record[1].levelname == "WARNING"
    assert logged_record[2].levelname == "INFO"
    assert logged_record[3].levelname == "DEBUG"


def test_passing_extra_param_into_helper_logging_functions():
    import logging
    from moler.util.loghelper import log_into_logger

    logger = logging.getLogger('moler')

    def fun_using_helper_logging():
        log_into_logger(logger, level=logging.WARNING, msg="hi", extra={'transfer_direction': '<'})

    logged_record = []

    def log_record_receiver(logger, log_record):
        logged_record.append(log_record)

    with mock.patch.object(logger.__class__, "handle", new=log_record_receiver):
        fun_using_helper_logging()

    assert logged_record[0].transfer_direction == "<"
