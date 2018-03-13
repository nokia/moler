# -*- coding: utf-8 -*-
import logging
import time
import pytest

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'


def test_multiline_formatter_expects_format_ending_with_message():
    from moler.config.loggers import MultilineWithDirectionFormatter

    formatter = MultilineWithDirectionFormatter(fmt="%(asctime)s.%(msecs)03d |%(message)s")
    assert isinstance(formatter, logging.Formatter)

    with pytest.raises(AssertionError):
        MultilineWithDirectionFormatter(fmt="%(asctime)s.%(msecs)03d", datefmt="%d %H:%M:%S")


def test_multiline_formatter_puts_message_lines_into_data_area():
    """
    We want logs to look like:

    01 19:36:09.823  |This is
                     |multiline
                     |content
    """
    from moler.config.loggers import MultilineWithDirectionFormatter

    formatter = MultilineWithDirectionFormatter(fmt="%(asctime)s.%(msecs)03d |%(message)s", datefmt="%d %H:%M:%S")
    tm_struct = time.strptime("2000-01-01 19:36:09", "%Y-%m-%d %H:%M:%S")
    epoch_tm = time.mktime(tm_struct)
    logging_time = epoch_tm
    log_rec = logging.makeLogRecord({'msg': "This is\nmultiline\ncontent",
                                     'created': logging_time, 'msecs': 823})
    output = formatter.format(log_rec)

    assert output == "01 19:36:09.823 |This is\n" \
                     "                |multiline\n" \
                     "                |content"


def test_multiline_formatter_puts_direction_info_into_direction_area():
    """
    We want logs to look like:

    01 19:36:09.823 >|sent
    01 19:36:09.823 <|received
    01 19:36:09.823  |just log
    """
    from moler.config.loggers import MultilineWithDirectionFormatter

    formatter = MultilineWithDirectionFormatter(fmt="%(asctime)s.%(msecs)03d %(transfer_direction)s|%(message)s",
                                                datefmt="%d %H:%M:%S")
    tm_struct = time.strptime("2000-01-01 19:36:09", "%Y-%m-%d %H:%M:%S")
    epoch_tm = time.mktime(tm_struct)
    logging_time = epoch_tm

    log_rec = logging.makeLogRecord({'msg': "sent",
                                     'created': logging_time, 'msecs': 823,
                                     'transfer_direction': '>'})
    output = formatter.format(log_rec)
    assert output == "01 19:36:09.823 >|sent"

    log_rec = logging.makeLogRecord({'msg': "received",
                                     'created': logging_time, 'msecs': 823,
                                     'transfer_direction': '<'})
    output = formatter.format(log_rec)
    assert output == "01 19:36:09.823 <|received"

    log_rec = logging.makeLogRecord({'msg': "just log",
                                     'created': logging_time, 'msecs': 823})
    output = formatter.format(log_rec)
    assert output == "01 19:36:09.823  |just log"
