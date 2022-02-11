# -*- coding: utf-8 -*-
"""
Compress logs after time rotation.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2022, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import subprocess
import os
from logging.handlers import TimedRotatingFileHandler


class CompressedTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, compress_command='zip -9mq {compressed} {log_input}', compress_suffix='.zip', *args, **kwargs):
        self.compress_command = compress_command
        self.compress_suffix = compress_suffix
        super(CompressedTimedRotatingFileHandler, self).__init__(*args, **kwargs)

    def rotate(self, source, dest):
        super(CompressedTimedRotatingFileHandler, self).rotate(source, dest)
        self._compress_file(filename=dest)

    def close(self):
        super(CompressedTimedRotatingFileHandler, self).close()
        self._compress_file(filename=self.baseFilename)

    def _compress_file(self, filename):
        if os.path.exists(filename):
            full_pack_command = self.compress_command.format(compressed=filename + self.compress_suffix,
                                                             log_input=filename)
            subprocess.Popen(full_pack_command.split())
