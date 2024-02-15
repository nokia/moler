# -*- coding: utf-8 -*-
"""
Compress logs after time rotation.
"""

__author__ = 'Marcin Usielski'
__copyright__ = 'Copyright (C) 2022, Nokia'
__email__ = 'marcin.usielski@nokia.com'

import subprocess
import os
from logging.handlers import RotatingFileHandler


class CompressedRotatingFileHandler(RotatingFileHandler):
    # pylint: disable=keyword-arg-before-vararg
    def __init__(self, compress_command='zip -9mq {compressed} {log_input}', compressed_file_extension='.zip',
                 *args, **kwargs):
        self.compress_command = compress_command
        self.compressed_file_extension = compressed_file_extension
        super(CompressedRotatingFileHandler, self).__init__(*args, **kwargs)

    def rotate(self, source, dest):
        super(CompressedRotatingFileHandler, self).rotate(source, dest)
        self._compress_file(filename=dest)

    def close(self):
        super(CompressedRotatingFileHandler, self).close()
        self._compress_file(filename=self.baseFilename)

    def _compress_file(self, filename):
        if os.path.exists(filename):
            # pylint: disable-next=consider-using-f-string
            full_pack_command = self.compress_command.format(compressed=f"{filename}{self.compressed_file_extension}",
                                                             log_input=filename)
            subprocess.Popen(full_pack_command.split())  # Potential issue if pack command takes more time than next
            #                                              log rotation.

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            # noinspection PyUnresolvedReferences
            self.stream.close()
            self.stream = None
        if int(self.backupCount) > 0:
            for i in range(int(self.backupCount) - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{int(i)}{self.compressed_file_extension}")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}{self.compressed_file_extension}")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(f"{self.baseFilename}.1")
            compressed_dfn = dfn + self.compressed_file_extension
            if os.path.exists(compressed_dfn):
                os.remove(compressed_dfn)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()
