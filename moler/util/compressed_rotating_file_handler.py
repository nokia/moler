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
    def __init__(self, compress_command='zip -9mq {packed} {log_input}', compress_suffix='.zip', *args, **kwargs):
        self.compress_command = compress_command
        self.compress_suffix = compress_suffix
        super(CompressedRotatingFileHandler, self).__init__(*args, **kwargs)

    def rotate(self, source, dest):
        super(CompressedRotatingFileHandler, self).rotate(source, dest)
        full_pack_command = self.compress_command.format(packed=dest + self.compress_suffix, log_input=dest)
        subprocess.Popen(full_pack_command.split())

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d%s" % (self.baseFilename, i, self.compress_suffix))
                dfn = self.rotation_filename("%s.%d%s" % (self.baseFilename,
                                                          i + 1, self.compress_suffix))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.baseFilename + ".1")
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()
