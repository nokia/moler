# -*- coding: utf-8 -*-

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import time
import pytest


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


def test_RawFileHandler_appends_binary_message_into_logfile():
    import os
    import os.path
    from moler.config.loggers import RAW_DATA, RawFileHandler
    cwd = os.getcwd()
    logfile_full_path = os.path.join(cwd, "tmp.raw.log")
    raw_handler = RawFileHandler(filename=logfile_full_path, mode='wb')
    binary_msg = b"1 0.000000000    127.0.0.1 \xe2\x86\x92 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64"
    record = logging.LogRecord(name=None, level=RAW_DATA, pathname="", lineno=0,
                               msg=binary_msg,  # only this is used
                               args=(), exc_info=None)
    raw_handler.emit(record=record)
    raw_handler.close()
    with open(logfile_full_path, mode='rb') as logfh:
        content = logfh.read()
        assert content == binary_msg
    os.remove(logfile_full_path)


def test_RawDataFormatter_uses_encoder_of_log_record():
    from moler.config.loggers import RAW_DATA, RawDataFormatter
    raw_formatter = RawDataFormatter()
    binary_msg = b"1 0.000000000    127.0.0.1 \xe2\x86\x92 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64"
    decoded_msg = binary_msg.decode(encoding='utf-8')
    record = logging.LogRecord(name=None, level=RAW_DATA, pathname="", lineno=0,
                               msg=decoded_msg,         # this is used - not bytes data
                               args=(), exc_info=None)
    record.encoder = lambda data: data.encode('utf-8')  # must be combined with encoder
    # Raw logger (and its formatter) may get already decoded data
    # but it must produce bytes
    # so, it converts back decoded data into bytes using encoder
    # that must come in record together with data
    raw_msg = raw_formatter.format(record=record)
    assert raw_msg == binary_msg


def test_RawTraceFormatter_produces_yaml_record():
    from moler.config.loggers import RAW_DATA, RawTraceFormatter, date_format
    import mock
    trace_formatter = RawTraceFormatter()
    binary_msg = b"127.0.0.1 \xe2\x86\x92 ttl"
    now = time.time()
    with mock.patch("time.time", return_value=now):
        record = logging.Logger(name='moler').makeRecord(name=None, level=RAW_DATA, fn="", lno=0,
                                                         msg=binary_msg,
                                                         args=(), exc_info=None,
                                                         extra={'transfer_direction': '<'})
    trace_msg = trace_formatter.format(record=record)
    timestamp = logging.Formatter(fmt="%(asctime)s.%(msecs)03d", datefmt=date_format).format(record)
    assert trace_msg.startswith("- {}".format(record.created))
    trace_msg_rest = trace_msg[2 + len(str(record.created)):]  # 2 for '- '
    assert trace_msg_rest == ": {time: '%s', direction: <, bytesize: 17, offset: 0}\n" % timestamp
    trace_msg = trace_formatter.format(record=record)
    trace_msg_rest = trace_msg[2 + len(str(record.created)):]  # 2 for '- '
    assert trace_msg_rest == ": {time: '%s', direction: <, bytesize: 17, offset: 17}\n" % timestamp  # offset shifts by bytesize of previous record


def test_RawFileHandler_logs_only_records_with_level_equal_to_RAW_DATA():
    import os
    import os.path
    from moler.config.loggers import RAW_DATA, TRACE, RawFileHandler
    cwd = os.getcwd()
    logfile_full_path = os.path.join(cwd, "tmp.raw.log")
    raw_handler = RawFileHandler(filename=logfile_full_path, mode='wb')
    binary_msg1 = b"1 0.000000000    127.0.0.1 \xe2\x86\x92 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64"
    binary_msg2 = b"2 0.000000000    127.0.0.1 \xe2\x86\x92 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64"
    binary_msg3 = b"3 0.000000000    127.0.0.1 \xe2\x86\x92 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64"
    record1 = logging.LogRecord(name=None, pathname="", lineno=0,
                                msg=binary_msg1, level=TRACE,          # too low level
                                args=(), exc_info=None)
    record2 = logging.LogRecord(name=None, pathname="", lineno=0,
                                msg=binary_msg2, level=RAW_DATA,       # expected level
                                args=(), exc_info=None)
    record3 = logging.LogRecord(name=None, pathname="", lineno=0,
                                msg=binary_msg3, level=logging.DEBUG,  # too high level
                                args=(), exc_info=None)
    raw_handler.handle(record=record1)
    raw_handler.handle(record=record2)
    raw_handler.handle(record=record3)
    raw_handler.close()
    with open(logfile_full_path, mode='rb') as logfh:
        content = logfh.read()
        assert content == binary_msg2
    os.remove(logfile_full_path)


def test_raw_logger_can_log_binary_raw_data(monkeypatch):
    import os
    import moler.config.loggers as m_logger

    binary_msg = b"1 0.000000000    127.0.0.1 \xe2\x86\x92 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64"
    buffer = bytearray()
    buffer.extend(binary_msg)
    size2read = len(buffer)
    data = buffer[:size2read]  # should work well with bytes  and  bytearray
    monkeypatch.setattr(m_logger, 'raw_logs_active', True)
    device_data_logger = m_logger.configure_device_logger(connection_name='Linux_xyz_2', propagate=False)
    device_data_logger.log(level=m_logger.RAW_DATA, msg=data, extra={'transfer_direction': '<'})
    created_files = []
    raw_logfile_full_path = ''
    for hndl in device_data_logger.handlers:
        hndl.close()
        created_files.append(hndl.baseFilename)
        if isinstance(hndl, m_logger.RawFileHandler) and not isinstance(hndl.formatter, m_logger.RawTraceFormatter):
            raw_logfile_full_path = hndl.baseFilename
    with open(raw_logfile_full_path, mode='rb') as logfh:
        content = logfh.read()
        assert content == binary_msg
    for filename in created_files:
        os.remove(filename)


def test_raw_logger_can_log_decoded_binary_raw_data(monkeypatch):
    import os
    import moler.config.loggers as m_logger

    binary_msg = b"1 0.000000000    127.0.0.1 \xe2\x86\x92 127.0.0.1    ICMP 98 Echo (ping) request  id=0x693b, seq=48/12288, ttl=64"
    decoded_msg = binary_msg.decode(encoding='utf-8')
    monkeypatch.setattr(m_logger, 'raw_logs_active', True)
    device_data_logger = m_logger.configure_device_logger(connection_name='Solaris_old_1', propagate=False)
    device_data_logger.log(level=m_logger.RAW_DATA, msg=decoded_msg,
                           extra={'transfer_direction': '<',
                                  # decoded_msg must be combined with encoder
                                  'encoder': lambda data: data.encode('utf-8')})
    created_files = []
    raw_logfile_full_path = ''
    for hndl in device_data_logger.handlers:
        hndl.close()
        created_files.append(hndl.baseFilename)
        if isinstance(hndl, m_logger.RawFileHandler) and not isinstance(hndl.formatter, m_logger.RawTraceFormatter):
            raw_logfile_full_path = hndl.baseFilename
    with open(raw_logfile_full_path, mode='rb') as logfh:
        content = logfh.read()
        assert content == binary_msg
    for filename in created_files:
        os.remove(filename)


def test_raw_logger_can_create_both_raw_logs(monkeypatch):
    import os
    import moler.config.loggers as m_logger

    binary_msg = b"127.0.0.1 \xe2\x86\x92 ttl"

    monkeypatch.setattr(m_logger, 'raw_logs_active', True)
    monkeypatch.setattr(m_logger, 'date_format', "%H:%M:%S")
    device_data_logger = m_logger.configure_device_logger(connection_name='Suse_10', propagate=False)
    device_data_logger.log(level=m_logger.RAW_DATA, msg=binary_msg, extra={'transfer_direction': '<'})
    created_files = []
    raw_logfile_full_path = ''
    raw_trace_logfile_full_path = ''
    for hndl in device_data_logger.handlers:
        hndl.close()
        created_files.append(hndl.baseFilename)
        if isinstance(hndl, m_logger.RawFileHandler):
            if isinstance(hndl.formatter, m_logger.RawTraceFormatter):
                raw_trace_logfile_full_path = hndl.baseFilename
            else:
                raw_logfile_full_path = hndl.baseFilename
    with open(raw_logfile_full_path, mode='rb') as logfh:
        content = logfh.read()
        assert content == binary_msg
    with open(raw_trace_logfile_full_path, mode='r') as logfh:
        content = logfh.read()
        assert 'direction: <, bytesize: 17, offset: 0}\n' in content
    for filename in created_files:
        os.remove(filename)


def test_raw_trace_log_can_be_yaml_loaded(monkeypatch):
    import os
    import yaml
    import moler.config.loggers as m_logger

    binary_msg = b"127.0.0.1 \xe2\x86\x92 ttl"

    monkeypatch.setattr(m_logger, 'raw_logs_active', True)
    monkeypatch.setattr(m_logger, 'date_format', "%H:%M:%S")
    device_data_logger = m_logger.configure_device_logger(connection_name='RHat_10', propagate=False)
    device_data_logger.log(level=m_logger.RAW_DATA, msg=binary_msg, extra={'transfer_direction': '<'})
    device_data_logger.log(level=m_logger.RAW_DATA, msg=binary_msg, extra={'transfer_direction': '<'})
    device_data_logger.log(level=m_logger.RAW_DATA, msg=binary_msg, extra={'transfer_direction': '<'})
    created_files = []
    raw_trace_logfile_full_path = ''
    for hndl in device_data_logger.handlers:
        hndl.close()
        created_files.append(hndl.baseFilename)
        if isinstance(hndl, m_logger.RawFileHandler) and isinstance(hndl.formatter, m_logger.RawTraceFormatter):
            raw_trace_logfile_full_path = hndl.baseFilename
    with open(raw_trace_logfile_full_path, mode='r') as logfh:

        raw_log_records = yaml.load(logfh)

        assert len(raw_log_records) == 3
        rec1 = raw_log_records[0]
        rec2 = raw_log_records[1]
        rec3 = raw_log_records[2]
        time1 = list(rec1.keys())[0]  # always one key - timestamp
        time2 = list(rec2.keys())[0]
        time3 = list(rec3.keys())[0]
        assert rec1[time1]['direction'] == '<'
        assert rec1[time1]['bytesize'] == 17
        assert rec1[time1]['offset'] == 0
        assert rec2[time2]['direction'] == '<'
        assert rec2[time2]['bytesize'] == 17
        assert rec2[time2]['offset'] == 17
        assert rec3[time3]['direction'] == '<'
        assert rec3[time3]['bytesize'] == 17
        assert rec3[time3]['offset'] == 34
    for filename in created_files:
        os.remove(filename)
